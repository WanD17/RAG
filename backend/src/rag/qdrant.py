from __future__ import annotations

import uuid

from fastembed import SparseTextEmbedding
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from src.config import settings


class QdrantService:
    _instance: QdrantService | None = None
    _client: AsyncQdrantClient | None = None
    _bm25: SparseTextEmbedding | None = None

    def __new__(cls) -> QdrantService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(url=settings.QDRANT_URL)
        return self._client

    def load_bm25(self) -> None:
        if self._bm25 is None:
            self._bm25 = SparseTextEmbedding(model_name="Qdrant/bm25")
            logger.info("BM25 encoder (Qdrant/bm25) loaded")

    def encode_bm25(self, texts: list[str]) -> list[SparseVector]:
        if self._bm25 is None:
            self.load_bm25()
        results = list(self._bm25.embed(texts))
        return [
            SparseVector(indices=r.indices.tolist(), values=r.values.tolist())
            for r in results
        ]

    async def ensure_collection(self) -> None:
        exists = await self.client.collection_exists(settings.QDRANT_COLLECTION)
        if exists:
            info = await self.client.get_collection(settings.QDRANT_COLLECTION)
            has_sparse = bool(info.config.params.sparse_vectors)
            if has_sparse:
                logger.debug(
                    f"Qdrant collection '{settings.QDRANT_COLLECTION}' already exists "
                    f"with dense + sparse vectors"
                )
                return
            logger.warning(
                f"Recreating Qdrant collection '{settings.QDRANT_COLLECTION}' "
                f"to add BM25 sparse vectors — existing data will be cleared, re-upload documents"
            )
            await self.client.delete_collection(settings.QDRANT_COLLECTION)

        logger.info(
            f"Creating Qdrant collection '{settings.QDRANT_COLLECTION}' "
            f"(dense={settings.EMBEDDING_DIM}d COSINE + sparse BM25)"
        )
        await self.client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config={
                "dense": VectorParams(size=settings.EMBEDDING_DIM, distance=Distance.COSINE),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(),
            },
        )
        await self.client.create_payload_index(
            collection_name=settings.QDRANT_COLLECTION,
            field_name="user_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        await self.client.create_payload_index(
            collection_name=settings.QDRANT_COLLECTION,
            field_name="document_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )

    async def upsert_chunks(
        self,
        chunk_ids: list[uuid.UUID],
        embeddings: list[list[float]],
        sparse_vectors: list[SparseVector],
        payloads: list[dict],
    ) -> None:
        if not chunk_ids:
            return
        points = [
            PointStruct(
                id=str(cid),
                vector={"dense": emb, "sparse": sv},
                payload=pl,
            )
            for cid, emb, sv, pl in zip(chunk_ids, embeddings, sparse_vectors, payloads, strict=True)
        ]
        await self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points,
            wait=True,
        )

    async def search(
        self,
        query_vector: list[float],
        user_id: uuid.UUID,
        top_k: int,
    ) -> list[dict]:
        result = await self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_vector,
            using="dense",
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
            ),
            limit=top_k,
            with_payload=True,
        )
        return [
            {"id": p.id, "score": p.score, "payload": p.payload or {}}
            for p in result.points
        ]

    async def search_sparse(
        self,
        query_sparse: SparseVector,
        user_id: uuid.UUID,
        top_k: int,
    ) -> list[dict]:
        result = await self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_sparse,
            using="sparse",
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
            ),
            limit=top_k,
            with_payload=True,
        )
        return [
            {"id": p.id, "score": p.score, "payload": p.payload or {}}
            for p in result.points
        ]

    async def delete_by_document(self, document_id: uuid.UUID) -> None:
        await self.client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))
                ]
            ),
            wait=True,
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None


qdrant_service = QdrantService()
