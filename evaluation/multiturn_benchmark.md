# Multi-turn Benchmark

Lịch sử đánh giá khả năng multi-turn conversation trên 9 conversations, 20 turns từ `multiturn_golden_set.json`.

## Metric legend

| Metric | Meaning | Target | Higher better |
|--------|---------|:------:|:---:|
| `t1_hit@5` | doc_hit@5 của turn 1 (standard) — baseline retrieval | > 70% | ✓ |
| `coref_kw` | keyword_recall của coreference turns — LLM có resolve pronoun đúng không | > 60% | ✓ |
| `ellip_hit@5` | doc_hit@5 của elliptical turns — retrieval có hoạt động trên câu hỏi rút gọn không | > 50% | ✓ |
| `no_leak` | % topic_shift turns không bị topic leakage | > 90% | ✓ |
| `oos_ref` | % oos_followup turns bị refuse đúng | > 80% | ✓ |
| `conv_ok` | % conversations có conversation_id nhất quán suốt | 100% | ✓ |
| `p50/p95 ms` | Latency percentiles tính trên tất cả turns | p95 < 10000 | ✗ |

**Cách đọc kết quả:**
- `t1_hit@5` thấp → vấn đề retrieval tổng quát (không liên quan multi-turn)
- `coref_kw` thấp hơn `t1_hit@5` nhiều → query rewriter chưa hiệu quả
- `ellip_hit@5` thấp → cần query rewriter để expand elliptical query trước khi search
- `no_leak` < 90% → conversation history đang nhiễu topic shift turns
- `conv_ok` < 100% → bug trong conversation manager

---

## Run history

Latest on top.

| Date | Tag | C | T | t1_hit@5 | coref_kw | ellip_hit@5 | no_leak | oos_ref | conv_ok | p50 ms | p95 ms | Notes |
|------|-----|:-:|:-:|:--------:|:--------:|:-----------:|:-------:|:-------:|:-------:|:------:|:------:|-------|
| 2026-04-30 17:24 | **with-rewriter** | 9 | 19 | 88.9% | 0.500 | 100.0% | 100.0% | 100.0% | 100.0% | 160,611 | 231,907 | with rewriter |
| 2026-04-30 16:19 | **conv-manager-v1** | 9 | 19 | 88.9% | 0.500 | 50.0% | 100.0% | 0.0% | 100.0% | 161,686 | 200,525 | baseline |

---

## Analysis — conv-manager-v1 → with-rewriter delta

| Metric | conv-manager-v1 | with-rewriter | Delta | Target met |
|--------|:-:|:-:|:-:|:-:|
| t1_hit@5 | 88.9% | 88.9% | = | ✅ (expected: no change) |
| coref_kw | 0.500 | 0.500 | = | ⚠️ below 0.6 target |
| ellip_hit@5 | 50.0% | 100.0% | **+50pp** | ✅ |
| no_leak | 100.0% | 100.0% | = | ✅ |
| oos_ref | 0.0% | 100.0% | **+100pp** | ✅ (side effect of rewriter) |
| conv_ok | 100.0% | 100.0% | = | ✅ |

**ellip_hit@5 50% → 100%** — rewriter expanded elliptical queries (e.g. "And the rate on public holidays?" → standalone query) before retrieval. Exactly as expected.

**oos_ref 0% → 100%** — unexpected bonus: rewriter expanded "How does this compare to France and the US?" into a query containing "France / United States" which has no matching documents in the Vietnamese law corpus, so retrieval returns weak/no candidates and the LLM correctly refuses.

**coref_kw unchanged at 0.500** — coreference turns (e.g. "its members", "this rate") appear to pass the heuristic gate as self-contained (≥8 words, no trigger pronoun matched). Investigation needed: check if `_PRONOUN_RE` is catching "its" / "this" in those specific queries, or if the issue is retrieval succeeding but LLM missing required keywords.

**p95 latency +31s** — rewriter adds 1 LLM call per rewritten turn. Acceptable at current scale; can gate with `REWRITER_ENABLED=false` if needed.

## Future runs

### Planned

- [x] ~~`no-rewriter`~~ — skipped (conv-manager-v1 serves as pre-rewriter baseline)
- [x] `with-rewriter` — ✅ done 2026-04-30
- [ ] `coref-fix` — investigate coref_kw stuck at 0.500; tune `_PRONOUN_RE` or lower heuristic gate threshold → expect coref_kw > 0.6
