import uuid

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.embeddings.service import embedding_service
from src.rag import generator, retriever
from src.rag.schemas import QueryResponse, SourceChunk


async def query(
    db: AsyncSession,
    query_text: str,
    user_id: uuid.UUID,
    top_k: int = 5,
) -> QueryResponse:
    logger.debug(f"RAG query: user={user_id}, top_k={top_k}")

    query_embedding = embedding_service.embed_text(query_text)

    chunks = await retriever.retrieve(db, query_embedding, top_k=top_k, user_id=user_id)

    if not chunks:
        return QueryResponse(
            answer="No relevant documents found in your knowledge base for this query.",
            sources=[],
            query=query_text,
        )

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
