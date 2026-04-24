from __future__ import annotations

import uuid

from src.rag.retriever import ChunkResult


def reciprocal_rank_fusion(
    dense: list[ChunkResult],
    sparse: list[ChunkResult],
    top_n: int,
    alpha: float = 0.7,
    k: int = 60,
) -> list[ChunkResult]:
    """Fuse dense and sparse rankings via Reciprocal Rank Fusion.

    Score = alpha / (k + rank_dense) + (1 - alpha) / (k + rank_sparse).
    Rank is 1-based. A chunk missing from one list contributes 0 from that side.
    Returns up to top_n chunks sorted by fused score desc, with similarity_score
    overwritten to the fused RRF score.
    """
    scores: dict[uuid.UUID, float] = {}
    chunks_by_id: dict[uuid.UUID, ChunkResult] = {}

    for rank, chunk in enumerate(dense, start=1):
        scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + alpha / (k + rank)
        chunks_by_id.setdefault(chunk.chunk_id, chunk)

    for rank, chunk in enumerate(sparse, start=1):
        scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + (1 - alpha) / (k + rank)
        chunks_by_id.setdefault(chunk.chunk_id, chunk)

    fused: list[ChunkResult] = []
    for chunk_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        chunk = chunks_by_id[chunk_id]
        chunk.similarity_score = score
        fused.append(chunk)

    return fused[:top_n]
