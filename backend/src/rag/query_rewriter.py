"""Query rewriter for multi-turn RAG.

Heuristic gating: skip if query is already self-contained.
LLM rewrite: inject last 3 turns of history, ask model to produce
a standalone search query. Fallback to original on any error.

Only the retrieval_query is rewritten. The original query is passed
to the LLM for answer generation and stored in conversation history.
"""
import re

import httpx
from loguru import logger

from src.config import settings

_PRONOUN_RE = re.compile(
    r"\b(it|its|this|these|they|them|their|that|those|he|she|his|her)\b"
    r"|\b(nó|cái đó|cái này|đó|này|họ|chúng)\b",
    re.IGNORECASE,
)
_ELLIPSIS_STARTERS = re.compile(
    r"^(and|but|or|also|what about|how about|còn|vậy|thế còn|còn về|và|nhưng)\b",
    re.IGNORECASE,
)

_REWRITE_SYSTEM = (
    "You are a query rewriter for a document retrieval system. "
    "Given conversation history and a follow-up question, rewrite the follow-up "
    "into a fully self-contained search query that can be understood without the history. "
    "Output ONLY the rewritten query — no explanation, no quotes, no prefix."
)


def _needs_rewrite(query: str, history: list[dict]) -> bool:
    """Return True if the query likely requires context to be understood."""
    if not history:
        return False
    words = query.split()
    if len(words) >= 8 and not _PRONOUN_RE.search(query) and not _ELLIPSIS_STARTERS.search(query.strip()):
        return False
    return True


def _build_history_snippet(history: list[dict]) -> str:
    """Format last 3 turns (6 messages) into compact text."""
    recent = history[-6:]
    lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content'][:300]}")
    return "\n".join(lines)


async def rewrite_query(query: str, history: list[dict]) -> str:
    """Return a standalone retrieval query. Falls back to original on any error."""
    if not settings.REWRITER_ENABLED:
        return query
    if not _needs_rewrite(query, history):
        logger.debug("Query rewriter: skipped (self-contained)")
        return query

    history_text = _build_history_snippet(history)
    user_prompt = (
        f"Conversation history:\n{history_text}\n\n"
        f"Follow-up question: {query}\n\n"
        "Rewritten standalone search query:"
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": _REWRITE_SYSTEM},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0,
                        "num_predict": 120,
                        "num_ctx": 2048,
                    },
                },
            )
        resp.raise_for_status()
        rewritten = resp.json()["message"]["content"].strip()

        # Sanitize: strip surrounding quotes, collapse whitespace
        rewritten = re.sub(r'^["\']|["\']$', "", rewritten).strip()
        rewritten = " ".join(rewritten.split())

        if not rewritten or len(rewritten) > 500:
            logger.warning("Query rewriter returned invalid output; using original")
            return query

        logger.debug(f"Query rewriter: '{query}' -> '{rewritten}'")
        return rewritten

    except Exception as exc:
        logger.warning(f"Query rewriter failed ({exc}); using original query")
        return query
