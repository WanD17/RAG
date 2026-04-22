# Những điều cần biết khi xây hệ thống RAG

Tổng hợp kinh nghiệm + tham chiếu đến project **Internal Knowledge RAG** làm ví dụ thực tế.

---

## 1. Ingestion — đưa tài liệu vào hệ thống

- **Parse đa định dạng**: PDF (`pypdf`), DOCX (`python-docx`), TXT/MD (plain text). Mỗi loại có edge case riêng (PDF scan không có text layer → phải OCR; DOCX có table/image phức tạp).
- **Chunking là bước quan trọng nhất**. Chunk quá nhỏ → mất ngữ cảnh; quá lớn → embedding loãng, vượt context LLM. Project này: **512 tokens + 50 overlap** qua `tiktoken cl100k_base`, recursive split theo separator (`\n\n` → `\n` → `. ` → ` `).
- **Overlap** tránh câu trả lời bị cắt đôi giữa 2 chunk.
- **Metadata mỗi chunk**: `document_id`, `filename`, `chunk_index` — để cite source và filter sau này.

## 2. Embeddings

- **Chọn model theo trade-off dim/chất lượng/tốc độ**. Project dùng `all-MiniLM-L6-v2` (384 dim, ~90MB, chạy CPU được). Alternatives: `bge-base-en` (768), `e5-large` (1024) — chất lượng cao hơn nhưng nặng + tốn storage.
- **Normalize vector** (L2) nếu dùng cosine similarity — inner product sẽ tương đương, query nhanh hơn.
- **Batch embed** khi ingest (project dùng batch 32) thay vì embed từng chunk.
- **Load 1 lần ở startup** (singleton pattern như `embeddings/service.py`) — không load lại mỗi request.

## 3. Vector Store

- **pgvector vs Qdrant vs Milvus vs Pinecone**: pgvector đơn giản nhất (1 DB, không service riêng) — hợp với MVP < vài triệu chunk. Vượt quá thì chuyển Qdrant/Milvus.
- **Index type**: project dùng **IVFFlat cosine** (`lists=100`). HNSW chất lượng cao hơn nhưng tốn RAM. IVFFlat cần `ANALYZE` sau khi insert nhiều mới hiệu quả.
- **Similarity metric**: cosine cho semantic text (đã normalize), L2 cho feature vectors, inner product cho recsys.

## 4. Retrieval

- **Top-k = 3–10**. Project default 5. Quá ít → thiếu ngữ cảnh; quá nhiều → noise + tăng context LLM.
- **Per-user scoping**: luôn filter theo `user_id` trước khi similarity search → tránh data leak giữa tenants (xem `rag/retriever.py`).
- **Hybrid search** (vector + BM25/keyword) thường cho kết quả tốt hơn pure vector — nhưng phức tạp thêm. MVP chưa cần.
- **Re-ranking** với cross-encoder (bge-reranker) sau top-k giúp precision tăng rõ rệt — thêm khi đã đo được retrieval miss.
STAGE=DEV

### Logs env
LOG_PATH=logs
APP_NAME=prepress-automatic-verfication-app
API_APP_NAME=prepress-automatic-verfication-api

### Database env
#MONGO_URI=mongodb://rpac_prepress:rpac_prepressEV@192.168.154.7:27017/?authSource=PrepressEV_Database
MONGO_URI=mongodb://localhost:27017


#Storage location
#STORAGE_PATH=P:\PrepressCTP-F1\softwware\Prepress_storage
STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepress_EV_storage
PACKAGING_STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\Packaging


PUBLIC_STORAGE_PRINTSHEETS_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepressEV_public_storage

### Email env
MAIL_SENDER=rpacprepressev@gmail.com
MAIL_APP_PASS='veim ucvh zacv ojvn'

### AI workers env
SRC_ICC_PROFILE=app\ai_workers\constants\USWebCoatedSWOP.icc
DST_ICC_PROFILE=app\ai_workers\constants\PAL_SECAM.icc

#JWT
JWT_SECRET_KEY=74f0995aeab518cf632302597cc60fa88acc4d186e4ff79779b1d0945dab8e0a
JWT_ALGORITHM=HS256
JWT_TOKEN_EXPIRY_HOURS=24STAGE=DEV

### Logs env
LOG_PATH=logs
APP_NAME=prepress-automatic-verfication-app
API_APP_NAME=prepress-automatic-verfication-api

### Database env
#MONGO_URI=mongodb://rpac_prepress:rpac_prepressEV@192.168.154.7:27017/?authSource=PrepressEV_Database
MONGO_URI=mongodb://localhost:27017


#Storage location
#STORAGE_PATH=P:\PrepressCTP-F1\softwware\Prepress_storage
STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepress_EV_storage
PACKAGING_STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\Packaging


PUBLIC_STORAGE_PRINTSHEETS_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepressEV_public_storage

### Email env
MAIL_SENDER=rpacprepressev@gmail.com
MAIL_APP_PASS='veim ucvh zacv ojvn'

### AI workers env
SRC_ICC_PROFILE=app\ai_workers\constants\USWebCoatedSWOP.icc
DST_ICC_PROFILE=app\ai_workers\constants\PAL_SECAM.icc

#JWT
JWT_SECRET_KEY=74f0995aeab518cf632302597cc60fa88acc4d186e4ff79779b1d0945dab8e0a
JWT_ALGORITHM=HS256
JWT_TOKEN_EXPIRY_HOURS=24STAGE=DEV

### Logs env
LOG_PATH=logs
APP_NAME=prepress-automatic-verfication-app
API_APP_NAME=prepress-automatic-verfication-api

### Database env
#MONGO_URI=mongodb://rpac_prepress:rpac_prepressEV@192.168.154.7:27017/?authSource=PrepressEV_Database
MONGO_URI=mongodb://localhost:27017


#Storage location
#STORAGE_PATH=P:\PrepressCTP-F1\softwware\Prepress_storage
STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepress_EV_storage
PACKAGING_STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\Packaging


PUBLIC_STORAGE_PRINTSHEETS_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepressEV_public_storage

### Email env
MAIL_SENDER=rpacprepressev@gmail.com
MAIL_APP_PASS='veim ucvh zacv ojvn'

### AI workers env
SRC_ICC_PROFILE=app\ai_workers\constants\USWebCoatedSWOP.icc
DST_ICC_PROFILE=app\ai_workers\constants\PAL_SECAM.icc

#JWT
JWT_SECRET_KEY=74f0995aeab518cf632302597cc60fa88acc4d186e4ff79779b1d0945dab8e0a
JWT_ALGORITHM=HS256
JWT_TOKEN_EXPIRY_HOURS=24STAGE=DEV

### Logs env
LOG_PATH=logs
APP_NAME=prepress-automatic-verfication-app
API_APP_NAME=prepress-automatic-verfication-api

### Database env
#MONGO_URI=mongodb://rpac_prepress:rpac_prepressEV@192.168.154.7:27017/?authSource=PrepressEV_Database
MONGO_URI=mongodb://localhost:27017


#Storage location
#STORAGE_PATH=P:\PrepressCTP-F1\softwware\Prepress_storage
STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepress_EV_storage
PACKAGING_STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\Packaging


PUBLIC_STORAGE_PRINTSHEETS_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepressEV_public_storage

### Email env
MAIL_SENDER=rpacprepressev@gmail.com
MAIL_APP_PASS='veim ucvh zacv ojvn'

### AI workers env
SRC_ICC_PROFILE=app\ai_workers\constants\USWebCoatedSWOP.icc
DST_ICC_PROFILE=app\ai_workers\constants\PAL_SECAM.icc

#JWT
JWT_SECRET_KEY=74f0995aeab518cf632302597cc60fa88acc4d186e4ff79779b1d0945dab8e0a
JWT_ALGORITHM=HS256
JWT_TOKEN_EXPIRY_HOURS=24STAGE=DEV

### Logs env
LOG_PATH=logs
APP_NAME=prepress-automatic-verfication-app
API_APP_NAME=prepress-automatic-verfication-api

### Database env
#MONGO_URI=mongodb://rpac_prepress:rpac_prepressEV@192.168.154.7:27017/?authSource=PrepressEV_Database
MONGO_URI=mongodb://localhost:27017


#Storage location
#STORAGE_PATH=P:\PrepressCTP-F1\softwware\Prepress_storage
STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepress_EV_storage
PACKAGING_STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\Packaging


PUBLIC_STORAGE_PRINTSHEETS_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepressEV_public_storage

### Email env
MAIL_SENDER=rpacprepressev@gmail.com
MAIL_APP_PASS='veim ucvh zacv ojvn'

### AI workers env
SRC_ICC_PROFILE=app\ai_workers\constants\USWebCoatedSWOP.icc
DST_ICC_PROFILE=app\ai_workers\constants\PAL_SECAM.icc

#JWT
JWT_SECRET_KEY=74f0995aeab518cf632302597cc60fa88acc4d186e4ff79779b1d0945dab8e0a
JWT_ALGORITHM=HS256
JWT_TOKEN_EXPIRY_HOURS=24STAGE=DEV

### Logs env
LOG_PATH=logs
APP_NAME=prepress-automatic-verfication-app
API_APP_NAME=prepress-automatic-verfication-api

### Database env
#MONGO_URI=mongodb://rpac_prepress:rpac_prepressEV@192.168.154.7:27017/?authSource=PrepressEV_Database
MONGO_URI=mongodb://localhost:27017


#Storage location
#STORAGE_PATH=P:\PrepressCTP-F1\softwware\Prepress_storage
STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepress_EV_storage
PACKAGING_STORAGE_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\Packaging


PUBLIC_STORAGE_PRINTSHEETS_PATH=D:\Project\Rpac\release\PrepressEV_Realease_12-09-2025\prepressEV_public_storage

### Email env
MAIL_SENDER=rpacprepressev@gmail.com
MAIL_APP_PASS='veim ucvh zacv ojvn'

### AI workers env
SRC_ICC_PROFILE=app\ai_workers\constants\USWebCoatedSWOP.icc
DST_ICC_PROFILE=app\ai_workers\constants\PAL_SECAM.icc

#JWT
JWT_SECRET_KEY=74f0995aeab518cf632302597cc60fa88acc4d186e4ff79779b1d0945dab8e0a
JWT_ALGORITHM=HS256
JWT_TOKEN_EXPIRY_HOURS=24
## 5. Generation

- **Prompt template cứng**: system prompt bảo LLM chỉ trả lời dựa trên context (tránh hallucination). Ví dụ `generator.py`: *"Answer based solely on the provided context"*.
- **Context assembly**: nối chunks với citation (`[filename:chunk_index]`) để LLM có thể reference nguồn.
- **Tham số LLM**: `temperature=0.1` (ít creative, bám nguồn), `num_ctx` vừa đủ chứa context + query.
- **Streaming bắt buộc với UX tốt**: dùng SSE (Server-Sent Events). Project có 2 endpoint: `/rag/query` (full response) và `/rag/query-stream` (SSE).
- **Timeout cần dài**: generation 1024 token có thể mất >30s. Project timeout 120s (non-stream), 300s (stream).

## 6. Self-hosted LLM (Ollama)

- **GPU passthrough** (docker-compose nvidia driver) là bắt buộc cho throughput — CPU chạy qwen3:8b cực chậm.
- **Model size vs RAM**: 8B model cần ~6GB VRAM fp16, ~4GB q4. Chọn theo hardware.
- **Cold start**: lần đầu query phải load model vào VRAM (~10–30s). Keep-alive.

## 7. Bảo mật & Multi-tenancy

- **Auth**: JWT đủ cho internal. Lưu ý: project **decode JWT ở client-side** (naive base64) — OK cho UI state, **không** được làm vậy cho authorization logic.
- **SSE & Bearer token**: `EventSource` không support custom headers → project truyền token qua query param. Rủi ro: log proxy có thể leak token. Nginx `access_log off` cho endpoint này trong prod.
- **User scoping trong retrieval** (không phải chỉ ở API layer) — defense in depth.
- **Rate limiting** cần thiết sớm (embed + LLM đều tốn tài nguyên). Project chưa có → Phase 2 roadmap.

## 8. Operations

- **Async processing**: ingest phải background (parse + embed lâu). Project dùng `BackgroundTasks` của FastAPI — đủ cho nhẹ, nặng thì Celery/RQ + Redis.
- **Status state machine**: `pending → processing → completed/failed`, FE poll (2s trong project này) hoặc WebSocket.
- **Observability**: log retrieval score distribution (nếu top-1 < 0.5 thường → câu hỏi không liên quan doc). Log query text + top_k sources + latency từng stage (embed/retrieve/generate).
- **Cost & scaling**: embedding batch size, vector index rebuild sau mass delete, disk cho uploads (project lưu local — cần S3/object storage khi scale).

## 9. Đánh giá chất lượng

- **Retrieval metrics**: Hit@k, MRR trên bộ test Q&A có golden answer.
- **Generation metrics**: faithfulness (có hallucinate không), answer relevance. Dùng LLM-as-judge (Ragas framework) hoặc manual eval.
- **User feedback loop**: thumbs up/down → dataset để tuning.

## 10. Bẫy phổ biến

- Chunk cắt giữa câu / giữa bảng → retrieval sai. Giải pháp: semantic chunking hoặc layout-aware parsers (unstructured.io).
- Embed model train trên English nhưng dữ liệu Tiếng Việt → dùng multilingual model (`paraphrase-multilingual-MiniLM`, `bge-m3`).
- Không test với "câu hỏi không có trong doc" → LLM bịa. Prompt phải có fallback: *"If context doesn't contain the answer, say you don't know"*.
- Migration vector schema đau đầu — thay embedding model = phải re-embed toàn bộ. Lưu `embedding_model_name` trong chunk metadata để support version.

---

## Tóm tắt

**RAG pipeline** = Parse → Chunk → Embed → Store → Retrieve → Generate

**Thứ tự chỗ dễ sai nhất:**
1. Chunking
2. Retrieval filter (user scoping, metadata)
3. Prompt (hallucination fallback)
4. Model choice (embedding + LLM)

Project `Internal Knowledge RAG` là MVP tham khảo đủ 6 bước trên.
