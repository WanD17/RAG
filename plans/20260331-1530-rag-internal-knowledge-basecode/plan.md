# RAG Internal Knowledge - Basecode Implementation Plan

**Date:** 2026-03-31
**Status:** In Progress

## Overview

Tạo basecode cho dự án RAG thông tin nội bộ - cho phép upload tài liệu nội bộ (PDF, DOCX, TXT, MD), xử lý & lưu trữ vector embeddings, và trả lời câu hỏi dựa trên nội dung tài liệu bằng Claude API.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11 + FastAPI |
| Vector DB | PostgreSQL 16 + pgvector |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2, 384 dims) |
| LLM | Claude API (Anthropic) |
| Chunking | Recursive 512-token, 50-token overlap |
| Auth | JWT (multi-user) |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Container | Docker + Docker Compose |

## Phases

| # | Phase | Status |
|---|-------|--------|
| 1 | Project structure & config | ⬜ Pending |
| 2 | Backend API (FastAPI) | ⬜ Pending |
| 3 | Document processing pipeline | ⬜ Pending |
| 4 | RAG core engine | ⬜ Pending |
| 5 | Frontend UI | ⬜ Pending |
| 6 | Docker & documentation | ⬜ Pending |

## Architecture

```
[Frontend (React)] --> [FastAPI Backend]
                           |
                    [Document Pipeline]
                    - Upload & parse (PDF/DOCX/TXT/MD)
                    - Chunk (512 tokens, 50 overlap)
                    - Embed (sentence-transformers)
                    - Store (pgvector)
                           |
                    [RAG Engine]
                    - Query embedding
                    - Vector similarity search
                    - Context assembly
                    - Claude API generation
                           |
                    [PostgreSQL + pgvector]
```
