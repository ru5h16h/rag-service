from __future__ import annotations

from src.loaders.base import Document
from src.pipeline import cleaning_pipeline


def test_clean_document_returns_none_for_short_text(monkeypatch) -> None:
    monkeypatch.setattr(cleaning_pipeline.settings, "min_content_chars", 20)
    document = Document(content="too short", metadata={"source_path": "short.txt"})

    cleaned = cleaning_pipeline.clean_document(document)

    assert cleaned is None


def test_clean_document_returns_none_for_non_target_language(monkeypatch) -> None:
    monkeypatch.setattr(cleaning_pipeline.settings, "min_content_chars", 10)
    monkeypatch.setattr(cleaning_pipeline.settings, "target_language", "en")
    monkeypatch.setattr(
        cleaning_pipeline,
        "detect_language",
        lambda text, confidence_threshold=0.9: "fr",
    )
    document = Document(
        content="This sentence is long enough to pass the length check.",
        metadata={"source_path": "foreign.txt"},
    )

    cleaned = cleaning_pipeline.clean_document(document)

    assert cleaned is None


def test_clean_document_applies_pipeline_and_sets_language(monkeypatch) -> None:
    monkeypatch.setattr(cleaning_pipeline.settings, "min_content_chars", 10)
    monkeypatch.setattr(cleaning_pipeline.settings, "target_language", "en")
    monkeypatch.setattr(cleaning_pipeline.settings, "language_confidence_threshold", 0.9)
    monkeypatch.setattr(
        cleaning_pipeline,
        "detect_language",
        lambda text, confidence_threshold=0.9: "en",
    )
    document = Document(
        content="  “Hello”   world  \n\nPage 1 of 3\n\nUseful section  ",
        metadata={"source_path": "example.txt"},
    )

    cleaned = cleaning_pipeline.clean_document(document)

    assert cleaned is not None
    assert cleaned.content == '"Hello" world\n\nUseful section'
    assert cleaned.metadata["language"] == "en"
    assert "Page 1 of 3" not in cleaned.content
