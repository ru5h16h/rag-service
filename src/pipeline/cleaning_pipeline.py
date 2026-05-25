from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from src.config import settings
from src.loaders.base import Document
from src.utils.cleaning import normalize_unicode, normalize_whitespace, strip_boilerplate
from src.utils.language import detect_language

CleaningStep = Callable[[str], str]


def build_pipeline(extra_patterns: list[str] | None = None) -> list[CleaningStep]:
    return [
        normalize_unicode,
        lambda text: strip_boilerplate(text, extra_patterns),
        normalize_whitespace,
    ]


def clean_document(
    doc: Document,
    pipeline: list[CleaningStep] | None = None,
) -> Document | None:
    """Clean a document and drop it if it fails length or language checks."""
    steps = build_pipeline() if pipeline is None else pipeline
    text = doc.content
    for step in steps:
        text = step(text)

    if len(text) < settings.min_content_chars:
        return None

    language = detect_language(text, settings.language_confidence_threshold)
    if language != settings.target_language:
        return None

    return replace(doc, content=text, metadata={**doc.metadata, "language": language})
