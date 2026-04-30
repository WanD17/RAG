"""Multi-turn conversation evaluation against the RAG backend.

Loads multiturn_golden_set.json, runs each conversation turn-by-turn while
threading conversation_id, computes per-turn and aggregate metrics, and writes
a timestamped JSON report to evaluation/results/.

Metrics:
  - Per-turn: doc_hit@5, MRR, cosine_sim, keyword_recall, citation, is_refusal
  - Conversation-level: conversation_id consistency across turns
  - Aggregated by turn position (turn 1 vs turn 2 vs turn 3)
  - Aggregated by test_type (coreference, elliptical, topic_shift, continuation, oos_followup)

Usage:
    python evaluation/run_multiturn_eval.py
    python evaluation/run_multiturn_eval.py --tag "after-conv-manager"
    python evaluation/run_multiturn_eval.py --limit 3     # first N conversations
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
GOLDEN_FILE = HERE / "multiturn_golden_set.json"
RESULTS_DIR = HERE / "results"

REFUSAL_RE = re.compile(
    r"\bnot\s+found\b|\bcannot\s+answer\b|\bno\s+(relevant\s+)?information\b"
    r"|\bdo\s+not\s+have\b|\bunable\s+to\b|\binsufficient\b"
    r"|\bkhông\s+tìm\s+thấy\b|\bkhông\s+có\s+thông\s+tin\b"
    r"|\bno\s+relevant\s+documents?\b|\bnot\s+available\b"
    r"|\bcannot\s+find\b|\bi\s+cannot\s+find\b",
    re.IGNORECASE,
)
CITATION_RE = re.compile(r"\[?\b(?:Source|Article|Chapter)\s+\w+", re.IGNORECASE)


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        sys.exit(f"[error] {CONFIG_FILE} not found. Run upload_docs.py first.")
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def load_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def cosine(a, b) -> float:
    import numpy as np
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def query_backend(cfg: dict, question: str, conversation_id: str | None, top_k: int = 5) -> dict:
    payload: dict = {"query": question, "top_k": top_k}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    t0 = time.perf_counter()
    r = httpx.post(
        f"{cfg['backend']}/rag/query",
        json=payload,
        headers={"Authorization": f"Bearer {cfg['token']}"},
        timeout=300,
    )
    latency_ms = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    data = r.json()
    data["_latency_ms"] = latency_ms
    return data


def score_turn(turn_spec: dict, result: dict, embedder, emb_cache: dict) -> dict:
    """Compute metrics for one turn."""
    answer = (result.get("answer") or "").strip()
    sources = result.get("sources") or []
    retrieved_docs = [s.get("filename") for s in sources if s.get("filename")]
    is_refusal = bool(REFUSAL_RE.search(answer)) if answer else True

    m: dict = {
        "test_type": turn_spec["test_type"],
        "turn": turn_spec["turn"],
        "latency_ms": round(result["_latency_ms"], 1),
        "answer_len": len(answer),
        "is_refusal": is_refusal,
    }

    if turn_spec.get("must_refuse"):
        m["refused_correctly"] = is_refusal
        return m

    # doc_hit@5 + MRR
    src = turn_spec.get("source_doc")
    if src and retrieved_docs:
        m["doc_hit@5"] = int(src in retrieved_docs)
        if m["doc_hit@5"]:
            rank = retrieved_docs.index(src) + 1
            m["mrr"] = round(1.0 / rank, 3)
            m["doc_rank"] = rank
        else:
            m["mrr"] = 0.0
            m["doc_rank"] = None
    else:
        m["doc_hit@5"] = None
        m["mrr"] = None

    # cosine similarity vs reference
    ref = turn_spec.get("reference_answer")
    if ref and answer and not is_refusal:
        cache_key = f"{turn_spec['turn']}_{ref[:40]}"
        if cache_key not in emb_cache:
            emb_cache[cache_key] = embedder.encode(ref)
        ans_emb = embedder.encode(answer)
        m["cosine_sim"] = round(cosine(ans_emb, emb_cache[cache_key]), 3)

    # keyword recall
    kws = turn_spec.get("required_keywords") or []
    if kws:
        low = answer.lower()
        hits = sum(1 for k in kws if k.lower() in low)
        m["keyword_recall"] = round(hits / len(kws), 3)
        m["keywords_hit"] = [k for k in kws if k.lower() in low]
        m["keywords_miss"] = [k for k in kws if k.lower() not in low]

    # forbidden keywords (topic shift check)
    forbidden = turn_spec.get("forbidden_keywords") or []
    if forbidden:
        low = answer.lower()
        leaks = [k for k in forbidden if k.lower() in low]
        m["topic_leak"] = len(leaks) > 0
        m["leaked_keywords"] = leaks

    # citation
    m["has_citation"] = bool(CITATION_RE.search(answer)) or len(sources) > 0

    return m


def run_conversation(conv: dict, cfg: dict, embedder, emb_cache: dict) -> dict:
    turns_out = []
    conversation_id: str | None = None
    conv_ids_seen: list[str] = []
    first_conv_id: str | None = None

    for turn_spec in conv["turns"]:
        t = turn_spec["turn"]
        q = turn_spec["question"]
        print(f"    turn {t}: {q[:70]}...", flush=True)

        try:
            result = query_backend(cfg, q, conversation_id)
        except Exception as e:
            print(f"      [error] {e}")
            turns_out.append({
                "turn": t,
                "test_type": turn_spec["test_type"],
                "error": str(e),
                "metrics": {"test_type": turn_spec["test_type"], "turn": t, "latency_ms": 0},
            })
            continue

        # thread conversation_id
        returned_id = result.get("conversation_id")
        if returned_id:
            conv_ids_seen.append(returned_id)
            if conversation_id is None:
                conversation_id = returned_id
                first_conv_id = returned_id

        metrics = score_turn(turn_spec, result, embedder, emb_cache)
        turns_out.append({
            "turn": t,
            "test_type": turn_spec["test_type"],
            "question": q,
            "answer": (result.get("answer") or "")[:600],
            "retrieved_docs": [s.get("filename") for s in result.get("sources", [])],
            "conversation_id": returned_id,
            "metrics": metrics,
        })

    # conversation-level: check conv_id consistency
    consistent = len(set(conv_ids_seen)) == 1 if conv_ids_seen else None

    return {
        "conv_id": conv["id"],
        "description": conv["description"],
        "first_conversation_id": first_conv_id,
        "conv_id_consistent": consistent,
        "turns": turns_out,
    }


def _vals(results: list[dict], turn_filter=None, test_type_filter=None, key=None):
    out = []
    for conv in results:
        for t in conv["turns"]:
            if turn_filter and t["turn"] != turn_filter:
                continue
            if test_type_filter and t.get("test_type") != test_type_filter:
                continue
            v = t["metrics"].get(key)
            if v is not None:
                out.append(v)
    return out


def pct(vals: list) -> float | None:
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals) * 100, 1) if vals else None


def mean(vals: list) -> float | None:
    vals = [v for v in vals if v is not None]
    return round(statistics.mean(vals), 3) if vals else None


def percentile(vals: list, p: int) -> float | None:
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    idx = min(len(vals) - 1, int(len(vals) * p / 100))
    return round(vals[idx], 1)


def aggregate(results: list[dict]) -> dict:
    all_turns = [t for c in results for t in c["turns"]]
    all_lat = [t["metrics"].get("latency_ms") for t in all_turns]

    # by turn position
    by_turn = {}
    for pos in [1, 2, 3]:
        hit = _vals(results, turn_filter=pos, key="doc_hit@5")
        cos = _vals(results, turn_filter=pos, key="cosine_sim")
        kw = _vals(results, turn_filter=pos, key="keyword_recall")
        if hit or cos or kw:
            by_turn[str(pos)] = {
                "n": len([t for c in results for t in c["turns"] if t["turn"] == pos]),
                "doc_hit@5_pct": pct(hit),
                "cosine_sim_mean": mean(cos),
                "keyword_recall_mean": mean(kw),
            }

    # by test_type
    by_type: dict = {}
    for tt in ["standard", "coreference", "elliptical", "continuation", "topic_shift", "oos_followup"]:
        turns_tt = [t for c in results for t in c["turns"] if t.get("test_type") == tt]
        if not turns_tt:
            continue
        entry: dict = {"n": len(turns_tt)}
        if tt in ("standard", "coreference", "elliptical", "continuation"):
            entry["doc_hit@5_pct"] = pct([t["metrics"].get("doc_hit@5") for t in turns_tt])
            entry["cosine_sim_mean"] = mean([t["metrics"].get("cosine_sim") for t in turns_tt])
            entry["keyword_recall_mean"] = mean([t["metrics"].get("keyword_recall") for t in turns_tt])
        if tt == "topic_shift":
            leaks = [t["metrics"].get("topic_leak") for t in turns_tt if t["metrics"].get("topic_leak") is not None]
            entry["no_topic_leak_pct"] = pct([not v for v in leaks]) if leaks else None
        if tt == "oos_followup":
            entry["refusal_accuracy_pct"] = pct([t["metrics"].get("refused_correctly") for t in turns_tt])
        by_type[tt] = entry

    # conversation-level
    conv_consistent = [c.get("conv_id_consistent") for c in results if c.get("conv_id_consistent") is not None]

    return {
        "num_conversations": len(results),
        "num_turns_total": len(all_turns),
        "conversation_id_consistency_pct": pct(conv_consistent),
        "by_turn_position": by_turn,
        "by_test_type": by_type,
        "latency_ms": {
            "p50": percentile(all_lat, 50),
            "p95": percentile(all_lat, 95),
            "mean": mean(all_lat),
        },
    }


def print_summary(summary: dict, run_meta: dict | None = None) -> None:
    line = "=" * 60
    print(line)
    print(f" MULTI-TURN EVAL — {summary['num_conversations']} conversations, "
          f"{summary['num_turns_total']} turns")
    if run_meta:
        print(f" Timestamp: {run_meta.get('timestamp')}")
    print(line)

    print("\n[By turn position]")
    for pos, s in summary["by_turn_position"].items():
        print(f"  Turn {pos} (n={s['n']}): hit@5={s['doc_hit@5_pct']}%  "
              f"cos={s['cosine_sim_mean']}  kw={s['keyword_recall_mean']}")

    print("\n[By test type]")
    for tt, s in summary["by_test_type"].items():
        parts = [f"n={s['n']}"]
        if "doc_hit@5_pct" in s:
            parts.append(f"hit@5={s['doc_hit@5_pct']}%")
        if "cosine_sim_mean" in s:
            parts.append(f"cos={s['cosine_sim_mean']}")
        if "keyword_recall_mean" in s:
            parts.append(f"kw={s['keyword_recall_mean']}")
        if "no_topic_leak_pct" in s:
            parts.append(f"no_leak={s['no_topic_leak_pct']}%")
        if "refusal_accuracy_pct" in s:
            parts.append(f"refusal={s['refusal_accuracy_pct']}%")
        print(f"  {tt:<15}: {', '.join(parts)}")

    print(f"\n[Conversation ID consistency]  {summary['conversation_id_consistency_pct']}%")
    lat = summary["latency_ms"]
    print(f"[Latency] p50={lat['p50']} ms  p95={lat['p95']} ms  mean={lat['mean']} ms")
    print(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Only run first N conversations")
    ap.add_argument("--tag", type=str, default="", help="Tag suffix in result filename")
    ap.add_argument("--top-k", type=int, default=5)
    args = ap.parse_args()

    cfg = load_config()
    golden = json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))
    conversations = golden["conversations"]
    if args.limit:
        conversations = conversations[:args.limit]

    print(f"Loading embedder...", flush=True)
    embedder = load_embedder()
    emb_cache: dict = {}
    RESULTS_DIR.mkdir(exist_ok=True)

    results = []
    start = time.time()

    for conv in conversations:
        print(f"\n[{conv['id']}] {conv['description']}", flush=True)
        try:
            out = run_conversation(conv, cfg, embedder, emb_cache)
        except KeyboardInterrupt:
            print("\n[interrupt] saving partial results...")
            break
        except Exception as e:
            print(f"  [error] {e}")
            out = {"conv_id": conv["id"], "error": str(e), "turns": []}
        results.append(out)

    summary = aggregate(results)
    run_meta = {
        "timestamp": datetime.now().isoformat(),
        "duration_sec": round(time.time() - start, 1),
        "backend": cfg["backend"],
        "top_k": args.top_k,
        "tag": args.tag,
        "golden_file": GOLDEN_FILE.name,
    }
    report = {"run": run_meta, "summary": summary, "per_conversation": results}

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag_suffix = f"-{args.tag}" if args.tag else ""
    out_path = RESULTS_DIR / f"{stamp}-multiturn{tag_suffix}.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print_summary(summary, run_meta)
    print(f"\n[saved] {out_path}")


if __name__ == "__main__":
    main()
