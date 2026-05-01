# RAG Benchmark

Lịch sử đánh giá hệ thống trên 60 golden samples (50 in-scope + 10 OOS/adversarial) từ 13 Vietnamese Law PDFs.

## Metric legend

| Metric | Meaning | Target | Higher better |
|--------|---------|:------:|:---:|
| `doc_hit@5` | % câu hỏi có GT doc trong top-5 retrieved | > 70% | ✓ |
| `MRR` | Mean Reciprocal Rank của GT doc | > 0.5 | ✓ |
| `cos_sim` | Cosine similarity answer vs reference (MiniLM) | > 0.6 | ✓ |
| `kw_recall` | % required keywords trong answer | > 0.5 | ✓ |
| `cite` | % answer có citation | > 80% | ✓ |
| `OOS_ref` | % OOS refused đúng | > 70% | ✓ |
| `false_ref` | % IS refused nhầm | < 10% | ✗ |
| `p50/p95 ms` | Latency percentiles | p95 < 10000 | ✗ |

---

## Run history

Latest on top.

| Date | Tag | N | doc_hit@5 | MRR | cos_sim | kw_rec | cite | OOS_ref | false_ref | p50 ms | p95 ms | Notes |
|------|-----|:-:|:---------:|:---:|:-------:|:------:|:----:|:-------:|:---------:|:------:|:------:|-------|
| 2026-04-30 19:39 | **RRF + score threshold + chunkerv2** | 60 | 100.0% | 0.948 | 0.801 | 0.860 | 100.0% | 100.0%✓ | 0.0% | 100,284 | 150,029 | RRF + score threshold + chunkerv2; OOS_ref corrected after regex fix |
| 2026-04-27 16:56 | **bm25+qdrant+propmt_eng+reranker** | 60 | 98.0% | 0.953 | 0.795 | 0.830 | 100.0% | 10.0% | 0.0% | 172,315 | 227,391 | bm25+qdrant+propmt_eng+reranker |
| 2026-04-23 16:26 | **baseline** | 60 | 100.0% | 0.948 | 0.763 | 0.830 | 100.0% | 30.0%⚠ | 0.0% | 146707 | 186728 | qwen3:8b CPU, pgvector cosine, no reranker |
| 2026-04-23 13:50 | smoke | 5 | 100.0% | 0.867 | 0.718 | 0.700 | 100.0% | — | 0.0% | 149641 | 161056 | Smoke test, 5 IS samples |

⚠ = metric bị ảnh hưởng bởi regex gap, xem phần diagnosis bên dưới.

---

## Baseline — 2026-04-23 16:26

### Configuration

| Field | Value |
|-------|-------|
| Backend | `http://localhost:8000` |
| LLM | `qwen3:8b` (Ollama, CPU) |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` (384 dim) |
| Vector DB | PostgreSQL 16 + pgvector, IVFFlat cosine (lists=100) |
| Retrieval | Pure vector, top_k=5 |
| Reranker | ❌ None |
| BM25 / Hybrid | ❌ None |
| System prompt | Default (1-line) |
| Duration | 2h 24m 10s (8650s) |
| Errors | 0 / 60 |

### Metrics

**Retrieval — 🌟 Excellent**
- `doc_hit@5`: **100.0%** (50/50 in-scope samples retrieved correct document)
- `MRR`: **0.948** (GT doc thường ở top-1; rank trung bình ~1.05)
- **Interpretation**: Pure pgvector cosine với MiniLM embed hoạt động rất tốt trên corpus luật này. 13 docs phân biệt chủ đề đủ rõ → embedding tách được domain một cách dễ dàng.

**Answer quality — 🟢 Good**
- `cosine similarity`: **0.763** (answer semantically rất sát reference)
- `keyword recall`: **0.830** (83% required keywords xuất hiện)
- `citation coverage`: **100.0%** (mọi answer đều có source cited)

**Behavior — 🟡 Needs investigation**
- `OOS refusal accuracy`: **30.0%** ⚠ — xem diagnosis
- `false refusal (in-scope)`: **0.0%** 🌟 (không bao giờ refuse nhầm câu hỏi có câu trả lời)

**Latency — 🔴 Critical (hardware bottleneck)**
- `p50 / p95 / p99`: **146,707 / 186,728 / 202,309 ms** (~2.5 / 3.1 / 3.4 phút)
- `mean / max`: **144,120 / 202,309 ms**
- `min`: 11,977 ms (probably cached embed or short answer)
- **Interpretation**: qwen3:8b trên CPU = bottleneck duy nhất. Toàn bộ 2h24m eval time là thời gian LLM generation.

### Diagnosis: OOS refusal 30% không phải bug thật

Inspect 5/7 OOS samples bị flag "not refused":

| ID | Question | Answer (trích) |
|----|----------|----------------|
| q_051 | Speed limit on highways | "...**is not provided in the given context**..." |
| q_052 | Driver's license requirements | "...sources **do not contain** any information..." |
| q_053 | Cryptocurrency regulations | "...**no specific mention** of regulations..." |
| q_055 | PIT rates in 2035 | "The information provided **does not contain details**..." |
| q_056 | Next Chief Justice | "...**no specific mention**..." |

→ **Model ĐANG refuse đúng**, nhưng regex `REFUSAL_PATTERNS` trong `run_eval.py` không bắt được các phrasing này:
- `"not provided"` — missed
- `"no specific mention"` — missed
- `"do not contain"` / `"does not contain"` — missed
- `"only covers the current law"` (q_055) — missed

**Fix**: mở rộng `REFUSAL_PATTERNS` trong `run_eval.py`:

```python
REFUSAL_PATTERNS = [
    r"\bnot\s+found\b", r"\bcannot\s+answer\b", r"\bno\s+(relevant\s+)?information\b",
    r"\bdo\s+not\s+have\b", r"\bunable\s+to\b", r"\binsufficient\b",
    r"\bkhông\s+tìm\s+thấy\b", r"\bkhông\s+có\s+thông\s+tin\b",
    r"\bno\s+relevant\s+documents?\b", r"\bnot\s+available\b",
    # NEW — add these:
    r"\bnot\s+provided\b", r"\bnot\s+mentioned\b", r"\bno\s+specific\s+mention\b",
    r"\bdoes\s+not\s+(contain|mention|provide|include)\b",
    r"\bdo\s+not\s+contain\b", r"\bcontext\s+does\s+not\b",
    r"\bno\s+(details?|mention|regulations?|information)\s+(about|on|regarding)\b",
]
```

Re-run metrics hoặc just re-aggregate từ per_sample answers (không cần re-query). Expected OOS refusal thật sau fix: **~100%** (tất cả 10 OOS đều refuse đúng, chỉ là phrasing khác).

### Summary assessment

| Aspect | Status |
|--------|:------:|
| Retrieval | 🌟 Excellent (nothing to improve) |
| Answer correctness | 🟢 Good (cos 0.76 + kw 0.83) |
| Citation | 🌟 Perfect (100%) |
| OOS behavior (sau regex fix) | 🌟 Likely excellent |
| False refusal | 🌟 Zero |
| Latency | 🔴 **Unusable for production** — 2.5 min/query on CPU |

---

## Priority action items

1. **[P1 — 5 min]** Mở rộng `REFUSAL_PATTERNS` trong `run_eval.py` → re-aggregate để confirm OOS ~100%
2. **[P1 — Infrastructure]** Latency: switch `qwen2.5:3b` cho dev iteration, hoặc rent GPU cho prod
3. **[P2 — Low priority]** Corpus đã retrievable perfect → tier 1 upgrades (reranker, BM25) **không cần thiết** với corpus này. Để lại cho khi scale corpus.

Với corpus luật 13 PDFs hiện tại, **upgrade duy nhất có ROI là giải quyết latency**, không phải retrieval/generation quality.

---

## Future runs

Template để thêm row mới:

```markdown
| YYYY-MM-DD HH:MM | tag-name | 60 | XX.X% | 0.XXX | 0.XXX | 0.XXX | XX.X% | XX.X% | XX.X% | XXXXX | XXXXX | short note |
```

Manual append hoặc restore `update_benchmark.py` nếu muốn tự động.

### Planned next runs

- [ ] `baseline-3b` — qwen2.5:3b thay qwen3:8b để đo latency floor trên CPU
- [ ] `oos-fix` — sau khi fix REFUSAL_PATTERNS, re-aggregate baseline
- [ ] `prompt-v2` — thử system prompt 6-section (mục tiêu: OOS refusal ↑ cực mạnh)
- [ ] `rerank` — thêm bge-reranker-base (optional, retrieval đã 100%)
