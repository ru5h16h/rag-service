from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_query(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    return _WHITESPACE_RE.sub(" ", text).strip()


def is_empty_query(text: str) -> bool:
    return len(normalize_query(text)) == 0
