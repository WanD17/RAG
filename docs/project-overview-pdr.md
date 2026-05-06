# Project Overview & PDR - RAG Internal Knowledge

**Version:** 0.1.1 | **Last Updated:** 2026-05-06

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

1. **Multi-format Document Management** — Upload and manage PDF, DOCX, TXT, MD files with pdfplumber parser + table extraction
2. **Intelligent Document Processing** — Section-aware chunking (512 tokens, 50 overlap, breadcrumb prefixes), automated Unicode/ligature normalization, header/footer dedup
3. **Hybrid Retrieval System** — Dense vector search (Qdrant 768-dim HNSW) + sparse BM25 (fastembed) with RRF fusion (alpha=0.7, k=60)
4. **Cross-encoder Reranking** — BAAI/bge-reranker-base re-ranking (top-20 → top-k, sigmoid threshold=0.6) for improved relevance precision
5. **Asymmetric Embeddings** — BAAI/bge-base-en-v1.5 (768-dim) with query-side prefix, passages without prefix for maximum semantic matching
6. **Natural Language RAG Query** — Ask questions with conversation memory (sliding window 6 turns), automatic query rewriting for follow-ups
7. **Streaming Responses** — Real-time answer generation via Server-Sent Events (SSE) with 6-section anti-hallucination system prompt and [Source N] citations
8. **Per-user Document Isolation** — Each user manages and queries only their documents with enforced retriever-layer filtering
9. **Self-hosted Deployment** — No external API dependencies, full data control, Docker Compose orchestration
10. **Evaluation Framework** — Golden set of 60 Q&A pairs + 9-conversation multi-turn set for accuracy benchmarking with LLM judge

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Retrieval Strategy** | Hybrid (Qdrant dense + Postgres FTS) + RRF fusion + reranking | Combine strengths: dense for semantic, sparse for exact match, RRF balances both, reranking improves quality |
| **Vector Database** | Qdrant (dedicated vector DB) + PostgreSQL FTS | Qdrant: optimized cosine similarity, Postgres FTS: full-text on content_tsv (GIN index), both indexed |
| **Reranker Model** | BAAI/bge-reranker-base | Lightweight, high-quality re-ranking, improves top-k precision without large latency overhead |
| **Embedding Model** | BAAI/bge-base-en-v1.5 (768-dim) | Higher quality semantic matching (vs. 384-dim MiniLM), asymmetric encoding (query prefix), batch_size=32 |
| **Chunking Strategy** | Recursive split, 512 tokens, 50-token overlap (tiktoken cl100k_base) | Balances context preservation with query precision per recent RAG benchmarks |
| **Fusion Algorithm** | Reciprocal Rank Fusion (RRF) with alpha=0.7, k=60 | Mathematically sound, avoids score normalization issues, configurable weighting |
| **LLM** | Ollama (self-hosted) + Qwen3 8B | No API costs, local inference, streaming support, configurable model selection, temperature=0 (deterministic), presence_penalty=0.2 |
| **System Prompt** | Anti-hallucination with grounding, citations, refusal, language mirroring | Improves answer reliability, citation coverage, reduces out-of-scope responses |
| **Authentication** | JWT HS256, 24h expiry, bcrypt passwords | Stateless, simple, suitable for internal tools |
| **Database** | PostgreSQL 16 + async SQLAlchemy | Proven, async support for FastAPI, vector extension, FTS indexes |
| **Frontend Framework** | React 19 + TypeScript + Vite | Fast development, type safety, excellent ecosystem |

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
- Real-time collaboration
- Document annotations and commenting
- Fine-tuned embedding models
- Circuit breaker + retry logic (Phase 3: Production Hardening)
- Rate limiting and quota management (Phase 2)
- Refresh tokens (Phase 2)
- Web socket updates for document status (Phase 2+)
- Document-level access control (Phase 3)
- Backup and disaster recovery (Phase 3)
- Redis caching (Phase 3)
- Distributed tracing and metrics (Phase 3)

## Success Metrics (Post-Sprint 2 Achieved)

1. **Query Accuracy** — doc_hit@5=100%, MRR=0.990, keyword_recall=0.900 (exceeded targets)
2. **Citation Coverage** — 100% of answers include valid source citations
3. **Out-of-Scope Refusal** — 100% correct refusal on adversarial queries; zero false_refusal (fixed in Sprint 1)
4. **System Reliability** — p95=108s (excluding LLM generation); p95 for retrieval+rerank <1s
5. **Multi-turn Conversations** — 100% coherence, citation consistency ✓, correct refusal on OOS follow-ups
6. **Parser Quality** — pdfplumber table extraction +40% vs. pypdf, header removal 99% effective
7. **Embedding Quality** — BAAI/bge-base-en-v1.5 (768-dim) asymmetric encoding outperforms all-MiniLM-L6-v2 by 0.042 MRR
8. **Adoption** — Pilot team using system with no critical bugs after 1 week

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
