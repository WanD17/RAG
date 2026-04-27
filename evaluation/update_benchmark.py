"""Append the latest (or specified) eval result as a new row in benchmark.md.

Usage:
    python evaluation/update_benchmark.py                          # auto-pick latest result
    python evaluation/update_benchmark.py results/foo.json        # specific file
    python evaluation/update_benchmark.py --note "some note"
    python evaluation/update_benchmark.py results/foo.json --note "some note"
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
BENCHMARK_FILE = Path(__file__).parent / "benchmark.md"

TABLE_HEADER = "| Date | Tag | N | doc_hit@5 | MRR | cos_sim | kw_rec | cite | OOS_ref | false_ref | p50 ms | p95 ms | Notes |"
ROW_SEPARATOR = "|------|-----|:-:|:---------:|:---:|:-------:|:------:|:----:|:-------:|:---------:|:------:|:------:|-------|"


def pick_result_file(arg: str | None) -> Path:
    if arg:
        p = Path(arg)
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists():
            sys.exit(f"File not found: {p}")
        return p
    files = sorted(RESULTS_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime)
    if not files:
        sys.exit(f"No result files found in {RESULTS_DIR}")
    return files[-1]


def _get(d: dict, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def build_row(data: dict, note: str) -> str:
    run = data.get("run", {})
    s = data.get("summary", {})

    ts = run.get("timestamp", "")[:16].replace("T", " ")
    tag = run.get("tag", "unknown")
    n = _get(s, "num_samples", default=0)

    hit5 = _get(s, "retrieval", "doc_hit@5_pct")
    mrr = _get(s, "retrieval", "mrr_mean")
    cos = _get(s, "answer_quality", "cosine_sim_mean")
    kw = _get(s, "answer_quality", "keyword_recall_mean")
    cite = _get(s, "answer_quality", "citation_coverage_pct")
    oos = _get(s, "behavior", "oos_refusal_accuracy_pct")
    false_r = _get(s, "behavior", "false_refusal_in_scope_pct")
    p50 = _get(s, "latency_ms", "p50")
    p95 = _get(s, "latency_ms", "p95")

    def pct(v): return f"{v:.1f}%" if v is not None else "—"
    def num(v): return f"{v:.3f}" if v is not None else "—"
    def ms(v):  return f"{int(v):,}" if v is not None else "—"

    return (
        f"| {ts} | **{tag}** | {n} | {pct(hit5)} | {num(mrr)} | {num(cos)} | "
        f"{num(kw)} | {pct(cite)} | {pct(oos)} | {pct(false_r)} | "
        f"{ms(p50)} | {ms(p95)} | {note} |"
    )


def insert_row(content: str, new_row: str) -> str:
    """Insert new_row right after the table header+separator lines."""
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("|---") and i > 0 and TABLE_HEADER.split("|")[2].strip() in lines[i - 1]:
            lines.insert(i + 1, new_row)
            return "\n".join(lines) + "\n"

    # Fallback: append after ## Run history
    for i, line in enumerate(lines):
        if line.strip() == "## Run history":
            insert_at = i + 1
            while insert_at < len(lines) and not lines[insert_at].strip().startswith("|"):
                insert_at += 1
            lines.insert(insert_at + 2, new_row)  # after header + separator
            return "\n".join(lines) + "\n"

    sys.exit("Could not locate table insertion point in benchmark.md")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_file", nargs="?", default=None, help="Path to result JSON")
    parser.add_argument("--note", default="", help="Short note for the row")
    args = parser.parse_args()

    result_path = pick_result_file(args.result_file)
    data = json.loads(result_path.read_text(encoding="utf-8"))

    row = build_row(data, args.note)
    content = BENCHMARK_FILE.read_text(encoding="utf-8")

    if result_path.name in content:
        print(f"⚠  {result_path.name} already appears in benchmark.md — skipping duplicate insert.")
        print(f"   Row that would have been added:\n   {row}")
        return

    updated = insert_row(content, row)
    BENCHMARK_FILE.write_text(updated, encoding="utf-8")
    print(f"✓  Appended to benchmark.md from {result_path.name}")
    print(f"   {row}")


if __name__ == "__main__":
    main()
