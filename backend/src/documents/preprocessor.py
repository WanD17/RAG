"""Text preprocessor — cleans raw extracted PDF/DOCX text before chunking.

Steps applied in order:
1. Unicode normalization (NFC) + replace common ligatures
2. Fix hyphenated line breaks (word-\nword → word)
3. Deduplicate repeated header/footer lines (appear on 3+ pages unchanged)
4. Collapse excessive blank lines (3+ → 2)
5. Strip trailing whitespace per line
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

_LIGATURES = str.maketrans({
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl",
    "ﬃ": "ffi", "ﬄ": "ffl",
    "’": "'", "‘": "'",
    "“": '"', "”": '"',
    "–": "-", "—": "-",
})

_HYPHEN_BREAK_RE = re.compile(r"(\w)-\n(\w)")
_MULTI_BLANK_RE = re.compile(r"\n{3,}")
_TRAILING_WS_RE = re.compile(r"[ \t]+$", re.MULTILINE)


def _normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return text.translate(_LIGATURES)


def _fix_hyphen_breaks(text: str) -> str:
    """Merge words split across lines with a hyphen: 'regu-\nlation' → 'regulation'."""
    return _HYPHEN_BREAK_RE.sub(r"\1\2", text)


def _dedup_headers_footers(pages: list[str], min_pages: int = 3) -> list[str]:
    """Remove lines that appear verbatim on min_pages or more pages (repeated headers/footers)."""
    if len(pages) < min_pages:
        return pages

    line_counts: Counter[str] = Counter()
    for page in pages:
        seen = set()
        for line in page.splitlines():
            stripped = line.strip()
            if stripped and stripped not in seen:
                line_counts[stripped] += 1
                seen.add(stripped)

    repeated = {line for line, count in line_counts.items() if count >= min_pages}
    if not repeated:
        return pages

    cleaned = []
    for page in pages:
        lines = [ln for ln in page.splitlines() if ln.strip() not in repeated]
        cleaned.append("\n".join(lines))
    return cleaned


def _collapse_blanks(text: str) -> str:
    text = _TRAILING_WS_RE.sub("", text)
    return _MULTI_BLANK_RE.sub("\n\n", text)


def preprocess(text: str, page_texts: list[str] | None = None) -> str:
    """Apply full preprocessing pipeline. Pass page_texts for header/footer dedup."""
    text = _normalize_unicode(text)
    text = _fix_hyphen_breaks(text)

    if page_texts and len(page_texts) >= 3:
        cleaned_pages = _dedup_headers_footers(
            [_normalize_unicode(p) for p in page_texts]
        )
        text = "\n\n".join(cleaned_pages)

    text = _collapse_blanks(text)
    return text.strip()
