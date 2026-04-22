# Project Roadmap

**Last Updated:** 2026-04-21

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
- User registration & JWT authentication
- Multi-format document upload (PDF, DOCX, TXT, MD)
- Automatic document processing pipeline (parse → chunk → embed → store)
- RAG query engine with pgvector retrieval
- Streaming responses via Server-Sent Events (SSE)
- Source citations for all answers
- Per-user document isolation
- Responsive React UI with Tailwind CSS
- PostgreSQL + pgvector vector storage
- Ollama self-hosted LLM integration

### Known Limitations
- Minimal test coverage (only health check)
- No rate limiting or quotas
- No refresh tokens (24h JWT expiry only)
- No `/auth/me` endpoint (frontend decodes JWT naively)
- No document versioning
- SSE token in query parameter (security concern)
- Synchronous-style document processing (BackgroundTasks, no queue)
- No caching

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
