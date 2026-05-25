from __future__ import annotations

from typing import cast

from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 42


def detect_language(text: str, confidence_threshold: float = 0.9) -> str | None:
    """Return a detected language code when confidence clears the threshold."""
    sample = text[:2000].strip()
    if not sample:
        return None

    try:
        candidates = detect_langs(sample)
    except LangDetectException:
        return None

    if not candidates:
        return None

    best_match = candidates[0]
    if best_match.prob < confidence_threshold:
        return None
    return cast(str, best_match.lang)
