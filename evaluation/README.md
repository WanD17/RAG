# RAG Evaluation

Automated evaluation của backend RAG dựa trên 60 golden samples (Claude pre-generated từ 13 Law PDFs). Zero cost API, zero LLM-judge, deterministic metrics.

## File layout

```
evaluation/
├── golden_set.json        # 60 samples (50 in-scope + 10 OOS/adversarial)
├── upload_docs.py         # [1-time] Register + upload 13 PDFs
├── run_eval.py            # [each run] Query backend, compute metrics
├── update_benchmark.py    # [after each run] Append to BENCHMARK.md
├── compare.py             # Diff 2 runs side-by-side
├── BENCHMARK.md           # History log, auto-updated
├── README.md              # This file
├── .config.json           # JWT + doc IDs (auto-generated)
├── .last_run_checkpoint.json  # Resume state (auto-generated)
└── results/
    └── <timestamp>-<tag>.json
```

## Metrics (8 core + latency)

| Group | Metric | Target |
|-------|--------|:------:|
| Retrieval | `doc_hit@5` — GT doc trong top-5 | > 70% |
| Retrieval | `MRR` — rank của GT doc | > 0.5 |
| Answer | `cosine_sim` — sim với reference answer | > 0.6 |
| Answer | `keyword_recall` — required keywords trong answer | > 0.5 |
| Answer | `citation_coverage` — answer có cite source | > 80% |
| Behavior | `OOS_refusal_accuracy` — OOS refused đúng | > 70% |
| Behavior | `false_refusal` — in-scope refused nhầm | < 10% |
| Latency | `p50 / p95 / p99 / mean / max` | p95 < 10s |

Thresholds chi tiết xem `BENCHMARK.md`.

---

## Prerequisites

1. **Backend + Ollama chạy**:
   ```bash
   cd "D:/New folder"
   docker compose up -d
   curl http://localhost:8000/health   # verify
   ```

2. **LLM model đã pull**:
   ```bash
   docker compose exec ollama ollama pull qwen3:8b
   # CPU chậm? Switch model nhẹ hơn cho dev:
   # docker compose exec ollama ollama pull qwen2.5:3b
   # Edit backend/.env: LLM_MODEL=qwen2.5:3b + docker compose restart backend
   ```

3. **Python deps cho eval**:
   ```bash
   pip install sentence-transformers httpx numpy
   ```

---

## Workflow đầy đủ

### Step 1 — Upload 13 PDFs (1 lần duy nhất)

```bash
cd "D:/New folder"
python evaluation/upload_docs.py
```

Script tự động:
- Register user `eval@example.com` (hoặc login nếu đã tồn tại)
- Upload từng PDF trong `Law_docs/`
- Chờ status `completed` (embedding xong) — 10-30 phút tùy CPU
- Lưu JWT + doc list vào `evaluation/.config.json`

**Expected output:**
```
[auth] registered and logged in
[upload] 01_constitution_of_vietnam_2013.pdf
...
[processing] waiting for 13 new docs to finish embedding...
[done] 13 docs ready. Config saved to evaluation/.config.json
```

### Step 2 — Smoke test (5-10 phút)

Verify setup với 5 samples:

```bash
python evaluation/run_eval.py --limit 5 --tag smoke
```

Nếu OK → tiến tới Step 3. Nếu không → check `results/<timestamp>-smoke.json` xem error chi tiết.

### Step 3 — Full baseline eval

```bash
python evaluation/run_eval.py --tag baseline
```

**Thời gian** (CPU only, 60 samples):
| LLM Model | Ước tính |
|-----------|:---:|
| qwen2.5:3b | 30-60 phút |
| qwen3:8b | 3-6 giờ (chạy overnight) |

**Interrupt-safe**: Ctrl+C bất cứ lúc nào → checkpoint auto-saved. Resume:
```bash
python evaluation/run_eval.py --resume --tag baseline
```

Output: `evaluation/results/<timestamp>-baseline.json` + console summary.

### Step 4 — Append vào BENCHMARK.md

Ngay sau khi eval xong:

```bash
python evaluation/update_benchmark.py
```

Script tự detect file JSON mới nhất trong `results/`, parse summary, append row vào bảng benchmark + thêm note chi tiết. Idempotent — chạy lại không duplicate.

**Thêm note ngắn cho row:**
```bash
python evaluation/update_benchmark.py --note "baseline, no prompt engineering"
```

**Chỉ định file cụ thể:**
```bash
python evaluation/update_benchmark.py results/20260423-140000-baseline.json
```

### Step 5 — Implement improvement → eval → compare

Sau khi sửa hệ thống (ví dụ thêm reranker):

```bash
# Restart backend
docker compose restart backend

# Eval mới
python evaluation/run_eval.py --tag after-reranker

# Update benchmark log
python evaluation/update_benchmark.py --note "added bge-reranker-base"

# Compare 2 runs side-by-side
python evaluation/compare.py \
  evaluation/results/20260423-140000-baseline.json \
  evaluation/results/20260424-100000-after-reranker.json
```

`compare.py` output bảng delta + flag `✗ WORSE !!` cho regression > threshold (3% pct, 0.03 scalar, 15% latency).

---

## One-liner tiện lợi

Chạy eval + update benchmark trong 1 lệnh:

```bash
# Windows cmd
python evaluation\run_eval.py --tag foo && python evaluation\update_benchmark.py

# Bash/WSL
python evaluation/run_eval.py --tag foo && python evaluation/update_benchmark.py --note "foo change"
```

---

## Interpret results — cheat sheet

| Vấn đề | Symptom | Fix priority |
|--------|---------|:---:|
| LLM bịa khi OOS | `OOS_refusal < 40%` | 🔴 System prompt + grounding |
| Không cite source | `citation_coverage < 60%` | 🔴 System prompt citation rule |
| Retrieval yếu | `doc_hit@5 < 60%` | 🟡 Reranker / BM25 hybrid / embed model |
| Answer lạc đề | `cosine_sim < 0.5` but `doc_hit@5 > 70%` | 🟡 Prompt engineering hoặc chunk context |
| Quá thận trọng | `false_refusal > 15%` | 🟡 Relax refusal criteria |
| Quá chậm | `p95 > 15s` | 🟡 Giảm num_predict / switch model nhỏ |
| Crash | Lots of `error` in `per_sample` | 🔴 Check backend logs |

---

## Edit golden set

Thêm/sửa samples trực tiếp trong `golden_set.json`. Schema:

```json
{
  "id": "q_061",
  "question": "Your question here",
  "reference_answer": "Expected answer with key facts",
  "category": "in_scope",                       // or "out_of_scope"
  "source_doc": "04_labor_code_2019.pdf",       // null for OOS
  "source_section": "Article X",                // optional
  "required_keywords": ["key", "numbers"],      // must appear in answer
  "must_refuse": false,                         // true for OOS
  "difficulty": "easy"                          // or "medium" / "hard"
}
```

**Quy tắc cập nhật golden set:**
- Đổi chunking/embedding/LLM → **KHÔNG** cần đổi golden
- Thêm PDFs mới → thêm samples liên quan
- Sửa PDFs cũ → kiểm tra samples bị ảnh hưởng

Khi thay đổi lớn, bump `version` trong `golden_set.json` để tracking.

---

## Troubleshooting

**`ConnectionError: backend not reachable`**
→ `docker compose ps` — backend có up không? `curl http://localhost:8000/health`

**`token expired / 401`**
→ Xóa `evaluation/.config.json` và chạy lại `upload_docs.py`

**`Ollama timeout`**
→ Ollama quá chậm với model hiện tại. Check `docker compose logs ollama`. Giảm `num_predict` trong `backend/src/rag/generator.py` từ 1024 xuống 512. Hoặc switch model nhẹ hơn.

**`sentence-transformers download slow`**
→ Lần đầu chạy, MiniLM model (~90MB) sẽ download. Chạy: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"` pre-cache.

**`encoding errors khi mở JSON`**
→ Scripts đã dùng utf-8 explicit. Nếu tool ngoài fail, mở bằng VSCode (auto-detect UTF-8).

**Eval báo `false_refusal: 100%`**
→ Backend trả lời rỗng hoặc toàn "not found". Query thủ công bằng `curl` hoặc UI để debug.

---

## Xem benchmark history

```bash
# Windows
type evaluation\BENCHMARK.md

# Hoặc mở trong editor
code evaluation/BENCHMARK.md
```

File auto-updated với mỗi `update_benchmark.py`. Chronological table + chi tiết từng run.
