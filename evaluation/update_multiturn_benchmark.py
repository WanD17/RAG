"""Append the latest (or specified) multiturn eval result as a new row in multiturn_benchmark.md.

Usage:
    python evaluation/update_multiturn_benchmark.py
    python evaluation/update_multiturn_benchmark.py results/foo-multiturn.json
    python evaluation/update_multiturn_benchmark.py --note "no query rewriter baseline"
    python evaluation/update_multiturn_benchmark.py results/foo.json --note "with rewriter"
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
BENCHMARK_FILE = Path(__file__).parent / "multiturn_benchmark.md"

TABLE_HEADER = "| Date | Tag | C | T | t1_hit@5 | coref_kw | ellip_hit@5 | no_leak | oos_ref | conv_ok | p50 ms | p95 ms | Notes |"
ROW_SEPARATOR = "|------|-----|:-:|:-:|:--------:|:--------:|:-----------:|:-------:|:-------:|:-------:|:------:|:------:|-------|"


def pick_result_file(arg: str | None) -> Path:
    if arg:
        p = Path(arg)
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists():
            sys.exit(f"File not found: {p}")
        return p
    # prefer multiturn result files
    files = sorted(RESULTS_DIR.glob("*multiturn*.json"), key=lambda f: f.stat().st_mtime)
    if not files:
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
    n_conv = _get(s, "num_conversations", default=0)
    n_turns = _get(s, "num_turns_total", default=0)

    # turn 1 (standard) hit@5
    t1_hit = _get(s, "by_turn_position", "1", "doc_hit@5_pct")

    # coreference keyword_recall
    coref_kw = _get(s, "by_test_type", "coreference", "keyword_recall_mean")

    # elliptical doc_hit@5
    ellip_hit = _get(s, "by_test_type", "elliptical", "doc_hit@5_pct")

    # topic_shift no_leak
    no_leak = _get(s, "by_test_type", "topic_shift", "no_topic_leak_pct")

    # oos_followup refusal
    oos_ref = _get(s, "by_test_type", "oos_followup", "refusal_accuracy_pct")

    # conversation_id consistency
    conv_ok = _get(s, "conversation_id_consistency_pct")

    # latency
    p50 = _get(s, "latency_ms", "p50")
    p95 = _get(s, "latency_ms", "p95")

    def pct(v): return f"{v:.1f}%" if v is not None else "—"
    def num(v): return f"{v:.3f}" if v is not None else "—"
    def ms(v):  return f"{int(v):,}" if v is not None else "—"

    return (
        f"| {ts} | **{tag}** | {n_conv} | {n_turns} | "
        f"{pct(t1_hit)} | {num(coref_kw)} | {pct(ellip_hit)} | "
        f"{pct(no_leak)} | {pct(oos_ref)} | {pct(conv_ok)} | "
        f"{ms(p50)} | {ms(p95)} | {note} |"
    )


def insert_row(content: str, new_row: str) -> str:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("|---") and i > 0 and TABLE_HEADER.split("|")[2].strip() in lines[i - 1]:
            lines.insert(i + 1, new_row)
            return "\n".join(lines) + "\n"

    sys.exit("Could not locate table insertion point in multiturn_benchmark.md")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_file", nargs="?", default=None)
    parser.add_argument("--note", default="", help="Short note for the row")
    args = parser.parse_args()

    result_path = pick_result_file(args.result_file)
    data = json.loads(result_path.read_text(encoding="utf-8"))

    row = build_row(data, args.note)
    content = BENCHMARK_FILE.read_text(encoding="utf-8")

    if result_path.name in content:
        print(f"⚠  {result_path.name} already in multiturn_benchmark.md — skipping.")
        print(f"   Row: {row}")
        return

    updated = insert_row(content, row)
    BENCHMARK_FILE.write_text(updated, encoding="utf-8")
    print(f"✓  Appended to multiturn_benchmark.md from {result_path.name}")
    print(f"   {row}")


if __name__ == "__main__":
    main()
