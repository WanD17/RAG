from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass

from src.rag.qdrant import qdrant_service


@dataclass
class ChunkResult:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    chunk_index: int
    content: str
    similarity_score: float


async def retrieve(
    query_embedding: list[float],
    top_k: int,
    user_id: uuid.UUID,
) -> list[ChunkResult]:
    """Dense retrieval via Qdrant HNSW + payload filter by user_id."""
    hits = await qdrant_service.search(query_embedding, user_id, top_k)

    return [
        ChunkResult(
            chunk_id=uuid.UUID(str(h["id"])),
            document_id=uuid.UUID(h["payload"]["document_id"]),
            filename=h["payload"]["filename"],
            chunk_index=int(h["payload"]["chunk_index"]),
            content=h["payload"]["content"],
            similarity_score=float(h["score"]),
        )
        for h in hits
    ]


async def retrieve_bm25(
    query_text: str,
    top_k: int,
    user_id: uuid.UUID,
) -> list[ChunkResult]:
    """Sparse BM25 retrieval via Qdrant sparse vectors."""
    query_sparse = await asyncio.to_thread(qdrant_service.encode_bm25, [query_text])
    hits = await qdrant_service.search_sparse(query_sparse[0], user_id, top_k)

    return [
        ChunkResult(
            chunk_id=uuid.UUID(str(h["id"])),
            document_id=uuid.UUID(h["payload"]["document_id"]),
            filename=h["payload"]["filename"],
            chunk_index=int(h["payload"]["chunk_index"]),
            content=h["payload"]["content"],
            similarity_score=float(h["score"]),
        )
        for h in hits
    ]
