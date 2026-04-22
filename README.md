# RAG Internal Knowledge

Hệ thống RAG (Retrieval-Augmented Generation) cho thông tin nội bộ. Upload tài liệu (PDF, DOCX, TXT, MD), tự động xử lý & lưu trữ vector embeddings, trả lời câu hỏi dựa trên nội dung tài liệu. Hoàn toàn self-hosted, không phụ thuộc API bên ngoài.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11, FastAPI 0.111.0, SQLAlchemy 2.0.30 |
| Vector DB | PostgreSQL 16 + pgvector 0.3.0 |
| Embeddings | sentence-transformers 3.0 (all-MiniLM-L6-v2, 384 dims) |
| LLM | Ollama + Qwen3 8B (self-hosted, configurable) |
| Frontend | React 19.2.4, TypeScript 5.9.3, Vite 5.4.21, Tailwind CSS 4.2.2 |
| Auth | JWT HS256 (24h expiry, bcrypt hashing) |
| Container | Docker Compose (4 services) |

## Quick Start

### Docker (Recommended)

```bash
# Clone & setup
git clone <repo-url>
cd <project-folder>
cp backend/.env.example backend/.env
# Edit backend/.env: set SECRET_KEY

# Start all services
docker compose up -d

# Pull LLM model (first time only, ~5GB)
docker compose exec ollama ollama pull qwen3:8b

# Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Local Development

See [docs/deployment-guide.md](./docs/deployment-guide.md) for detailed setup instructions.

## Architecture

```
[React Frontend]  -->  [FastAPI Backend]
    (Port 3000)          (Port 8000)
                             |
                [Document Pipeline]
                - Parse & chunk
                - Embed (sentence-transformers)
                - Store (pgvector)
                             |
                    [RAG Engine]
                    - Vector search
                    - Ollama generation
                    - SSE streaming
                             |
             [PostgreSQL 16 + pgvector]
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Register new user |
| POST | /auth/login | Login, get JWT token |
| POST | /documents/upload | Upload document (multipart) |
| GET | /documents | List user's documents |
| GET | /documents/{id} | Document detail |
| DELETE | /documents/{id} | Delete document |
| POST | /rag/query | Query RAG (full response) |
| GET | /rag/query-stream | Query RAG (SSE streaming) |
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
# Backend
cd backend && poetry install && poetry run uvicorn src.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Tests
cd backend && poetry run pytest

# Lint
cd backend && poetry run ruff check src/
```

## License

Internal use only.
