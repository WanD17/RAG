from __future__ import annotations

import tiktoken

_encoder: tiktoken.Encoding | None = None


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


def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> list[str]:
    text = text.strip()
    if not text:
        return []

    if count_tokens(text) <= chunk_size:
        return [text]

    separators = ["\n\n", "\n", ". ", " ", ""]
    splits = _split_recursive(text, chunk_size, 0, separators)
    return _merge_splits(splits, chunk_size, chunk_overlap)
