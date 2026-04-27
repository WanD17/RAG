# RAG Internal Knowledge

Self-hosted retrieval-augmented generation system for internal knowledge. Upload documents (PDF, DOCX, TXT, MD), auto-process with embeddings, query via natural language with source citations. Fully self-hosted with zero external API dependencies.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11 + FastAPI + SQLAlchemy 2.0 async |
| Vector DB | Qdrant (dense embeddings) + PostgreSQL 16 (FTS) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (384 dims) |
| Retrieval | Hybrid search (Qdrant cosine + Postgres FTS), RRF fusion, cross-encoder reranking (BAAI/bge-reranker-base) |
| LLM | Ollama + Qwen3 8B (self-hosted, configurable) |
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS |
| Auth | JWT HS256 (24h expiry, bcrypt) |
| Container | Docker Compose (6 services) |

## Quick Start

### Docker (Recommended)

```bash
# Clone & setup
git clone <repo-url>
cd <project-folder>
cp backend/.env.example backend/.env
# Edit backend/.env: set SECRET_KEY, QDRANT_URL, HYBRID_ENABLED, RERANKER_ENABLED

# Start all services (db, pgadmin, ollama, qdrant, backend, frontend)
docker compose up -d

# Pull LLM model (first time only, ~5GB)
docker compose exec ollama ollama pull qwen3:8b

# Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Qdrant Dashboard: http://localhost:6333/dashboard
# PgAdmin: http://localhost:5050
```

### Local Development

See [docs/deployment-guide.md](./docs/deployment-guide.md) for detailed setup instructions.

## Architecture

```
[React Frontend]  -->  [FastAPI Backend]
    (Port 3000)          (Port 8000)
                             |
           [Document Pipeline]
           - Parse & chunk (tiktoken cl100k_base, 512 tokens, 50 overlap)
           - Embed (sentence-transformers all-MiniLM-L6-v2, 384-dim)
           - Store (Qdrant + Postgres FTS)
                             |
      [RAG Engine - Hybrid Search]
      - Qdrant cosine similarity (dense vectors)
      - Postgres FTS (ts_rank_cd, GIN index)
      - RRF fusion (alpha=0.7, k=60)
      - Cross-encoder reranking (BAAI/bge-reranker-base)
      - Ollama generation (Qwen3 8B, SSE streaming)
                             |
       [Qdrant (Port 6333)]    [PostgreSQL 16 + FTS]
          (Dense vectors)          (Full-text search)
```

## Key Features

- **Hybrid Search** — Combine dense (Qdrant) + sparse (Postgres FTS) retrieval with RRF fusion
- **Cross-encoder Reranking** — Improve answer quality with BAAI/bge-reranker-base
- **Streaming Responses** — Real-time SSE streaming for instant user feedback
- **Full Document Isolation** — Per-user document scoping at retrieval layer
- **Evaluation Framework** — Golden set of 60 Q&A pairs for accuracy benchmarking
- **Anti-hallucination System Prompt** — Grounding, citations, refusal handling, language mirroring

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Register new user |
| POST | /auth/login | Login, get JWT token |
| POST | /documents/upload | Upload document (multipart), trigger async processing |
| GET | /documents | List user's documents |
| GET | /documents/{id} | Document detail + status |
| DELETE | /documents/{id} | Delete document and chunks |
| POST | /rag/query | Query with hybrid search (full response) |
| GET | /rag/query-stream | Query with hybrid search (SSE streaming) |
| GET | /health | Health check |

## Project Structure

```
.
├── docker-compose.yml
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── auth/                # JWT authentication
│   │   ├── documents/           # Upload & processing
│   │   ├── rag/                 # RAG query engine
│   │   ├── embeddings/          # Embedding service
│   │   └── db/                  # Database layer
│   └── tests/                   # Test suite
└── frontend/
    └── src/
        ├── api/                 # API client
        ├── components/          # UI components
        ├── pages/               # Route pages
        ├── hooks/               # Custom hooks
        └── contexts/            # Auth context
```

## Documentation

- [Project Overview & PDR](./docs/project-overview-pdr.md) — Product definition, features, technical decisions
- [System Architecture](./docs/system-architecture.md) — Data flows, DB schema, security model
- [Code Standards](./docs/code-standards.md) — Conventions, testing, error handling
- [Codebase Summary](./docs/codebase-summary.md) — Module inventory, file structure
- [Deployment Guide](./docs/deployment-guide.md) — Docker, local dev, env config, troubleshooting
- [Project Roadmap](./docs/project-roadmap.md) — Development phases and milestones

## Development

```bash
# Backend (with async support)
cd backend && poetry install
poetry run alembic upgrade head
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Tests
cd backend && poetry run pytest --cov=src

# Lint
cd backend && poetry run ruff check src/
cd frontend && npm run lint
```

## Evaluation

```bash
# Run benchmark against golden set
cd backend
poetry run python scripts/run_eval.py --tag v0.1.0

# Compare results
python scripts/compare.py
```

## License

Internal use only.
