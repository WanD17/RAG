# Deployment Guide

**Last Updated:** 2026-04-27 | **6 Docker Services:** db, pgadmin, qdrant, ollama, backend, frontend

## Prerequisites

### Minimum Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| Docker | 24.0+ | Container orchestration |
| Docker Compose | 2.0+ | Multi-container coordination |
| Git | 2.0+ | Source control |

### Hardware Recommendations

| Scenario | CPU | RAM | Disk | GPU |
|----------|-----|-----|------|-----|
| **Development (local)** | 4 cores | 8GB | 20GB | Optional |
| **Production (small team)** | 8 cores | 16GB | 30GB | Recommended (8GB+) |
| **Production (larger team)** | 16 cores | 32GB | 50GB | Recommended |

**GPU Note:** Ollama (LLM) runs 10x faster with NVIDIA GPU. CPU-only is viable but slow (5-30s per query).

## Quick Start (Docker)

### 1. Clone & Setup

```bash
git clone <repo-url>
cd <project-folder>

# Create .env from template
cp backend/.env.example backend/.env
```

### 2. Configure Environment

Edit `backend/.env`:

```env
# Database (Docker internal hostname)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/rag_db

# Secrets (change to random value)
SECRET_KEY=<generate-random-string>  # See "Generate SECRET_KEY" section

# Ollama (Docker internal hostname)
OLLAMA_BASE_URL=http://ollama:11434
LLM_MODEL=qwen3:8b

# Qdrant (Docker internal hostname)
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=chunks

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Hybrid Search
HYBRID_ENABLED=true
HYBRID_ALPHA=0.7
HYBRID_RRF_K=60

# Reranking
RERANKER_ENABLED=true
RERANKER_MODEL=BAAI/bge-reranker-base
RETRIEVAL_TOP_N=20

# API
CORS_ORIGINS=["http://localhost:3000"]
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=50
ALLOWED_EXTENSIONS=["pdf","docx","txt","md"]
```

### 3. Start Services

```bash
# Build and start all containers
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f backend
```

### 4. Initialize LLM Model

```bash
# Pull Qwen3 8B (first time only, ~5GB, ~10 minutes)
docker compose exec ollama ollama pull qwen3:8b

# Verify model loaded
docker compose exec ollama ollama list
```

### 5. Access System

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | React SPA (chat, documents) |
| **API Docs** | http://localhost:8000/docs | Swagger interactive docs |
| **Health Check** | http://localhost:8000/health | Backend health status |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Vector DB admin UI |
| **PgAdmin** | http://localhost:5050 | PostgreSQL admin UI (user: admin@admin.com) |

### 6. Stop Services

```bash
# Stop containers
docker compose down

# Stop and remove volumes (WARNING: deletes database)
docker compose down -v
```

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (with pgvector)
- Ollama

### 1. Setup PostgreSQL + pgvector

**Option A: Docker (Recommended)**

```bash
docker run -d \
  --name rag-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=rag_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

**Option B: Native Installation (macOS)**

```bash
brew install postgresql@16 pgvector
brew services start postgresql@16

createdb rag_db
psql rag_db -c "CREATE EXTENSION vector;"
psql rag_db -c "CREATE EXTENSION \"uuid-ossp\";"
```

**Option C: Native Installation (Ubuntu/Debian)**

```bash
sudo apt install postgresql-16 postgresql-16-pgvector
sudo systemctl start postgresql

sudo -u postgres createdb rag_db
sudo -u postgres psql rag_db -c "CREATE EXTENSION vector;"
sudo -u postgres psql rag_db -c "CREATE EXTENSION \"uuid-ossp\";"
```

### 2. Setup Ollama

Visit https://ollama.com and download for your OS.

Start Ollama and pull model:

```bash
# Start server (background)
ollama serve &

# Pull model (terminal 2)
ollama pull qwen3:8b

# Verify
ollama list
```

### 3. Setup Backend

```bash
cd backend

# Install Poetry (if not already installed)
pip install poetry

# Install dependencies
poetry install

# Create .env
cp .env.example .env
```

Edit `backend/.env` for local development:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db
SECRET_KEY=<generate-random-string>
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=qwen3:8b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384
CHUNK_SIZE=512
CHUNK_OVERLAP=50
CORS_ORIGINS=["http://localhost:5173"]
UPLOAD_DIR=./uploads
```

Run migrations:

```bash
poetry run alembic upgrade head
```

Start backend:

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Access at http://localhost:5173.

### 5. Running Tests

```bash
cd backend
poetry run pytest

# With coverage
poetry run pytest --cov=src
```

## Environment Variables Reference

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db` | PostgreSQL async connection string |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | None (required) | JWT signing key; use `secrets.token_urlsafe(32)` |
| `ALGORITHM` | `HS256` | JWT algorithm (do not change) |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `24` | JWT expiration time in hours |

### Ollama LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama inference server URL |
| `LLM_MODEL` | `qwen3:8b` | Model name; must be pulled first |

### Qdrant Vector DB

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_URL` | `http://localhost:6333` | Qdrant API URL |
| `QDRANT_COLLECTION` | `chunks` | Collection name for document embeddings |

### Embeddings

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model from HuggingFace |
| `EMBEDDING_DIM` | `384` | Vector dimensions (must match model) |

### Document Processing

| Variable | Default | Description |
|----------|---------|-------------|
| `CHUNK_SIZE` | `512` | Tokens per chunk (recursive split, tiktoken cl100k_base) |
| `CHUNK_OVERLAP` | `50` | Token overlap between chunks |
| `UPLOAD_DIR` | `./uploads` | Directory for uploaded files |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max file size in MB |
| `ALLOWED_EXTENSIONS` | `["pdf","docx","txt","md"]` | Allowed file formats |

### Hybrid Search & Reranking

| Variable | Default | Description |
|----------|---------|-------------|
| `HYBRID_ENABLED` | `true` | Enable hybrid search (Qdrant + Postgres FTS) |
| `HYBRID_ALPHA` | `0.7` | RRF alpha parameter for score weighting |
| `HYBRID_RRF_K` | `60` | RRF k parameter (top-k from each retriever) |
| `RERANKER_ENABLED` | `true` | Enable cross-encoder reranking |
| `RERANKER_MODEL` | `BAAI/bge-reranker-base` | Reranker model name |
| `RETRIEVAL_TOP_N` | `20` | Top-N candidates before reranking |

### API & CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `["http://localhost:5173"]` | JSON array of allowed origins |

## Ollama Model Selection

### Quick Comparison

| Model | RAM | VRAM | Quality | Speed | Use Case |
|-------|-----|------|---------|-------|----------|
| `qwen3:4b` | 8GB | 4GB | Good | Very Fast | Low-end machines |
| `qwen3:8b` | 16GB | 6GB | Excellent | Good | **Recommended default** |
| `qwen3:14b` | 32GB | 10GB | Best | Slow | High-quality answers |
| `llama3.2:3b` | 8GB | 3GB | Fair | Very Fast | Quick testing |
| `llama3.1:8b` | 16GB | 6GB | Excellent | Good | Alternative to Qwen |
| `mistral:7b` | 16GB | 6GB | Very Good | Good | English-focused |

### Pulling Models

```bash
ollama pull qwen3:8b       # ~5GB
ollama pull llama3.1:8b    # ~4GB
ollama pull mistral:7b     # ~4GB
ollama pull qwen3:14b      # ~9GB
```

### Changing Models

1. Edit `backend/.env`: `LLM_MODEL=llama3.1:8b`
2. Pull model: `ollama pull llama3.1:8b`
3. Restart backend

## Troubleshooting

### Backend won't start: "Connection refused"

**Symptom:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
- Verify PostgreSQL is running: `docker ps | grep postgres` or `pg_isready`
- Check `DATABASE_URL` in `.env`
  - Docker: host should be `db`
  - Local: host should be `localhost`
- Verify extensions: `psql rag_db -c "\dx"` should show `vector` and `uuid-ossp`

### Ollama connection error

**Symptom:** `httpx.ConnectError: Unable to connect to http://localhost:11434`

**Solution:**
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check `OLLAMA_BASE_URL` in `.env`
  - Docker: use `http://ollama:11434`
  - Local: use `http://localhost:11434`

### Model not found

**Symptom:** `AssertionError: Model qwen3:8b not found`

**Solution:**
```bash
ollama list                    # Check pulled models
ollama pull qwen3:8b          # Pull if missing
docker compose logs ollama    # Check Ollama logs
```

### Embedding model takes forever to load

**Symptom:** Backend hangs on startup for 5+ minutes

**Solution:**
- First startup downloads embedding model (~90MB) from HuggingFace
- Use VPN if network is restricted
- Check logs: `docker compose logs -f backend`

### Document upload fails with 422

**Symptom:** `422 Unprocessable Entity`

**Solution:**
- File format must be in `ALLOWED_EXTENSIONS` (pdf, docx, txt, md)
- File size must be ≤ `MAX_UPLOAD_SIZE_MB` (default 50MB)
- File cannot be empty

### Document stuck in "processing"

**Symptom:** Document status never changes from "processing"

**Solution:**
```bash
# Check backend logs
docker compose logs backend | grep -i error

# Possible causes:
# - PDF is corrupted or password-protected
# - File is too large (time limit exceeded)
# - Embedding model failed to load
```

### Frontend 401 loop

**Symptom:** Redirects to login even after login

**Solution:**
- Check browser DevTools → Application → localStorage (look for `token` key)
- Verify `/auth/login` returns token: `curl -X POST http://localhost:8000/auth/login ...`
- Clear localStorage: `localStorage.clear()` in browser console
- Check backend CORS: `CORS_ORIGINS` should include frontend origin

### SSE streaming stops

**Symptom:** Chat response doesn't stream; shows full response at once

**Solution:**
- In Docker: check Nginx config has `proxy_buffering off`
- In local dev: check `vite.config.ts` proxy config
- Browser console: check for 504 Gateway Timeout or 401

### IVFFlat index error

**Symptom:** Migration fails: `pg_config not found` or index creation fails

**Solution:**
```bash
# Option 1: Use exact search initially (slower, no index)
# Let system work without index until ≥1000 chunks exist
# Then create index manually

# Option 2: Drop and recreate index
docker compose exec db psql -U postgres -d rag_db -c \
  "DROP INDEX IF EXISTS ix_document_chunks_embedding;"

# Option 3: Check pgvector installed
docker compose exec db psql -U postgres -d rag_db -c \
  "SELECT extname FROM pg_extension WHERE extname='vector';"
```

### Docker build fails

**Symptom:** `ERROR [backend 3/5] RUN poetry install --only main`

**Solution:**
```bash
# Clear cache and rebuild
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Production Hardening Checklist

- [ ] Rotate `SECRET_KEY` (use `secrets.token_urlsafe(32)`)
- [ ] Set `CORS_ORIGINS` to production domain only (not `localhost`)
- [ ] Enable TLS termination (reverse proxy like Nginx, Caddy)
- [ ] Restrict PostgreSQL access (no public port)
- [ ] Disable Ollama API exposure (run on internal network only)
- [ ] Setup database backups (automated daily)
- [ ] Setup upload file cleanup (age-based deletion)
- [ ] Monitor disk usage (uploads can grow large)
- [ ] Setup log aggregation (ELK, Splunk, etc.)
- [ ] Rate limiting on API endpoints
- [ ] Refresh token implementation (Phase 2)
- [ ] Use httpOnly cookies for JWT (Phase 2)
- [ ] Document disaster recovery procedure

## Monitoring & Logging

### Health Check

```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "0.1.0"}
```

### Container Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f db
docker compose logs -f ollama
docker compose logs -f frontend
```

### Database

```bash
# Connect to database
docker compose exec db psql -U postgres -d rag_db

# Check tables
\dt

# Check vector index
SELECT * FROM pg_indexes WHERE tablename = 'document_chunks';
```

## Backup & Recovery

### Backup Database

```bash
docker compose exec db pg_dump -U postgres rag_db > backup.sql
```

### Restore Database

```bash
docker compose exec -T db psql -U postgres rag_db < backup.sql
```

### Backup Uploads

```bash
tar -czf uploads-backup.tar.gz backend/uploads/
```
