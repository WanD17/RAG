"""Optional LLM judge for faithfulness + context precision scoring.

Called from run_eval.py when --llm-judge flag is passed.
Uses Ollama local — synchronous, no extra dependencies.

Faithfulness:       does the answer contain ONLY claims supported by the retrieved context?
Context Precision:  of the retrieved chunks, what fraction were actually relevant?

Both return None on failure — eval continues without them.
"""
import re

import httpx

_NUMBER_RE = re.compile(r"\b(1\.0|1|0\.\d{1,3}|0)\b")
_BITS_RE = re.compile(r"[01]")


def _ollama_chat(
    ollama_url: str,
    model: str,
    system: str,
    user: str,
    timeout: int,
    num_predict: int = 16,
) -> str:
    """Single Ollama /api/chat call. Returns stripped response text."""
    resp = httpx.post(
        f"{ollama_url}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "num_predict": num_predict, "num_ctx": 4096},
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


_FAITH_SYSTEM = (
    "You are an evaluation assistant. "
    "You rate how faithful an AI answer is to the retrieved context. "
    "Output ONLY a decimal number between 0.0 and 1.0. No explanation. No units."
)


def judge_faithfulness(
    answer: str,
    sources: list[dict],
    ollama_url: str = "http://localhost:11434",
    model: str = "qwen3:8b",
    timeout: int = 120,
) -> float | None:
    """Score faithfulness of answer vs retrieved context. Returns None on failure."""
    if not answer or not sources:
        return None

    context_parts = [
        "[Source " + str(i + 1) + ": " + s.get("filename", "?") + "]\n" + s.get("content", "")[:600]
        for i, s in enumerate(sources)
    ]
    context = "\n\n---\n\n".join(context_parts)

    user_msg = (
        "CONTEXT (retrieved document excerpts):\n"
        + context
        + "\n\nSYSTEM ANSWER:\n"
        + answer[:1000]
        + "\n\nScoring guide:\n"
        "- 1.0 = Every factual claim in the answer is directly supported by the context\n"
        "- 0.7 = Most claims are supported; one minor point slightly goes beyond the context\n"
        "- 0.5 = About half the claims are supported; noticeable inference or added knowledge\n"
        "- 0.3 = Most claims are not found in the context; significant hallucination\n"
        "- 0.0 = The answer is entirely fabricated or contradicts the context\n\n"
        "Output ONLY a decimal number between 0.0 and 1.0."
    )

    for attempt in range(2):
        try:
            raw = _ollama_chat(ollama_url, model, _FAITH_SYSTEM, user_msg, timeout, num_predict=16)
            m = _NUMBER_RE.search(raw)
            if m:
                return round(min(max(float(m.group(1)), 0.0), 1.0), 3)
            if attempt == 0:
                continue  # retry once
            print(f"    [judge] unexpected output: {raw!r}")
            return None
        except Exception as exc:
            if attempt == 1:
                print(f"    [judge error] faithfulness: {exc}")
            return None
    return None


_PRECISION_SYSTEM = (
    "You are an evaluation assistant. "
    "For each numbered chunk, output 1 if it helps answer the question or 0 if it does not. "
    "Output ONLY the digits separated by commas — nothing else. "
    "Example for 3 chunks: 1,0,1"
)


def judge_context_precision(
    question: str,
    sources: list[dict],
    ollama_url: str = "http://localhost:11434",
    model: str = "llama3.2:3b",
    timeout: int = 120,
) -> float | None:
    """Score context precision: fraction of retrieved chunks that are relevant. Returns None on failure."""
    if not sources:
        return None

    chunks_lines = []
    for i, s in enumerate(sources):
        chunks_lines.append("[Chunk " + str(i + 1) + "]\n" + s.get("content", "")[:400])
    chunks_text = "\n\n".join(chunks_lines)

    user_msg = (
        "Question: "
        + question
        + "\n\nChunks:\n"
        + chunks_text
        + "\n\nFor each chunk output 1 (relevant) or 0 (not relevant), separated by commas."
    )

    for attempt in range(3):
        try:
            raw = _ollama_chat(ollama_url, model, _PRECISION_SYSTEM, user_msg, timeout, num_predict=32)
            bits = _BITS_RE.findall(raw)
            if bits:
                relevant = sum(int(b) for b in bits)
                return round(relevant / len(bits), 3)
            if attempt < 2:
                continue  # retry
            print(f"    [judge] precision unexpected output: {raw!r}")
            return None
        except Exception as exc:
            if attempt == 2:
                print(f"    [judge error] context_precision: {exc}")
            return None
    return None
