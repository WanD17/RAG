"""Run automated evaluation against the RAG backend.

Loads golden_set.json, queries the backend for each sample, computes 8
deterministic metrics + latency statistics, and writes a timestamped
JSON report to evaluation/results/.

Usage:
    python evaluation/run_eval.py                          # full run
    python evaluation/run_eval.py --limit 10               # quick smoke test
    python evaluation/run_eval.py --resume                 # resume interrupted run
    python evaluation/run_eval.py --llm-judge              # + faithfulness (llama3.2:3b judge)
    python evaluation/run_eval.py --llm-judge --judge-model mistral:7b  # override judge
"""
import argparse
import json
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
CONFIG_FILE = HERE / ".config.json"
GOLDEN_FILE = HERE / "golden_set.json"
RESULTS_DIR = HERE / "results"
CHECKPOINT = HERE / ".last_run_checkpoint.json"

REFUSAL_PATTERNS = [
    r"\bnot\s+found\b", r"\bcannot\s+answer\b", r"\bno\s+(relevant\s+)?information\b",
    r"\bdo\s+not\s+have\b", r"\bunable\s+to\b", r"\binsufficient\b",
    r"\bkhông\s+tìm\s+thấy\b", r"\bkhông\s+có\s+thông\s+tin\b",
    r"\bno\s+relevant\s+documents?\b", r"\bnot\s+available\b",
    r"\bcannot\s+find\b", r"\bi\s+cannot\s+find\b",
    r"\bnot\s+provided\b", r"\bnot\s+mentioned\b", r"\bno\s+specific\s+mention\b",
    r"\bdoes\s+not\s+(contain|mention|provide|include)\b",
    r"\bdo\s+not\s+contain\b", r"\bcontext\s+does\s+not\b",
    r"\bnot\s+present\s+in\b", r"\bno\s+information\s+(about|on|regarding)\b",
]
REFUSAL_RE = re.compile("|".join(REFUSAL_PATTERNS), re.IGNORECASE)
CITATION_RE = re.compile(r"\[?\b(?:Source|Article|Chapter)\s+\w+", re.IGNORECASE)


def load_config():
    if not CONFIG_FILE.exists():
        sys.exit(f"[error] {CONFIG_FILE} not found. Run upload_docs.py first.")
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def load_embedder():
    """Lazy import to avoid startup delay when not needed."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def cosine(a, b) -> float:
    import numpy as np
    a, b = np.asarray(a), np.asarray(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def refresh_token(cfg: dict) -> None:
    """Re-login and update cfg['token'] + .config.json in-place."""
    email = cfg.get("email", "")
    password = cfg.get("password", "")
    if not email or not password:
        raise RuntimeError("No credentials in .config.json — re-run upload_docs.py")
    r = httpx.post(f"{cfg['backend']}/auth/login",
                   json={"email": email, "password": password}, timeout=30)
    r.raise_for_status()
    cfg["token"] = r.json()["access_token"]
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    [auth] token refreshed")


def query_backend(cfg, question: str, top_k: int = 5, timeout: int = 300) -> dict:
    t0 = time.perf_counter()
    r = httpx.post(
        f"{cfg['backend']}/rag/query",
        json={"query": question, "top_k": top_k},
        headers={"Authorization": f"Bearer {cfg['token']}"},
        timeout=timeout,
    )
    if r.status_code == 401:
        refresh_token(cfg)
        r = httpx.post(
            f"{cfg['backend']}/rag/query",
            json={"query": question, "top_k": top_k},
            headers={"Authorization": f"Bearer {cfg['token']}"},
            timeout=timeout,
        )
    latency_ms = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    data = r.json()
    data["_latency_ms"] = latency_ms
    return data


def compute_metrics(sample, result, embedder, ref_embeddings_cache):
    """Return dict of metric values for this sample."""
    m = {"category": sample["category"]}
    answer = (result.get("answer") or "").strip()
    sources = result.get("sources") or []
    retrieved_docs = [s.get("filename") for s in sources if s.get("filename")]
    is_refusal = bool(REFUSAL_RE.search(answer)) if answer else True

    m["latency_ms"] = round(result["_latency_ms"], 1)
    m["answer_len"] = len(answer)

    # --- Retrieval (in-scope only) ---
    if sample["category"] == "in_scope" and sample.get("source_doc"):
        gt = sample["source_doc"]
        m["doc_hit@5"] = int(gt in retrieved_docs)
        if m["doc_hit@5"]:
            rank = retrieved_docs.index(gt) + 1
            m["mrr"] = round(1.0 / rank, 3)
            m["doc_rank"] = rank
        else:
            m["mrr"] = 0.0
            m["doc_rank"] = None

    # --- Answer similarity (in-scope only, skip refusals) ---
    if sample["category"] == "in_scope" and answer and not is_refusal:
        if sample["id"] not in ref_embeddings_cache:
            ref_embeddings_cache[sample["id"]] = embedder.encode(sample["reference_answer"])
        ans_emb = embedder.encode(answer)
        m["ans_cosine"] = round(cosine(ans_emb, ref_embeddings_cache[sample["id"]]), 3)

    # --- Keyword recall (in-scope) ---
    if sample["category"] == "in_scope":
        kws = sample.get("required_keywords") or []
        if kws:
            low = answer.lower()
            hits = sum(1 for k in kws if k.lower() in low)
            m["keyword_recall"] = round(hits / len(kws), 3)

    # --- Citation presence (in-scope) ---
    if sample["category"] == "in_scope":
        m["has_citation"] = bool(CITATION_RE.search(answer)) or len(sources) > 0

    # --- Refusal (context-aware) ---
    if sample.get("must_refuse"):
        m["refused_correctly"] = is_refusal
    elif sample["category"] == "in_scope":
        m["false_refusal"] = is_refusal and not answer_is_substantive(answer)

    return m


def answer_is_substantive(answer: str) -> bool:
    """Heuristic: answer that refuses but also provides substantive info is OK."""
    return len(answer) > 100 and not answer.lower().startswith(("i cannot", "not found", "unable"))


def pct(vals):
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals) * 100, 1) if vals else None


def mean(vals):
    vals = [v for v in vals if v is not None]
    return round(statistics.mean(vals), 3) if vals else None


def percentile(vals, p):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    idx = min(len(vals) - 1, int(len(vals) * p / 100))
    return round(vals[idx], 1)


def aggregate(per_sample):
    in_scope = [r for r in per_sample if r["metrics"]["category"] == "in_scope"]
    oos = [r for r in per_sample if r["metrics"]["category"] == "out_of_scope"]

    def get(rows, key):
        return [r["metrics"].get(key) for r in rows]

    lat_all = get(per_sample, "latency_ms")

    answer_quality = {
        "cosine_sim_mean": mean(get(in_scope, "ans_cosine")),
        "keyword_recall_mean": mean(get(in_scope, "keyword_recall")),
        "citation_coverage_pct": pct(get(in_scope, "has_citation")),
    }
    faith_vals = [v for v in get(in_scope, "faithfulness") if v is not None]
    if faith_vals:
        answer_quality["faithfulness_mean"] = mean(faith_vals)
        answer_quality["faithfulness_n"] = len(faith_vals)

    prec_vals = [v for v in get(in_scope, "context_precision") if v is not None]
    if prec_vals:
        answer_quality["context_precision_mean"] = mean(prec_vals)
        answer_quality["context_precision_n"] = len(prec_vals)

    summary = {
        "num_samples": len(per_sample),
        "num_in_scope": len(in_scope),
        "num_out_of_scope": len(oos),
        "retrieval": {
            "doc_hit@5_pct": pct(get(in_scope, "doc_hit@5")),
            "mrr_mean": mean(get(in_scope, "mrr")),
        },
        "answer_quality": answer_quality,
        "behavior": {
            "oos_refusal_accuracy_pct": pct(get(oos, "refused_correctly")),
            "false_refusal_in_scope_pct": pct(get(in_scope, "false_refusal")),
        },
        "latency_ms": {
            "p50": percentile(lat_all, 50),
            "p95": percentile(lat_all, 95),
            "p99": percentile(lat_all, 99),
            "mean": mean(lat_all),
            "max": max(lat_all) if lat_all else None,
        },
    }
    return summary


def print_summary(summary, run_meta=None):
    line = "=" * 60
    print(line)
    print(f" EVAL SUMMARY — {summary['num_samples']} samples "
          f"({summary['num_in_scope']} in-scope, {summary['num_out_of_scope']} OOS)")
    if run_meta:
        print(f" Timestamp: {run_meta.get('timestamp')}")
    print(line)
    print("\n[Retrieval]")
    print(f"  doc_hit@5           : {summary['retrieval']['doc_hit@5_pct']}%")
    print(f"  MRR                 : {summary['retrieval']['mrr_mean']}")
    print("\n[Answer quality]")
    print(f"  cosine similarity   : {summary['answer_quality']['cosine_sim_mean']}")
    print(f"  keyword recall      : {summary['answer_quality']['keyword_recall_mean']}")
    print(f"  citation coverage   : {summary['answer_quality']['citation_coverage_pct']}%")
    if "faithfulness_mean" in summary["answer_quality"]:
        n = summary["answer_quality"]["faithfulness_n"]
        print(f"  faithfulness (LLM)  : {summary['answer_quality']['faithfulness_mean']} (n={n})")
    if "context_precision_mean" in summary["answer_quality"]:
        n = summary["answer_quality"]["context_precision_n"]
        print(f"  ctx precision (LLM) : {summary['answer_quality']['context_precision_mean']} (n={n})")
    print("\n[Behavior]")
    print(f"  OOS refusal accuracy: {summary['behavior']['oos_refusal_accuracy_pct']}%")
    print(f"  false refusal (IS)  : {summary['behavior']['false_refusal_in_scope_pct']}%")
    print("\n[Latency]")
    lat = summary["latency_ms"]
    print(f"  p50 / p95 / p99     : {lat['p50']} / {lat['p95']} / {lat['p99']} ms")
    print(f"  mean / max          : {lat['mean']} / {lat['max']} ms")
    print(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Only run first N samples")
    ap.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--tag", type=str, default="", help="Tag in filename (e.g. 'after-reranker')")
    ap.add_argument("--llm-judge", action="store_true", help="Enable faithfulness scoring via LLM judge")
    ap.add_argument("--judge-model", type=str, default="llama3.2:3b",
                    help="Ollama model for judge (default: llama3.2:3b — different family from qwen backend)")
    ap.add_argument("--judge-url", type=str, default="http://localhost:11434", help="Ollama URL for judge")
    args = ap.parse_args()

    if args.llm_judge:
        from llm_judge import judge_faithfulness as _judge_faith
        from llm_judge import judge_context_precision as _judge_prec
        judge_model = args.judge_model
        print(f"[llm-judge] enabled — model={judge_model}, url={args.judge_url}")
    else:
        _judge_faith = None
        _judge_prec = None
        judge_model = None

    cfg = load_config()
    golden = json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))
    samples = golden["samples"]
    if args.limit:
        samples = samples[:args.limit]

    embedder = load_embedder()
    per_sample = []
    ref_emb_cache = {}
    done_ids = set()

    if args.resume and CHECKPOINT.exists():
        cp = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        per_sample = cp["per_sample"]
        done_ids = {r["id"] for r in per_sample}
        print(f"[resume] continuing from {len(done_ids)} completed samples")

    RESULTS_DIR.mkdir(exist_ok=True)
    start = time.time()

    for i, sample in enumerate(samples, 1):
        if sample["id"] in done_ids:
            continue
        try:
            print(f"[{i}/{len(samples)}] {sample['id']}: {sample['question'][:70]}...",
                  flush=True)
            result = query_backend(cfg, sample["question"], top_k=args.top_k)
            metrics = compute_metrics(sample, result, embedder, ref_emb_cache)

            if _judge_faith and sample["category"] == "in_scope" and not metrics.get("false_refusal"):
                answer = (result.get("answer") or "").strip()
                sources = result.get("sources") or []
                faith = _judge_faith(answer, sources, args.judge_url, judge_model)
                if faith is not None:
                    metrics["faithfulness"] = faith
                prec = _judge_prec(sample["question"], sources, args.judge_url, judge_model)
                if prec is not None:
                    metrics["context_precision"] = prec
                if faith is not None or prec is not None:
                    f_str = f"{faith:.3f}" if faith is not None else "N/A"
                    p_str = f"{prec:.3f}" if prec is not None else "N/A"
                    print(f"    faithfulness={f_str}  ctx_precision={p_str}")

            per_sample.append({
                "id": sample["id"],
                "question": sample["question"],
                "answer": (result.get("answer") or "")[:800],
                "retrieved_docs": [s.get("filename") for s in result.get("sources", [])],
                "metrics": metrics,
            })
            # save checkpoint every sample (cheap insurance)
            CHECKPOINT.write_text(json.dumps({"per_sample": per_sample}, ensure_ascii=False), encoding="utf-8")
        except KeyboardInterrupt:
            print("\n[interrupt] saved checkpoint. Run with --resume to continue.")
            return
        except Exception as e:
            print(f"  [error] {e}")
            per_sample.append({
                "id": sample["id"], "question": sample["question"],
                "error": str(e),
                "metrics": {"category": sample["category"], "latency_ms": 0},
            })

    summary = aggregate(per_sample)
    run_meta = {
        "timestamp": datetime.now().isoformat(),
        "duration_sec": round(time.time() - start, 1),
        "backend": cfg["backend"],
        "top_k": args.top_k,
        "num_samples_requested": len(samples),
        "tag": args.tag,
    }
    report = {"run": run_meta, "summary": summary, "per_sample": per_sample}

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag_suffix = f"-{args.tag}" if args.tag else ""
    out = RESULTS_DIR / f"{stamp}{tag_suffix}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if CHECKPOINT.exists():
        CHECKPOINT.unlink()

    print_summary(summary, run_meta)
    print(f"\n[saved] {out}")


if __name__ == "__main__":
    main()
