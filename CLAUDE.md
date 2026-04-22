# RAG Internal Knowledge

## Overview
Internal knowledge RAG system - upload documents (PDF/DOCX/TXT/MD), auto-process with embeddings, query via natural language. Fully self-hosted with Ollama.

## Tech Stack
- Backend: Python 3.11 + FastAPI + SQLAlchemy 2.0 (async)
- Database: PostgreSQL 16 + pgvector (vector similarity search)
- Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
- LLM: Ollama + Qwen3 8B (self-hosted, configurable via LLM_MODEL env)
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS
- Auth: JWT (24h expiry, bcrypt)
- Container: Docker Compose (4 services: db, ollama, backend, frontend)

## Commands
- Backend: `cd backend && poetry run uvicorn src.main:app --reload`
- Frontend: `cd frontend && npm run dev`
- Docker: `docker compose up -d`
- Pull LLM model: `docker compose exec ollama ollama pull qwen3:8b`
- Migrations: `cd backend && poetry run alembic upgrade head`
- Tests: `cd backend && poetry run pytest`
- Lint: `cd backend && poetry run ruff check src/`
- Build frontend: `cd frontend && npm run build`

## Structure
- `/backend/src/` - FastAPI application (auth, documents, rag, embeddings, db modules)
- `/frontend/src/` - React application (api, components, pages, hooks, contexts)
- `/docs/` - Project documentation
- `/plans/` - Implementation plans

## Conventions
- Python: snake_case, async/await, type hints, Pydantic schemas
- TypeScript: kebab-case files, functional components, strict types
- Max 200 lines per code file
- Conventional commits
