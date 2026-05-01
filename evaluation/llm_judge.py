"""Optional LLM judge for faithfulness + context precision scoring.

Called from run_eval.py when --llm-judge flag is passed.
Uses Ollama local — synchronous, no extra dependencies.

Faithfulness:       does the answer contain ONLY claims supported by the retrieved context?
Context Precision:  of the retrieved chunks, what fraction were actually relevant?

Both return None on failure — eval continues without them.
"""
import re

import httpx

_PROMPT = """\
You are evaluating a RAG system for hallucination.

CONTEXT (retrieved document excerpts):
{context}

SYSTEM ANSWER:
{answer}

Task: Rate how faithful the SYSTEM ANSWER is to the CONTEXT above.

Scoring guide:
- 1.0 = Every factual claim in the answer is directly supported by the context
- 0.7 = Most claims are supported; one minor point slightly goes beyond the context
- 0.5 = About half the claims are supported; noticeable inference or added knowledge
- 0.3 = Most claims are not found in the context; significant hallucination
- 0.0 = The answer is entirely fabricated or contradicts the context

Output ONLY a decimal number between 0.0 and 1.0. No explanation. No units.\
"""

_NUMBER_RE = re.compile(r"\b(1\.0|1|0\.\d{1,3}|0)\b")


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
        f"[Source {i + 1}: {s.get('filename', '?')}]\n{s.get('content', '')[:600]}"
        for i, s in enumerate(sources)
    ]
    context = "\n\n---\n\n".join(context_parts)

    prompt = _PROMPT.format(context=context, answer=answer[:1000])

    try:
        resp = httpx.post(
            f"{ollama_url}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "think": False,
                "options": {"temperature": 0, "num_predict": 16, "num_ctx": 4096},
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        raw = resp.json()["message"]["content"].strip()
        m = _NUMBER_RE.search(raw)
        if m:
            score = float(m.group(1))
            return round(min(max(score, 0.0), 1.0), 3)
        print(f"    [judge] unexpected output: {raw!r}")
        return None
    except Exception as exc:
        print(f"    [judge error] faithfulness: {exc}")
        return None


_PRECISION_PROMPT = """\
Your job is to check which text chunks are useful for answering a question.

Question: {question}

Text chunks:
{chunks}

Instructions:
- Read each chunk carefully.
- If a chunk directly helps answer the question, mark it 1.
- If a chunk is unrelated or does not help, mark it 0.
- Reply with ONLY the marks in order, separated by commas.
- Do not explain. Do not write code. Just output the marks.

Reply format example (for 5 chunks): 1,0,1,0,0\
"""

_BITS_RE = re.compile(r"[01]")


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

    chunks_text = "\n\n".join(
        f"[Chunk {i + 1}]\n{s.get('content', '')[:400]}"
        for i, s in enumerate(sources)
    )
    prompt = _PRECISION_PROMPT.format(question=question, chunks=chunks_text)

    try:
        resp = httpx.post(
            f"{ollama_url}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "think": False,
                "options": {"temperature": 0, "num_predict": 32, "num_ctx": 4096},
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        raw = resp.json()["message"]["content"].strip()
        bits = _BITS_RE.findall(raw)
        if not bits:
            print(f"    [judge] precision unexpected output: {raw!r}")
            return None
        relevant = sum(int(b) for b in bits)
        return round(relevant / len(bits), 3)
    except Exception as exc:
        print(f"    [judge error] context_precision: {exc}")
        return None
