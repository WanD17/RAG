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
| 2026-04-30 16:19 | **conv-manager-v1** | 9 | 19 | 88.9% | 0.500 | 50.0% | 100.0% | 0.0% | 100.0% | 161,686 | 200,525 | baseline |

---

## Future runs

### Planned

- [ ] `no-rewriter` — baseline trước khi có query rewriter (ellip_hit@5 dự kiến thấp)
- [ ] `with-rewriter` — sau khi implement query rewriter → so sánh delta trên coref_kw + ellip_hit@5

### Interpretation guide

Sau `no-rewriter`:
- `coref_kw` thấp nhưng `t1_hit@5` cao → query rewriter sẽ giúp được
- `ellip_hit@5` rất thấp → elliptical rewrite quan trọng
- `no_leak = 100%` → conversation history không gây nhiễu (expected vì history chỉ inject vào LLM, không vào retrieval)

Sau `with-rewriter`:
- `coref_kw` và `ellip_hit@5` phải tăng rõ rệt
- `t1_hit@5` không đổi (turn 1 không qua rewriter)
- `no_leak` không đổi hoặc tốt hơn
