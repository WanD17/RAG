"""Compare two evaluation result files side-by-side.

Usage:
    python evaluation/compare.py results/<baseline>.json results/<current>.json
"""
import json
import sys
from pathlib import Path


# Metrics we care about and whether higher is better
METRICS = [
    # (path, label, higher_is_better, format)
    (["retrieval", "doc_hit@5_pct"], "doc_hit@5 (%)", True, "pct"),
    (["retrieval", "mrr_mean"], "MRR", True, "num"),
    (["answer_quality", "cosine_sim_mean"], "cosine similarity", True, "num"),
    (["answer_quality", "keyword_recall_mean"], "keyword recall", True, "num"),
    (["answer_quality", "citation_coverage_pct"], "citation coverage (%)", True, "pct"),
    (["behavior", "oos_refusal_accuracy_pct"], "OOS refusal (%)", True, "pct"),
    (["behavior", "false_refusal_in_scope_pct"], "false refusal (%)", False, "pct"),
    (["latency_ms", "p50"], "latency p50 (ms)", False, "ms"),
    (["latency_ms", "p95"], "latency p95 (ms)", False, "ms"),
    (["latency_ms", "mean"], "latency mean (ms)", False, "ms"),
]


def dig(d, path):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


def fmt(v, fmt_type):
    if v is None:
        return "  N/A"
    if fmt_type == "pct":
        return f"{v:>6.1f}%"
    if fmt_type == "ms":
        return f"{v:>7.0f}"
    return f"{v:>6.3f}"


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python compare.py <baseline.json> <current.json>")
    base_path, curr_path = Path(sys.argv[1]), Path(sys.argv[2])
    base = json.loads(base_path.read_text(encoding="utf-8"))
    curr = json.loads(curr_path.read_text(encoding="utf-8"))
    bs, cs = base["summary"], curr["summary"]

    print("=" * 80)
    print(f" BASELINE : {base_path.name}  ({base['run']['timestamp'][:19]})")
    print(f" CURRENT  : {curr_path.name}  ({curr['run']['timestamp'][:19]})")
    print("=" * 80)
    print(f"{'Metric':<28}{'Baseline':>12}{'Current':>12}{'Delta':>12}    Status")
    print("-" * 80)

    regressions = 0
    for path, label, higher_better, fmt_type in METRICS:
        b, c = dig(bs, path), dig(cs, path)
        if b is None or c is None:
            delta_str, status = "  N/A", ""
        else:
            delta = c - b
            improved = (delta > 0) == higher_better
            if fmt_type == "pct":
                delta_str = f"{delta:+6.1f}"
            elif fmt_type == "ms":
                delta_str = f"{delta:+7.0f}"
            else:
                delta_str = f"{delta:+6.3f}"
            if abs(delta) < (0.01 if fmt_type == "num" else 1):
                status = "→ no change"
            elif improved:
                status = "✓ better"
            else:
                status = "✗ WORSE"
                # Flag significant regressions
                if fmt_type == "pct" and abs(delta) >= 3:
                    status += " !!"; regressions += 1
                elif fmt_type == "num" and abs(delta) >= 0.03:
                    status += " !!"; regressions += 1
                elif fmt_type == "ms" and abs(delta) >= b * 0.15:
                    status += " !!"; regressions += 1

        print(f"{label:<28}{fmt(b, fmt_type):>12}{fmt(c, fmt_type):>12}"
              f"{delta_str:>12}    {status}")

    print("-" * 80)
    if regressions:
        print(f"⚠  {regressions} significant regression(s) detected (marked with !!)")
    else:
        print("✓  No significant regressions.")
    print("=" * 80)


if __name__ == "__main__":
    main()
