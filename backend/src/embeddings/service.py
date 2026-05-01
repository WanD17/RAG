from __future__ import annotations

from loguru import logger
from sentence_transformers import SentenceTransformer

from src.config import settings


class EmbeddingService:
    _instance: EmbeddingService | None = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> EmbeddingService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self) -> None:
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self.load()
        return self._model

    def embed_text(self, text: str) -> list[float]:
        # BGE asymmetric: query-side prefix improves retrieval accuracy
        prefixed = f"Represent this sentence for searching relevant passages: {text}"
        embedding = self.model.encode(prefixed, normalize_embeddings=True)
        return embedding.tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # Passage-side: no prefix for ingestion
        embeddings = self.model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [e.tolist() for e in embeddings]


embedding_service = EmbeddingService()
