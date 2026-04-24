import asyncio
import uuid

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.embeddings.service import embedding_service
from src.rag import generator, retriever
from src.rag.reranker import reranker_service
from src.rag.schemas import QueryResponse, SourceChunk


async def query(
    db: AsyncSession,
    query_text: str,
    user_id: uuid.UUID,
    top_k: int = 5,
) -> QueryResponse:
    logger.debug(f"RAG query: user={user_id}, top_k={top_k}")

    query_embedding = embedding_service.embed_text(query_text)

    retrieval_n = max(settings.RETRIEVAL_TOP_N, top_k) if settings.RERANKER_ENABLED else top_k
    candidates = await retriever.retrieve(
        db, query_embedding, top_k=retrieval_n, user_id=user_id
    )

    if not candidates:
        return QueryResponse(
            answer="No relevant documents found in your knowledge base for this query.",
            sources=[],
            query=query_text,
        )

    if settings.RERANKER_ENABLED:
        chunks = await asyncio.to_thread(
            reranker_service.rerank, query_text, candidates, top_k
        )
        logger.debug(f"Reranked {len(candidates)} -> {len(chunks)} chunks")
    else:
        chunks = candidates[:top_k]

    answer = await generator.generate_answer(query_text, chunks)

    sources = [
        SourceChunk(
            document_id=chunk.document_id,
            filename=chunk.filename,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            similarity_score=chunk.similarity_score,
        )
        for chunk in chunks
    ]

    return QueryResponse(answer=answer, sources=sources, query=query_text)
