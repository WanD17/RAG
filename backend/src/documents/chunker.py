from __future__ import annotations

import re

import tiktoken

_encoder: tiktoken.Encoding | None = None

# Heading hierarchy: (level, regex). Level 0=Part, 1=Chapter, 2=Section/Title, 3=Article, 4=Subsection
_HEADING_LEVELS: list[tuple[int, re.Pattern[str]]] = [
    (0, re.compile(r"^(part\s+(?:[ivxlcdm]+|\d+)\b.{0,80})$", re.I)),
    (1, re.compile(r"^(chapter\s+(?:[ivxlcdm]+|\d+)\b.{0,80})$", re.I)),
    (2, re.compile(r"^((?:title|section)\s+(?:[ivxlcdm]+|\d[\d.]*)\b.{0,80})$", re.I)),
    (3, re.compile(r"^(article\s+\d+\b.{0,100})$", re.I)),
    (4, re.compile(r"^(\d+(?:\.\d+)+\.?\s+[A-Z].{0,80})$")),
]
# Short ALL-CAPS lines treated as level-1 headings (e.g. "GENERAL PROVISIONS")
_ALLCAPS_RE = re.compile(r"^[A-Z][A-Z\s\-/]{3,57}[A-Z]$")


def get_encoder() -> tiktoken.Encoding:
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


def count_tokens(text: str) -> int:
    return len(get_encoder().encode(text))


def _split_by_separator(text: str, separator: str) -> list[str]:
    if separator == "":
        return list(text)
    parts = text.split(separator)
    return [p for p in parts if p.strip() or p == ""]


def _hard_split_by_tokens(text: str, chunk_size: int) -> list[str]:
    encoder = get_encoder()
    tokens = encoder.encode(text)
    return [encoder.decode(tokens[i : i + chunk_size]) for i in range(0, len(tokens), chunk_size)]


def _split_recursive(text: str, chunk_size: int, sep_index: int, separators: list[str]) -> list[str]:
    if count_tokens(text) <= chunk_size:
        return [text]

    if sep_index >= len(separators):
        return _hard_split_by_tokens(text, chunk_size)

    sep = separators[sep_index]
    parts = _split_by_separator(text, sep)

    if len(parts) <= 1:
        return _split_recursive(text, chunk_size, sep_index + 1, separators)

    results: list[str] = []
    for part in parts:
        if count_tokens(part) <= chunk_size:
            if part.strip():
                results.append(part)
        else:
            results.extend(_split_recursive(part, chunk_size, sep_index + 1, separators))
    return results


def _merge_splits(splits: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    encoder = get_encoder()
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for split in splits:
        split_len = len(encoder.encode(split))

        if current_len + split_len > chunk_size and current:
            merged = " ".join(current).strip()
            if merged:
                chunks.append(merged)

            overlap: list[str] = []
            overlap_len = 0
            for piece in reversed(current):
                piece_len = len(encoder.encode(piece))
                if overlap_len + piece_len > chunk_overlap:
                    break
                overlap.insert(0, piece)
                overlap_len += piece_len
            current = overlap
            current_len = overlap_len

        current.append(split)
        current_len += split_len

    if current:
        merged = " ".join(current).strip()
        if merged:
            chunks.append(merged)

    return chunks


def _chunk_flat(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Flat recursive chunking — used per section after structure is split out."""
    text = text.strip()
    if not text:
        return []
    if count_tokens(text) <= chunk_size:
        return [text]
    separators = ["\n\n", "\n", ". ", " ", ""]
    splits = _split_recursive(text, chunk_size, 0, separators)
    return _merge_splits(splits, chunk_size, chunk_overlap)


def _detect_heading(line: str) -> tuple[int, str] | None:
    """Return (level, title) if line is a structural heading, else None."""
    if not line or len(line) < 3 or len(line) > 200:
        return None
    for level, pattern in _HEADING_LEVELS:
        m = pattern.match(line)
        if m:
            title = m.group(1).strip()
            return (level, title[:60] if len(title) > 60 else title)
    if _ALLCAPS_RE.match(line):
        return (1, line[:60])
    return None


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split text at heading boundaries. Returns [(breadcrumb, body_text), ...]."""
    lines = text.splitlines(keepends=True)
    sections: list[tuple[str, str]] = []
    crumbs: list[tuple[int, str]] = []
    current: list[str] = []

    def _flush() -> None:
        body = "".join(current).strip()
        if body:
            bc = " > ".join(t for _, t in crumbs)
            sections.append((bc, body))
        current.clear()

    for line in lines:
        h = _detect_heading(line.strip())
        if h is not None:
            _flush()
            level, title = h
            crumbs = [(lv, t) for lv, t in crumbs if lv < level] + [(level, title)]
        else:
            current.append(line)

    _flush()
    return sections


def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> list[str]:
    """Section-aware chunking with heading breadcrumb prefix.

    Detects structural headings (Part / Chapter / Article / numbered subsections),
    splits the document into sections, and prepends each chunk with a breadcrumb
    like '[Chapter I > Article 12. Criminal liability]' for retrieval signal.

    Falls back to flat recursive chunking if no headings are detected.
    """
    text = text.strip()
    if not text:
        return []

    sections = _split_into_sections(text)

    # No headings found → flat chunking (backward compat for plain-text files)
    if not sections or all(not bc for bc, _ in sections):
        return _chunk_flat(text, chunk_size, chunk_overlap)

    result: list[str] = []
    for breadcrumb, body in sections:
        flat = _chunk_flat(body, chunk_size, chunk_overlap)
        if breadcrumb:
            prefix = f"[{breadcrumb}] "
            result.extend(prefix + c for c in flat)
        else:
            result.extend(flat)
    return result
