from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.documents.models import Document, DocumentChunk


@dataclass
class ChunkResult:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    chunk_index: int
    content: str
    similarity_score: float


async def retrieve(
    db: AsyncSession,
    query_embedding: list[float],
    top_k: int = 5,
    user_id: uuid.UUID | None = None,
) -> list[ChunkResult]:
    query = (
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.content,
            DocumentChunk.chunk_index,
            Document.filename,
            (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label("similarity"),
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.embedding.isnot(None))
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )

    if user_id is not None:
        query = query.where(Document.user_id == user_id)

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        ChunkResult(
            chunk_id=row.id,
            document_id=row.document_id,
            filename=row.filename,
            chunk_index=row.chunk_index,
            content=row.content,
            similarity_score=float(row.similarity),
        )
        for row in rows
    ]
