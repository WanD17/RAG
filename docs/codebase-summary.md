# Codebase Summary

**Last Updated:** 2026-04-27 | **Project Version:** 0.1.0

## Overview

RAG Internal Knowledge is a monorepo containing a FastAPI backend (Python) and React frontend (TypeScript), with Docker Compose orchestration for PostgreSQL, Qdrant, pgadmin, Ollama, and Nginx services.

**Backend Code:** ~1,676 LOC | **Frontend Code:** ~1,290 LOC | **Total Tokens:** ~48k | **Deployable Units:** 2 (backend, frontend)

## Backend (`/backend`)

**Tech:** Python 3.11, FastAPI 0.111.0, SQLAlchemy 2.0.30 async, Pydantic 2.7

### Core Modules

| Module | Files | Purpose | Key Classes/Functions |
|--------|-------|---------|----------------------|
| **auth** | 4 files | User authentication & JWT (HS256, 24h) | `User` (model), `register()`, `login()`, `get_current_user()` |
| **documents** | 5 files | Upload, parse, chunk, embed pipeline | `Document`, `DocumentChunk` (models), `upload()`, background task processing |
| **embeddings** | 1 file | sentence-transformers/all-MiniLM-L6-v2 singleton | `EmbeddingService`, `embed_text()`, `embed_texts()` (batch, size=32) |
| **rag** | 6+ files | Hybrid retrieval + reranking + streaming | `retrieve()` (Qdrant + Postgres FTS, RRF), `rerank()` (BAAI/bge-reranker), `generate()` (Ollama, SSE) |
| **db** | 3 files | AsyncSession, models, migrations | `Base`, `BaseModel` (UUID + timestamps), `get_session()` |

### File Count by Purpose

| Category | Count | Details |
|----------|-------|---------|
| Models | 4 | User, Document, DocumentChunk, + base |
| Schemas (Pydantic) | 5 | Request/response validation |
| Routers | 4 | Auth, documents, RAG, + health |
| Services | 5 | Auth, documents, embeddings, RAG, retrieval |
| Parsers/Utilities | 3 | PDF, DOCX, TXT/MD, chunking, utilities |
| Config/DB | 4 | Settings, database session, base, dependencies |
| Tests | 2 | conftest, test_health.py only |
| Migrations | 2 | Initial schema (users, documents, chunks) + Alembic config |

### Entry Points

- **Main:** `src/main.py` (FastAPI app, lifespan, CORS, routers)
- **Config:** `src/config.py` (pydantic-settings, reads .env)
- **Database:** `src/db/session.py` (async engine + session factory)
- **Auth:** `src/dependencies.py` (JWT dependency injection)

### Key Design Patterns

- **Async throughout** — AsyncSession, async/await, asyncpg driver
- **Dependency injection** — FastAPI Depends for auth, DB session
- **Background tasks** — BackgroundTasks for document processing (no queue)
- **Singleton pattern** — EmbeddingService loaded once at startup via lifespan
- **Modular structure** — Feature-based organization (auth/, documents/, rag/)

### Database Schema

```sql
-- users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE
);

-- documents
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  user_id UUID FOREIGN KEY REFERENCES users(id) ON DELETE CASCADE,
  filename VARCHAR(500) NOT NULL,
  file_type VARCHAR(50) NOT NULL,
  file_size BIGINT NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',  -- pending|processing|completed|failed
  chunk_count INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE
);

-- document_chunks (embeddings moved to Qdrant)
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY,
  document_id UUID FOREIGN KEY REFERENCES documents(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)),
  metadata_ JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX ix_documents_user_id ON documents(user_id);
CREATE INDEX ix_documents_status ON documents(status);
CREATE INDEX ix_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX ix_document_chunks_content_tsv ON document_chunks USING gin(content_tsv);
```

**Note:** Embeddings (384-dim vectors) stored in Qdrant collection `chunks`, not PostgreSQL. Qdrant indexed with IVFFlat for cosine similarity.

### External Dependencies (PyPI)

**Framework & Core:**
- fastapi 0.111.0
- uvicorn 0.30.0 (ASGI server)
- sqlalchemy 2.0.30 (async ORM)
- asyncpg 0.29.0 (async PostgreSQL)
- pydantic 2.7.0 (validation)
- alembic 1.13.0 (migrations)

**Embeddings & LLM:**
- sentence-transformers 3.0.0 (all-MiniLM-L6-v2, 384-dim)
- tiktoken 0.7.0 (token counting, cl100k_base)
- torch 2.3.0 (transformer dependency)
- qdrant-client (vector DB client, async)
- httpx 0.27.0 (async HTTP to Ollama + reranker)

**Parsing:**
- pypdf 4.2.0 (PDF → text)
- python-docx 1.1.0 (DOCX → text)

**Auth:**
- python-jose 3.3.0 + cryptography (JWT)
- passlib 1.7.4 + bcrypt (password hashing)

**Utilities:**
- python-multipart 0.0.9 (multipart/form-data)
- loguru 0.7.2 (logging)

## Frontend (`/frontend`)

**Tech:** React 19.2.4, TypeScript 5.9.3, Vite 5.4.21, Tailwind CSS 4.2.2, Axios 1.14.0

### Folder Structure

| Folder | Files | Purpose |
|--------|-------|---------|
| **api** | 4 | API client layer (auth, documents, RAG, HTTP client setup) |
| **components** | 10 | Reusable UI components (layout, auth guards, chat, documents, forms) |
| **pages** | 4 | Route pages (login, register, chat, documents) |
| **hooks** | 2 | Custom React hooks (useAuth, useSSE for streaming) |
| **contexts** | 1 | Auth context for JWT token management |
| **types** | 1 | TypeScript interfaces (User, Document, ChatMessage, etc.) |
| **lib** | 1 | Utility functions (className, etc.) |
| **assets** | 2 | Images (hero, icons) |

### Key Components

| Component | Lines | Purpose |
|-----------|-------|---------|
| `auth-context.tsx` | ~80 | JWT token storage, user state, logout |
| `use-sse.ts` | ~40 | EventSource streaming management (delta, sources, done) |
| `chat-page.tsx` | ~120 | Main RAG interface, message display, input handling |
| `documents-page.tsx` | ~100 | Upload, list, delete documents, status polling |
| `upload-zone.tsx` | ~60 | Drag-drop file upload |
| `chat-input.tsx` | ~50 | Textarea with auto-resize, Enter-to-send |
| `chat-message.tsx` | ~40 | Message bubble (user vs assistant roles) |
| `source-card.tsx` | ~50 | Citation card showing source document |
| `layout.tsx` | ~80 | Sidebar navigation, mobile toggle, header |

### API Integration

**API Client Setup:**
- Axios instance with baseURL from `VITE_API_URL` env var (default `http://localhost:8000`)
- Request interceptor injects `Authorization: Bearer {token}` from localStorage
- Response interceptor catches 401, clears token, redirects to `/login`

**API Endpoints Called:**
- `POST /auth/register` → `register()`
- `POST /auth/login` → `login()`
- `POST /documents/upload` → `uploadDocument()`
- `GET /documents` → `listDocuments()`
- `DELETE /documents/{id}` → `deleteDocument()`
- `POST /rag/query` → `query()` (full response)
- `GET /rag/query-stream?question=...&top_k=...` → EventSource (SSE)

### Routing

**React Router v7:**
```
/ (layout)
  ├── /login (public)
  ├── /register (public)
  ├── /chat (protected)
  ├── /documents (protected)
  └── * (redirect to /chat)
```

### Styling

- **Tailwind CSS 4.2.2** — all styling via utility classes
- **Custom theme** — Inter font, indigo primary, JetBrains Mono monospace
- **Dark mode** — configured but not enabled in v0.1.0
- **Responsive** — mobile-first breakpoints (sm, md, lg)
- **Glass morphism** — gradient blobs in background via custom CSS

### State Management

- **Auth state** → React Context + localStorage (token)
- **Component state** → useState for UI state
- **HTTP data** → fetch on mount, handle loading/error/empty states
- **No Redux/Zustand** — too heavy for this scale

## Infrastructure

### Docker Compose Services (6 Total)

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **db** | pgvector/pgvector:pg16 | 5432 | PostgreSQL + FTS + vector extension |
| **pgadmin** | dpage/pgadmin4:latest | 5050 | DB admin UI |
| **qdrant** | qdrant/qdrant:latest | 6333/6334 | Vector database (chunks collection, IVFFlat index) |
| **ollama** | ollama/ollama:latest | 11434 | LLM inference (Qwen3 8B) |
| **backend** | custom (Python 3.11) | 8000 | FastAPI + SQLAlchemy async + Qdrant client |
| **frontend** | custom (Nginx) | 3000 | React SPA + reverse proxy to backend |

### Build Artifacts

- **Backend Dockerfile:** Python 3.11-slim + Poetry + uvicorn
- **Frontend Dockerfile:** Multi-stage (Node 20 build → nginx:alpine serve)
- **Nginx config:** SPA fallback, `/api/*` → backend:8000 with path rewrite

## Test Coverage

**Current Status:** Minimal

| Component | Status | Details |
|-----------|--------|---------|
| Health check | ✓ Done | `test_health.py` — basic endpoint test |
| Auth | ✗ Gap | Register, login, JWT token validation |
| Documents | ✗ Gap | Upload, parse, chunk, embed pipelines |
| RAG | ✗ Gap | Retrieval, generation, streaming |
| Frontend | ✗ Gap | No tests yet; target Phase 2 |

**Target (Phase 2):** ≥80% coverage for business logic

## Performance Characteristics

| Operation | Target | Notes |
|-----------|--------|-------|
| Vector search (pgvector cosine) | <500ms | IVFFlat index with lists=100 |
| Embedding (single chunk) | <100ms | sentence-transformers batch inference |
| PDF parsing | <5s per 10MB | pypdf is synchronous in background task |
| LLM generation | 5-30s | Ollama on CPU (faster with GPU) |
| Full RAG query (excl. LLM) | <2s | embedding + retrieval + context assembly |

## Known Limitations & Gaps

1. **No background job queue** — uses BackgroundTasks (not persistent); consider Celery/RQ Phase 3
2. **No rate limiting** — add per-user quotas Phase 2
3. **No refresh tokens** — JWT 24h only; Phase 2 candidate
4. **No client `/auth/me` endpoint** — frontend decodes JWT naively; Phase 2
5. **Minimal test coverage** — only health check; target ≥80% Phase 2
6. **OOS refusal accuracy 30%** — REFUSAL_PATTERNS regex too narrow (not model bug); Phase 2
7. **Ollama CPU bottleneck** — ~3 min/query CPU-only; use GPU or qwen3:3b for iteration
8. **No document versioning** — upload overwrites; archive old Phase 3
9. **No observability** — no metrics, logging, or distributed tracing
10. **SSE token in query param** — visible in logs; use WebSocket Phase 2+
11. **No caching** — vector search + embedding results uncached; Phase 3 candidate
12. **pgvector column still present** — unused (embeddings fully migrated to Qdrant); migration 003 dropped it
13. **Background task failures** — no persistent job queue, no retry mechanism
14. **HTTPS not enforced** — no TLS in Docker compose; use reverse proxy production

## Dependencies Graph

```
FastAPI (main.py)
  ├── Auth module
  │   ├── SQLAlchemy User model
  │   ├── python-jose (JWT)
  │   └── passlib/bcrypt
  ├── Documents module
  │   ├── SQLAlchemy Document/DocumentChunk models
  │   ├── pypdf, python-docx (parsers)
  │   ├── tiktoken (chunking)
  │   ├── Embeddings service
  │   │   └── sentence-transformers
  │   └── BackgroundTasks
  ├── RAG module
  │   ├── pgvector (retrieval)
  │   ├── Ollama (httpx async call)
  │   └── EventSource (SSE streaming)
  └── Database
      ├── SQLAlchemy async
      └── asyncpg

React App
  ├── React Router
  ├── Axios (API client)
  ├── Auth Context
  ├── EventSource (useSSE hook)
  └── Tailwind CSS
```

## Deployment Graph

```
Docker Host
  ├── PostgreSQL 16 container (pgdata volume)
  ├── Ollama container (models volume)
  ├── Backend container (FastAPI, uploads volume)
  └── Frontend container (Nginx, SPA)
```
