from __future__ import annotations

import math

from loguru import logger
from sentence_transformers import CrossEncoder

from src.config import settings
from src.rag.retriever import ChunkResult


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


class RerankerService:
    _instance: RerankerService | None = None
    _model: CrossEncoder | None = None

    def __new__(cls) -> RerankerService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self) -> None:
        if self._model is None:
            logger.info(f"Loading reranker model: {settings.RERANKER_MODEL}")
            self._model = CrossEncoder(settings.RERANKER_MODEL, max_length=512)
            logger.info("Reranker model loaded successfully")

    @property
    def model(self) -> CrossEncoder:
        if self._model is None:
            self.load()
        return self._model

    def rerank(
        self,
        query: str,
        chunks: list[ChunkResult],
        top_k: int,
    ) -> list[ChunkResult]:
        """Score (query, chunk.content) pairs with cross-encoder, sort desc, return top_k.

        Mutates each chunk's similarity_score to the normalized rerank score (sigmoid of raw logit).
        """
        if not chunks:
            return []

        pairs = [[query, c.content] for c in chunks]
        raw_scores = self.model.predict(pairs, batch_size=32, show_progress_bar=False)

        for chunk, raw in zip(chunks, raw_scores, strict=True):
            chunk.similarity_score = _sigmoid(float(raw))

        chunks.sort(key=lambda c: c.similarity_score, reverse=True)
        top = chunks[:top_k]
        threshold = settings.RERANKER_SCORE_THRESHOLD
        filtered = [c for c in top if c.similarity_score >= threshold]
        # keep at least 1 chunk even if all below threshold
        return filtered if filtered else top[:1]


reranker_service = RerankerService()
