import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from jose import JWTError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import service as auth_service
from src.auth.models import User
from src.config import settings
from src.dependencies import get_current_user
from src.db.session import get_db
from src.embeddings.service import embedding_service
from src.rag import retriever
from src.rag import generator as gen
from src.rag import service
from src.rag.reranker import reranker_service
from src.rag.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await service.query(db, payload.query, current_user.id, payload.top_k)
    except Exception as e:
        logger.exception("RAG query failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{type(e).__name__}: {e}",
        )


async def _user_from_query_token(token: str, db: AsyncSession) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
    )
    try:
        payload = auth_service.decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    user = await auth_service.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


@router.get("/query-stream")
async def query_knowledge_base_stream(
    question: str = Query(..., min_length=1, max_length=2000),
    token: str = Query(...),
    top_k: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    current_user = await _user_from_query_token(token, db)

    query_embedding = embedding_service.embed_text(question)
    retrieval_n = max(settings.RETRIEVAL_TOP_N, top_k) if settings.RERANKER_ENABLED else top_k
    candidates = await retriever.retrieve(
        db, query_embedding, top_k=retrieval_n, user_id=current_user.id
    )
    if settings.RERANKER_ENABLED and candidates:
        chunks = await asyncio.to_thread(
            reranker_service.rerank, question, candidates, top_k
        )
    else:
        chunks = candidates[:top_k]

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            if not chunks:
                yield f"event: delta\ndata: {json.dumps('No relevant documents found.')}\n\n"
                yield "event: done\ndata: {}\n\n"
                return

            sources = [
                {
                    "document_id": str(c.document_id),
                    "filename": c.filename,
                    "chunk_index": c.chunk_index,
                    "content": c.content,
                    "score": c.similarity_score,
                }
                for c in chunks
            ]
            yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

            async for text in gen.generate_answer_stream(question, chunks):
                yield f"event: delta\ndata: {json.dumps(text)}\n\n"

            yield "event: done\ndata: {}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"event: error\ndata: {json.dumps(str(e))}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
