# System Architecture

**Last Updated:** 2026-04-21

## High-Level Overview

RAG Internal Knowledge is a distributed system with 4 main services orchestrated via Docker Compose. Each service has a single responsibility: database persistence, LLM inference, API serving, and frontend rendering.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Frontend (Port 3000)                          │
│                    React 19 + TypeScript + Vite                      │
│              (Nginx reverse proxy + SPA fallback routing)            │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ /api/* (port 8000)
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│                      Backend (Port 8000)                             │
│                   FastAPI + SQLAlchemy async                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐             │
│  │ Auth Module │  │ Documents    │  │ RAG Query       │             │
│  │ (JWT HS256) │  │ - Upload     │  │ - Embed         │             │
│  │ - register  │  │ - Parse      │  │ - Retrieve      │             │
│  │ - login     │  │ - Chunk      │  │ - Generate      │             │
│  │             │  │ - Embed      │  │ - Stream (SSE)  │             │
│  │             │  │ - Status     │  │                 │             │
│  └─────────────┘  └──────┬───────┘  └────────┬────────┘             │
│                          │                    │                     │
│                    BackgroundTasks       Ollama HTTP                │
│                    (async processing)    (async)                    │
└────────────────────────────┬─────────────────┬──────────────────────┘
                             │                 │
                             │        ┌────────▼──────┐
                             │        │ Ollama (11434)│
                             │        │ Qwen3 8B      │
                             │        │ (local LLM)   │
                             │        └───────────────┘
                             │
        ┌────────────────────▼──────────────────────┐
        │  PostgreSQL 16 + pgvector (Port 5432)    │
        │  ┌──────────┐  ┌──────────┐ ┌───────────┐│
        │  │users     │  │documents │ │doc_chunks ││
        │  │          │  │          │ │           ││
        │  │UUID, jwt │  │UUID, meta│ │embedding  ││
        │  │hashed_pw │  │status    │ │ (384-dim) ││
        │  │email     │  │chunks    │ │ IVFFlat   ││
        │  └──────────┘  └──────────┘ │ cosine idx││
        │                             └───────────┘│
        └─────────────────────────────────────────┘
```

## Component Responsibilities

### Frontend (React + Nginx)

**Responsibility:** User interface, form validation, API client, auth state management

**Key Functions:**
- Render login/register forms (email + password validation)
- Display chat interface with message history + sources
- Handle document upload (drag-drop, file type validation)
- Manage JWT token in localStorage
- Stream SSE responses in real-time
- Auto-redirect to login on 401

**Tech Stack:**
- React 19 + TypeScript 5 (strict mode)
- Tailwind CSS 4 (utility-first styling)
- Axios 1.14 (HTTP client with interceptors)
- React Router 7 (client-side routing)

**Nginx Config:**
- SPA fallback to index.html (catch 404 → return index.html)
- Reverse proxy /api/* to backend:8000
- No caching (cache-control: no-cache)
- SSE support (proxy_buffering off, 300s timeout)

### Backend (FastAPI)

**Responsibility:** API logic, auth, document processing, RAG orchestration, database queries

**Routes & Endpoints:**

```
POST   /auth/register          → create user + return JWT
POST   /auth/login              → validate credentials + return JWT
GET    /health                  → {"status": "ok", "version": "0.1.0"}

POST   /documents/upload        → save file, create document record, trigger async processing
GET    /documents               → list user's documents
GET    /documents/{id}          → get single document details
DELETE /documents/{id}          → delete document + all chunks

POST   /rag/query               → embed → retrieve → generate (full response)
GET    /rag/query-stream        → embed → retrieve → generate (SSE stream)
```

**Key Services:**

| Service | Module | Responsibility |
|---------|--------|-----------------|
| **AuthService** | auth/ | Register, hash password, create/verify JWT tokens |
| **DocumentService** | documents/ | Upload handler, background task orchestration, status updates |
| **ParserService** | documents/parser.py | PDF/DOCX/TXT/MD → text extraction |
| **ChunkerService** | documents/chunker.py | Recursive token-based splitting (512 tokens, 50 overlap) |
| **EmbeddingService** | embeddings/ | Singleton, loads model at startup, batch inference |
| **RetrieverService** | rag/retriever.py | pgvector cosine similarity (user-scoped) |
| **GeneratorService** | rag/generator.py | Ollama HTTP calls, streaming LLM responses |
| **RAGService** | rag/service.py | Orchestrates embed → retrieve → generate |

### Database (PostgreSQL + pgvector)

**Responsibility:** Persistent storage, vector indexing, user/document isolation

**Tables:**

| Table | Columns | Constraints |
|-------|---------|-------------|
| **users** | id (UUID PK), email (unique), hashed_password, full_name, is_active, created_at, updated_at | 1 user per email |
| **documents** | id (UUID PK), user_id (FK→users CASCADE), filename, file_type, file_size, status (pending\|processing\|completed\|failed), chunk_count, created_at, updated_at | FK ensures user exists |
| **document_chunks** | id (UUID PK), document_id (FK→documents CASCADE), content (TEXT), chunk_index, embedding (VECTOR 384), metadata_ (JSONB), created_at | FK ensures doc exists |

**Indexes:**
- `users.email` — unique, for login lookups
- `documents.user_id` — fast filtering by owner
- `documents.status` — fast status queries
- `document_chunks.document_id` — cascade deletes
- `document_chunks.embedding` — IVFFlat (cosine_ops, lists=100) for vector search

**Vector Search:**
```sql
SELECT * FROM document_chunks
WHERE document_id IN (SELECT id FROM documents WHERE user_id = current_user_id)
ORDER BY embedding <-> query_embedding  -- cosine distance
LIMIT 5;
```

### Ollama (LLM Service)

**Responsibility:** Generate human-readable answers from context + query

**Config:**
- Base URL: `OLLAMA_BASE_URL` (default `http://ollama:11434` in Docker, `localhost:11434` locally)
- Model: `LLM_MODEL` (default `qwen3:8b`, configurable)
- Inference params: `num_predict=1024` (max tokens), `temp=0.1` (low randomness), `num_ctx=8192` (context window)
- Timeout: 120s non-streaming, 300s streaming

**API Call:**
```bash
curl http://ollama:11434/api/chat \
  -d '{
    "model": "qwen3:8b",
    "messages": [{"role": "user", "content": "context...\n\nquestion..."}],
    "stream": true,
    "options": {"num_predict": 1024, "num_ctx": 8192, "temperature": 0.1}
  }'
```

## Data Flows

### 1. Document Ingestion Pipeline

```
User uploads file
    ↓
POST /documents/upload (multipart/form-data)
    ↓
Validate: extension whitelist, size ≤50MB
    ↓
Save file to ./uploads/{uuid}_{filename}
    ↓
Create Document record (status=pending)
    ↓
Return 201 with document metadata
    ↓
BackgroundTask (async) starts processing
    ↓
[Parse] Extract text (pypdf/python-docx/plain read)
    ↓
[Chunk] Split into ~512-token chunks, 50-token overlap
    ↓
[Embed] Generate 384-dim vectors (sentence-transformers)
    ↓
[Store] Save DocumentChunks to DB with embeddings
    ↓
Update Document (status=completed, chunk_count=N)
    ↓
Frontend polls GET /documents, sees status change
```

**Async Processing:**
- Uses FastAPI BackgroundTasks (simple, no queue)
- Failures logged but document stays in "processing" or updates to "failed"
- No retry mechanism (Phase 2 candidate)

### 2. RAG Query Flow

```
User submits question
    ↓
POST /rag/query OR GET /rag/query-stream
    ↓
Validate query (1-2000 chars), top_k (1-20, default 5)
    ↓
Embed query (same model as docs: all-MiniLM-L6-v2)
    ↓
pgvector cosine similarity search
    ├─ Filter by current_user.id (document isolation)
    ├─ ORDER BY embedding <-> query_embedding
    └─ LIMIT top_k
    ↓
Assemble context from top-k chunks
    ↓
Build Ollama prompt: "Context: [chunks]\n\nQuestion: [query]"
    ↓
POST /api/chat (Ollama) with stream={true|false}
    ↓
If stream=true:
    ├─ Open SSE connection
    ├─ Stream token-by-token as "data: {event}" lines
    └─ Close with "data: {done}"
If stream=false:
    └─ Return full answer + sources as JSON
    ↓
Frontend displays answer + citation cards
```

**SSE Event Format:**
```
event: sources
data: {"sources": [{"document_id": "...", "filename": "...", "content": "...", "similarity_score": 0.89}]}

event: delta
data: {"content": "According"}

event: delta
data: {"content": " to"}

...

event: done
data: {}
```

### 3. Authentication Flow

```
POST /auth/register
    ↓
Validate email format, password ≥8 chars
    ↓
Check email doesn't exist
    ↓
Hash password (bcrypt, cost=12)
    ↓
Create User record
    ↓
Generate JWT token (HS256, exp=24h)
    ↓
Return user + token
    ↓
Frontend stores token in localStorage
    ↓
All subsequent requests include Authorization: Bearer {token}
    ↓
Middleware (get_current_user) verifies token:
    ├─ Decode JWT
    ├─ Extract user_id
    ├─ Fetch user from DB
    └─ Pass to endpoint
```

**JWT Payload:**
```json
{
  "sub": "user-uuid",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Token Validation:**
- Signature verified with SECRET_KEY (HS256)
- Expiry checked against current time
- User must exist and is_active=true

## Security Model

### Data Isolation

- **Document Scoping:** All document queries filter `document.user_id == current_user.id`
- **Retriever Implementation:** Enforced at query time, not through RBAC
- **No cross-user access:** Even if user guesses UUID, retriever filters out unowned docs

### Authentication

- **Register:** Email + password → bcrypt(password, cost=12) → User record
- **Login:** Email + password → compare bcrypt → issue JWT (HS256, 24h expiry)
- **Per-request:** JWT verified via `get_current_user()` dependency

### File Handling

- **Extension Whitelist:** Only pdf, docx, txt, md allowed
- **Size Limit:** 50MB max per file
- **Storage:** ./uploads/{uuid}_{filename} (prevents directory traversal)
- **No server-side caching:** Each parse is fresh (Phase 3 candidate)

### Network

- **CORS:** Restricted to `CORS_ORIGINS` (default localhost:5173 dev, localhost:3000 Docker)
- **HTTPS:** Not enforced in Docker (use TLS termination in production)
- **SSE Token:** Passed in query param (not ideal, but EventSource limitation)

### Known Security Gaps

1. **JWT in localStorage** — vulnerable to XSS; use httpOnly cookies (Phase 2)
2. **No refresh tokens** — 24h expiry forces re-login; add refresh token endpoint (Phase 2)
3. **No rate limiting** — DoS risk; implement per-user quotas (Phase 2)
4. **SSE query param token** — visible in logs/browser history; use WebSocket (Phase 2+)
5. **No HTTPS** — use reverse proxy with TLS in production

## Deployment Topology

### Docker Compose

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    ports: [5432]
    environment: POSTGRES_DB=rag_db, POSTGRES_USER/PASSWORD
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck: pg_isready -U postgres

  ollama:
    image: ollama/ollama:latest
    ports: [11434]
    volumes: [ollama-models:/root/.ollama]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia  # GPU passthrough (optional)

  backend:
    build: ./backend
    ports: [8000]
    environment: DATABASE_URL, SECRET_KEY, OLLAMA_BASE_URL, LLM_MODEL, EMBEDDING_MODEL, ...
    depends_on: [db, ollama]
    volumes: [./backend/uploads:/app/uploads]
    command: poetry run alembic upgrade head && poetry run uvicorn ...

  frontend:
    build: ./frontend
    ports: [3000]
    environment: VITE_API_URL=http://backend:8000
    depends_on: [backend]
```

### Resource Requirements

| Service | CPU | RAM | Storage | Notes |
|---------|-----|-----|---------|-------|
| db (PostgreSQL) | 2 cores | 2GB | 10GB+ | Grows with chunks |
| ollama | 2+ cores | 6-16GB | 5-10GB | LLM model cache |
| backend | 2 cores | 2GB | 500MB | Embedding model cache |
| frontend | 0.5 core | 256MB | 100MB | Static files |
| **Total** | **6+ cores** | **10-24GB** | **15-25GB** | Scales with docs |

**GPU:**
- Ollama: NVIDIA GPU (8GB+ VRAM recommended for fast inference)
- Pass via `deploy.resources.devices` in docker-compose.yml
- Fallback to CPU (slower, ~5-10x slower generation)

## Performance & Scalability

### Query Latency Breakdown

| Operation | Typical | Max |
|-----------|---------|-----|
| Embed query | 50-100ms | 200ms |
| Vector search (pgvector IVFFlat) | 100-300ms | 500ms |
| LLM generation (Ollama) | 5-30s | 120s |
| **Total (excluding LLM)** | **150-400ms** | **700ms** |
| **Total (including LLM, 8B model)** | **5-30s** | **120s** |

**Bottleneck:** LLM generation (Ollama), not retrieval.

### Scalability Limits

| Metric | Limit | Notes |
|--------|-------|-------|
| Concurrent users | ~50 | Single machine, limited by FastAPI/DB connections |
| Total documents | 1000+ | Feasible; vector search scales linearly with chunks |
| Total chunks | 100k+ | IVFFlat index recommended; exact search OK <1k chunks |
| Query throughput | 10 queries/sec | Bottlenecked by Ollama (slow) |
| Document size | 50MB | Parser may timeout on huge PDFs |

**Scale-out Strategy (Phase 3):**
- Load balancer (Nginx) → multiple backend instances
- Redis for embedding/query caching
- Celery/RQ for document processing queue
- Separate Ollama cluster
- Read replicas for PostgreSQL

## Monitoring & Observability

**Currently None.** Phase 3 candidates:
- Application metrics (Prometheus)
- Structured logging (JSON, ELK stack)
- Distributed tracing (Jaeger)
- Health checks (`GET /health` only)

**Recommended:**
- Backend: Prometheus metrics (API latency, error rates, token usage)
- Database: Slow query logs, pg_stat_statements
- Frontend: Sentry for error tracking, Amplitude for analytics
- Ollama: Resource monitoring (GPU/CPU/RAM)
