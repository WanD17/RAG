from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession

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

    results: list[ChunkResult] = []
    for h in hits:
        p = h["payload"]
        results.append(
            ChunkResult(
                chunk_id=uuid.UUID(str(h["id"])),
                document_id=uuid.UUID(p["document_id"]),
                filename=p["filename"],
                chunk_index=int(p["chunk_index"]),
                content=p["content"],
                similarity_score=float(h["score"]),
            )
        )
    return results


_SPARSE_SQL = text(
    """
    SELECT
        dc.id AS id,
        dc.document_id AS document_id,
        dc.content AS content,
        dc.chunk_index AS chunk_index,
        d.filename AS filename,
        ts_rank_cd(dc.content_tsv, q.query) AS rank
    FROM document_chunks dc
    JOIN documents d ON d.id = dc.document_id
    CROSS JOIN plainto_tsquery('english', :query_text) AS q(query)
    WHERE dc.content_tsv @@ q.query
      AND (:user_id IS NULL OR d.user_id = :user_id)
    ORDER BY rank DESC
    LIMIT :top_k
    """
).bindparams(bindparam("user_id", type_=PG_UUID(as_uuid=True)))


async def retrieve_sparse(
    db: AsyncSession,
    query_text: str,
    top_k: int = 20,
    user_id: uuid.UUID | None = None,
) -> list[ChunkResult]:
    """Sparse retrieval via Postgres FTS (ts_rank_cd over GIN index on content_tsv)."""
    result = await db.execute(
        _SPARSE_SQL,
        {"query_text": query_text, "user_id": user_id, "top_k": top_k},
    )
    rows = result.fetchall()

    return [
        ChunkResult(
            chunk_id=row.id,
            document_id=row.document_id,
            filename=row.filename,
            chunk_index=row.chunk_index,
            content=row.content,
            similarity_score=float(row.rank),
        )
        for row in rows
    ]
