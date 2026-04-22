# Project Overview & PDR - RAG Internal Knowledge

**Version:** 0.1.0 | **Last Updated:** 2026-04-21

## Product Definition

**RAG Internal Knowledge** is a self-hosted retrieval-augmented generation system designed to enable teams to upload internal documents and query them using natural language. The system automatically processes documents (PDF, DOCX, TXT, MD), generates vector embeddings, and provides intelligent retrieval with source citations.

### Product Vision

Eliminate time spent searching for information across fragmented document repositories by providing a single, natural-language interface to internal knowledge.

## Problem Statement

Teams struggle with:
- Information scattered across multiple file systems and repositories
- Time spent manually searching and cross-referencing documents
- Difficulty assembling comprehensive answers from multiple sources
- Need for a solution that doesn't rely on external APIs or services

## Target Users

- Internal employees needing quick access to knowledge base
- Team leads assembling information across documents
- HR/Admin managing company knowledge base
- Development teams referencing standards and policies

## Core Features

1. **Multi-format Document Management** — Upload and manage PDF, DOCX, TXT, MD files
2. **Automatic Processing Pipeline** — Parse, chunk, embed, and index documents
3. **Natural Language RAG Query** — Ask questions, receive answers with source citations
4. **Streaming Responses** — Real-time answer generation via Server-Sent Events
5. **Per-user Document Isolation** — Each user manages and queries only their documents
6. **Self-hosted Deployment** — No external API dependencies, full data control

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Vector Database** | PostgreSQL + pgvector | Zero additional cost, ACID guarantees, sub-100ms queries, equivalent performance to specialized DBs |
| **Embedding Model** | sentence-transformers all-MiniLM-L6-v2 (384-dim) | Free, fast, excellent quality for corporate documents, L2-normalized vectors, cosine distance search |
| **Chunking Strategy** | Recursive split, 512 tokens, 50-token overlap | Balances context preservation with query precision per recent RAG benchmarks |
| **LLM** | Ollama (self-hosted) + Qwen3 8B | No API costs, local inference, streaming support, configurable model selection |
| **Authentication** | JWT HS256, 24h expiry, bcrypt passwords | Stateless, simple, suitable for internal tools |
| **Database** | PostgreSQL 16 + async SQLAlchemy | Proven, async support for FastAPI, pgvector extension for vectors |
| **Frontend Framework** | React 18 + TypeScript + Vite | Fast development, type safety, excellent ecosystem |

## Functional Requirements

- Users register with email and password
- Users upload documents up to 50MB in supported formats
- System automatically parses and chunks uploaded documents
- System generates embeddings for all chunks
- Users query RAG engine with natural language questions (1-2000 characters)
- System returns top-k relevant chunks (configurable, default 5)
- System generates answers using local LLM with source citations
- Users can see document processing status (pending → processing → completed/failed)
- Users can delete documents (removes document and all associated chunks)
- Users can only access their own documents

## Non-Functional Requirements

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **Response Time** | < 5 seconds for retrieval (excluding LLM generation) | Acceptable for internal use, embedding + vector search should be fast |
| **Concurrent Users** | Support 50+ simultaneous users | Typical internal team size, single-tenant-per-user scoping |
| **Document Size** | Support up to 50MB per file | Covers PDFs, DOCX, large corporate docs |
| **Deployment** | Containerized, self-hosted only | Data privacy, no external dependencies |
| **Availability** | 99% uptime during business hours | Internal tool, not 24/7 critical |
| **Security** | JWT auth, bcrypt hashing, user isolation, HTTPS in production | Standard security for internal tools |
| **Scalability** | Single machine with 16GB+ RAM | Designed for small to medium teams, not multi-tenant SaaS |

## Out of Scope (Phase 1)

- Multi-tenant organization support
- SAML/LDAP/OAuth integration
- Document versioning and history
- Full-text search
- Real-time collaboration
- Document annotations and commenting
- Fine-tuned embedding models
- Advanced caching strategies
- Rate limiting and quota management
- Refresh tokens
- Web socket updates for document status
- Document-level access control
- Backup and disaster recovery

## Success Metrics

1. **Adoption** — ≥80% of target team members upload at least one document within first month
2. **Query Accuracy** — ≥70% of answers are relevant to the question (user-rated)
3. **System Reliability** — 99% of queries complete within 60 seconds
4. **Document Coverage** — Average 95% of relevant chunks retrieved for domain-specific queries
5. **Performance** — Average vector search time < 500ms for 100k+ chunks

## Constraints

- No external API calls (fully self-hosted)
- Must run on commodity hardware (no specialized equipment required)
- Database limited to PostgreSQL 16+
- LLM must be open-source and runnable via Ollama
- Frontend uses React, no Vue or Svelte
- All code must be Python (backend) or TypeScript (frontend)

## Dependencies

### External Services
- HuggingFace (downloads embedding model on first startup)

### Internal Dependencies
- PostgreSQL 16 with pgvector extension
- Ollama (LLM inference)
- Docker (recommended deployment)

## Timeline & Phases

- **Phase 1 (Current):** MVP with basic auth, document upload, RAG query, streaming responses
- **Phase 2:** Hardening (test coverage, rate limiting, refresh tokens, `/auth/me` endpoint)
- **Phase 3:** Scale (background job queue, object storage, observability metrics)
- **Phase 4:** UX Polish (markdown rendering, WebSocket updates, retry logic, skeletons)
