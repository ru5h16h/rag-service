from __future__ import annotations

import re
import unicodedata


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace while preserving paragraph boundaries."""
    paragraphs = re.split(r"\n{2,}", text)
    cleaned = [re.sub(r"[ \t]+", " ", paragraph).strip() for paragraph in paragraphs]
    return "\n\n".join(paragraph for paragraph in cleaned if paragraph)


def strip_boilerplate(text: str, patterns: list[str] | None = None) -> str:
    """Remove lines that match known boilerplate patterns."""
    default_patterns = [
        r"page\s+\d+\s+of\s+\d+",
        r"©\s*\d{4}",
        r"all rights reserved",
        r"^\s*[-–—]{3,}\s*$",
    ]
    active_patterns = default_patterns if patterns is None else patterns
    lines = text.splitlines()
    kept_lines = [
        line
        for line in lines
        if not any(re.search(pattern, line, re.IGNORECASE) for pattern in active_patterns)
    ]
    return "\n".join(kept_lines)


def normalize_unicode(text: str) -> str:
    """Normalize unicode text and replace common typography with ASCII."""
    normalized = unicodedata.normalize("NFKC", text)
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for original, replacement in replacements.items():
        normalized = normalized.replace(original, replacement)
    return normalized
