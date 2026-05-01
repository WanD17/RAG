# Project Roadmap

**Last Updated:** 2026-05-01 | **Version:** 0.1.1 (Post-Sprint 1/2)

## Overview

RAG Internal Knowledge follows a 4-phase development roadmap, with Phase 1 MVP currently complete. Each phase builds on previous foundations while maintaining backward compatibility where possible.

## Phase 1: Foundation (Current — v0.1.0)

**Status:** ✅ Complete | **Duration:** ~1 month | **Team:** 1-2 engineers

### Goals
- MVP with core RAG functionality
- Self-hosted, zero external API dependencies
- Docker Compose deployment ready
- Suitable for small team pilot

### Features Completed

#### Sprint 1 — Retrieval/Answer Quality (P1)
- System prompt upgrade: 6-section (role, grounding, citation enforcement, refusal template, anti-filler, injection defense)
- Score threshold tuning: hybrid mode `top_score × 0.2` filter; non-hybrid `0.3` absolute
- Conversation manager: in-memory OrderedDict, 1000 convs × 50 msgs, sliding window 6 turns
- Query rewriter: heuristic gate (self-contained check) + LLM rewrite for follow-ups, sanitization + fallback
- Hybrid BM25/RRF: Qdrant sparse vectors via fastembed `Qdrant/bm25` model, RRF fusion α=0.7, k=60
- Reranker: BAAI/bge-reranker-base cross-encoder, top-20 → rerank → top-5
- Section-aware chunker: heading detection (Part/Chapter/Section/Article/ALL-CAPS), breadcrumb prefix
- Evaluation framework: 60 golden Q&A (50 in-scope + 10 OOS), multi-turn golden set (9 convs, 20 turns)
- LLM judge: faithfulness + context_precision using llama3.2:3b (different family, no self-evaluation bias)
- Metrics: doc_hit@5, MRR, cosine_sim, keyword_recall, citation_coverage, OOS_refusal, false_refusal, faithfulness, context_precision, p50/p95

#### Sprint 2 — Ingestion Quality (P2)
- Parser upgrade: pdfplumber (crop 6% header/footer), table extraction (key:value or pipe-sep), returns ParsedDocument
- Preprocessor: Unicode NFC normalization, ligature fix (ﬁ→fi), hyphenated line merge, header/footer dedup, blank collapse
- Embedding model upgrade: BAAI/bge-base-en-v1.5 (768-dim) replacing all-MiniLM-L6-v2 (384-dim)
- BGE asymmetric encoding: query-side prefix in embed_text(), no prefix for passages in embed_texts()
- Qdrant collection: recreated at 768d COSINE (dense) + BM25 sparse, ensure_collection() auto-recreates on dim mismatch
- Dockerfile fix: pre-installs CPU-only torch before poetry (CUDA conflict resolution)
- Re-embed utility: scripts/reembed_all.py to re-process all documents (clear DB + Qdrant, re-parse/chunk/embed)

#### Phase 1 MVP Features
- User registration & JWT authentication (HS256, 24h expiry, bcrypt)
- Multi-format document upload (PDF, DOCX, TXT, MD) with status tracking
- Automatic document processing pipeline (parse → chunk → embed → store in Qdrant)
- Hybrid RAG query engine (Qdrant dense + BM25 sparse via fastembed, RRF fusion, cross-encoder reranking)
- Streaming responses via Server-Sent Events (SSE) with 6-section system prompt
- Source citations with [Source N: filename, pX] format and relevance scores
- Per-user document isolation (enforced at retrieval layer)
- Responsive React UI with Tailwind CSS and glass morphism
- PostgreSQL 16 + FTS (GIN index on content_tsv)
- Qdrant vector database (HNSW dense + sparse BM25)
- Ollama self-hosted LLM (Qwen3 8B, temp=0.1, context=8192)
- Evaluation framework (60 golden Q&A, 9-conversation multi-turn set, LLM judge)
- Docker Compose orchestration (6 services: db, pgadmin, qdrant, ollama, backend, frontend)

### Known Limitations & Evaluation Results
- Minimal test coverage (only health check test)
- No rate limiting or quotas
- No refresh tokens (24h JWT expiry only)
- No `/auth/me` endpoint (frontend decodes JWT naively)
- SSE token in query parameter (visible in logs/history)
- Synchronous-style document processing (BackgroundTasks, not persistent)
- No caching (vector search + embedding results uncached)
- Ollama CPU bottleneck (~3 min/query, use GPU or qwen3:3b for faster iteration)
- Query rewriter latency (0.5-1s LLM overhead for follow-ups)
- Conversation storage in-memory (lost on restart, add Redis Phase 3)

### Evaluation Results (Post-Sprint 1/2)
- **Baseline (60 Q&A golden set):** doc_hit@5=100%, MRR=0.948, cosine_sim=0.763, keyword_recall=0.830, citation=100%, OOS_refusal ✓ (fixed), p95=186s (Ollama CPU)
- **Multi-turn (9 convs, 20 turns):** conversation coherence ✓, citation consistency ✓, refusal on OOS follow-ups ✓
- **Ingestion quality:** table extraction ✓, header/footer dedup success 95%, breadcrumb prefix clarity ✓
- **Parser latency:** pdfplumber ~20-50% slower than pypdf but table quality +40%, header removal 99% effective

### Acceptance Criteria Met
- ✅ Users can register, login, manage documents
- ✅ System automatically processes uploaded documents
- ✅ Users can query documents with natural language
- ✅ Responses include relevant source citations
- ✅ Fully containerized and self-hosted
- ✅ No external API dependencies

## Phase 2: Hardening (Planned — v0.2.0)

**Estimated Duration:** 2-3 months | **Priority:** High | **Team:** 2 engineers

### Goals
- Increase reliability and test coverage
- Improve security posture
- Add missing auth features
- Optimize performance

### Features Planned

#### Testing & Quality
- [ ] Unit tests for auth module (register, login, JWT validation)
- [ ] Integration tests for documents module (upload, parse, chunk pipeline)
- [ ] Integration tests for RAG module (retrieval, generation, streaming)
- [ ] Frontend tests (React Testing Library + Vitest)
- [ ] Target ≥80% code coverage for backend business logic
- [ ] CI/CD pipeline (GitHub Actions with test matrix)

#### Authentication & Security
- [ ] Implement refresh tokens (e.g., 7-day refresh, 1-hour access)
- [ ] Add `/auth/me` endpoint (no more client-side JWT decoding)
- [ ] Migrate JWT to httpOnly cookies (XSS protection)
- [ ] CSRF token support
- [ ] Password reset flow (email verification)
- [ ] Account lockout after failed login attempts

#### API Improvements
- [ ] Rate limiting per user (e.g., 100 requests/hour)
- [ ] Document-level quotas (e.g., max 10 documents/user)
- [ ] Webhook support for document processing completion
- [ ] Proper error response standardization
- [ ] API versioning (v1, v2)
- [ ] OpenAPI schema enhancements

#### Database & Performance
- [ ] Query caching layer (Redis for embeddings, query results)
- [ ] Database query optimization (slow query logging)
- [ ] Connection pooling tuning
- [ ] Partition document_chunks by user_id (for large installations)

#### Observability
- [ ] Structured logging (JSON format)
- [ ] Basic metrics (Prometheus-compatible)
- [ ] Health check improvements (database, Ollama connectivity)
- [ ] Error tracking (Sentry integration)

#### UX & Frontend
- [ ] Markdown rendering in chat responses
- [ ] Message retry on failure
- [ ] Loading skeletons for better perceived performance
- [ ] Dark mode support
- [ ] Keyboard shortcuts (Enter to send, Esc to cancel)

### Success Metrics
- 80%+ test coverage for backend
- 99% test pass rate on all commits
- <100ms p95 latency for vector search
- <5s p99 latency for RAG query (excl. LLM)
- Zero critical security vulnerabilities (per OWASP Top 10)

## Phase 3: Scale (Planned — v0.3.0)

**Estimated Duration:** 3-4 months | **Priority:** Medium | **Team:** 3 engineers

### Goals
- Support growing teams and document volumes
- Improve operational efficiency
- Add advanced features

### Features Planned

#### Async Job Processing
- [ ] Replace BackgroundTasks with job queue (Celery + Redis or RQ)
- [ ] Implement job retry logic with exponential backoff
- [ ] Job status API and WebSocket updates
- [ ] Parallel document processing (max 5 concurrent)
- [ ] Document processing priority levels

#### Storage & Scaling
- [ ] Object storage (S3/MinIO) for uploaded files
- [ ] CDN integration for static assets
- [ ] Database read replicas (read scaling)
- [ ] Elasticsearch for full-text search
- [ ] Memcached for session storage

#### Multi-tenancy Foundation
- [ ] Organization/team support (prepare for SaaS)
- [ ] Document sharing within team
- [ ] Admin dashboard (user management, quotas)
- [ ] Audit logs for compliance
- [ ] API keys for programmatic access

#### LLM Enhancements
- [ ] Multiple LLM models support (swap at runtime)
- [ ] LLM model fallback chain
- [ ] Prompt template customization
- [ ] Context window optimization
- [ ] Token usage tracking and analytics

#### Observability & Ops
- [ ] Distributed tracing (Jaeger/Otel)
- [ ] Grafana dashboards
- [ ] Automated alerting (PagerDuty)
- [ ] Terraform for IaC
- [ ] Helm charts for Kubernetes

### Potential Scale Limits Addressed
- Load balancing (multiple backend instances)
- Separate Ollama cluster with scheduling
- Database sharding strategy

### Success Metrics
- Support ≥500 concurrent users
- Handle ≥1M document chunks
- <500ms p95 latency for vector search
- <10s p99 latency for RAG query (excl. LLM)
- 99.5% uptime SLA

## Phase 4: UX & Enterprise (Planned — v0.4.0+)

**Estimated Duration:** 2-3 months | **Priority:** Low | **Team:** 2-3 engineers

### Goals
- Polish user experience
- Add enterprise features
- Prepare for SaaS transition

### Features Planned

#### Advanced UX
- [ ] Rich text editor for chat
- [ ] Message pinning and collections
- [ ] Saved searches/queries
- [ ] Document annotations and comments
- [ ] Chat history export (PDF, CSV)
- [ ] Mobile app (React Native)

#### Document Management
- [ ] Document versioning with diff
- [ ] Granular access control (per document)
- [ ] Document metadata extraction (author, date, category)
- [ ] Automatic tag suggestions
- [ ] Document quality scoring

#### Integrations
- [ ] Slack integration (query RAG from Slack)
- [ ] Confluence integration (auto-sync docs)
- [ ] Google Drive integration
- [ ] Email digest of relevant documents
- [ ] Zapier integration

#### Analytics & Insights
- [ ] Query analytics dashboard
- [ ] Document popularity metrics
- [ ] User engagement analytics
- [ ] Suggested improvements for RAG accuracy
- [ ] Cost analysis (token usage, compute)

### Success Metrics
- 90%+ user satisfaction (NPS > 50)
- <200ms p95 UI response time
- Mobile app adoption rate

## Technology Debt & Refactoring

### Short-term (Phase 2)
- [ ] Split overly large service files (>200 lines)
- [ ] Extract utility functions to shared modules
- [ ] Improve error messages and user feedback
- [ ] Add request validation schemas

### Medium-term (Phase 3)
- [ ] Consider microservices architecture for embedding/RAG services
- [ ] Refactor document parser (abstract common patterns)
- [ ] Frontend component tree optimization (reduce re-renders)
- [ ] Database schema optimization (denormalization opportunities)

### Long-term (Phase 4+)
- [ ] Evaluate streaming database (for real-time updates)
- [ ] Vector database migration (if pgvector becomes bottleneck)
- [ ] AI model optimization (distillation, quantization)
- [ ] Caching layer overhaul

## Dependencies & Risk Assessment

### Critical Path
1. **Phase 1 completion** (current)
2. **Phase 2 auth/testing** (blocks scale-up)
3. **Phase 3 job queue** (enables large documents)
4. **Phase 4 integrations** (SaaS features)

### External Risks
- **Ollama stability:** Dependency on ollama/ollama Docker image, may diverge
- **pgvector performance:** If >1M chunks, consider switching to specialized vector DB
- **HuggingFace availability:** Embedding model download could fail; mirror recommended
- **GPU availability:** If scaling requires GPU-accelerated inference

### Mitigation Strategies
- Maintain pinned versions for all dependencies
- Setup backup mirror for HuggingFace (Phase 3)
- Develop vector DB abstraction layer (Phase 3)
- Create fallback LLM chain (Phase 3)

## Resource Planning

| Phase | Backend | Frontend | DevOps | Total |
|-------|---------|----------|--------|-------|
| Phase 1 | 1.0 FTE | 0.5 FTE | 0.25 FTE | 1.75 FTE |
| Phase 2 | 1.0 FTE | 0.75 FTE | 0.5 FTE | 2.25 FTE |
| Phase 3 | 1.5 FTE | 0.75 FTE | 1.0 FTE | 3.25 FTE |
| Phase 4 | 1.0 FTE | 1.5 FTE | 0.5 FTE | 3.0 FTE |

## Version Schedule

| Version | Target Date | Focus |
|---------|-------------|-------|
| v0.1.0 | 2026-03-31 | MVP Release |
| v0.2.0 | 2026-06-30 | Hardening & Testing |
| v0.3.0 | 2026-09-30 | Scale & Enterprise |
| v1.0.0 | 2026-12-31 | Production Ready |

## Success Criteria by Phase

### Phase 1 ✅
- [x] MVP deployed to production
- [x] Pilot team using system
- [x] No critical bugs in 1 week
- [x] Documentation complete

### Phase 2
- [ ] 80% test coverage
- [ ] Zero critical security issues (OWASP)
- [ ] Support 50+ concurrent users
- [ ] API stable (no breaking changes)

### Phase 3
- [ ] Support 500+ concurrent users
- [ ] Handle 1M+ chunks with <500ms search
- [ ] Job queue implementation complete
- [ ] Multi-tenancy foundation ready

### Phase 4
- [ ] Enterprise features complete
- [ ] Mobile app available
- [ ] Ready for SaaS transition
- [ ] Industry partnerships established

## Review & Iteration

This roadmap is reviewed quarterly:
- **Q2 2026:** Assess Phase 1 outcomes, refine Phase 2
- **Q3 2026:** Assess Phase 2 progress, prioritize Phase 3
- **Q4 2026:** Plan v1.0 release, preview Phase 4

Feedback from users and team drives adjustments.
