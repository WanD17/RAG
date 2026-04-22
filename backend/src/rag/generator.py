from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx
from loguru import logger

from src.config import settings
from src.rag.retriever import ChunkResult

SYSTEM_PROMPT = (
    "You are an internal knowledge assistant. Answer questions based solely on the provided context. "
    "If the information is not available in the context, clearly state that. "
    "Always cite your sources by referencing the document filename and relevant chunk content."
)


def _build_context(chunks: list[ChunkResult]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[Source {i}: {chunk.filename} (chunk {chunk.chunk_index})]\n{chunk.content}")
    return "\n\n---\n\n".join(parts)


def _build_messages(query: str, context_chunks: list[ChunkResult]) -> list[dict]:
    context = _build_context(context_chunks)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
    ]


async def generate_answer(query: str, context_chunks: list[ChunkResult]) -> str:
    messages = _build_messages(query, context_chunks)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.LLM_MODEL,
                    "messages": messages,
                    "stream": False,
                    "think": False,
                    "options": {"num_predict": 1024, "num_ctx": 8192, "temperature": 0.1},
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
    except httpx.HTTPError as e:
        logger.error(f"Ollama API error: {e}")
        raise


async def generate_answer_stream(
    query: str, context_chunks: list[ChunkResult]
) -> AsyncGenerator[str, None]:
    messages = _build_messages(query, context_chunks)
    import json

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.LLM_MODEL,
                    "messages": messages,
                    "stream": True,
                    "think": False,
                    "options": {
                        "num_predict": 512,
                        "num_ctx": 4096,
                        "temperature": 0.1,
                    },
                },
            ) as response:
                if response.status_code >= 400:
                    body = (await response.aread()).decode("utf-8", errors="replace")
                    logger.error(f"Ollama {response.status_code}: {body}")
                    response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if err := data.get("error"):
                        logger.error(f"Ollama runtime error: {err}")
                        raise RuntimeError(err)
                    if content := data.get("message", {}).get("content", ""):
                        yield content
                    if data.get("done", False):
                        break
    except httpx.HTTPError as e:
        logger.error(f"Ollama HTTP error: {type(e).__name__}: {e}")
        raise
