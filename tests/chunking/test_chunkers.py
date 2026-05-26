from __future__ import annotations

import tiktoken

from src.chunking.fixed import FixedSizeChunker
from src.chunking.semantic import SemanticChunker
from src.config import settings
from src.loaders.base import Document


def test_fixed_chunker_overlap(monkeypatch, sample_text: str) -> None:
    monkeypatch.setattr(settings, "chunk_size_tokens", 20)
    monkeypatch.setattr(settings, "chunk_overlap_pct", 0.2)
    chunker = FixedSizeChunker()
    document = Document(content=f"{sample_text} " * 20, metadata={"source_path": "sample.txt"})

    chunks = chunker.chunk(document, doc_id="test-doc")

    assert len(chunks) > 1
    overlap_tokens = int(settings.chunk_size_tokens * settings.chunk_overlap_pct)
    enc = tiktoken.get_encoding("cl100k_base")
    for index in range(len(chunks) - 1):
        tail_tokens = enc.encode(chunks[index].text)[-overlap_tokens:]
        head_tokens = enc.encode(chunks[index + 1].text)[:overlap_tokens]
        assert tail_tokens == head_tokens


def test_fixed_chunker_returns_one_chunk_for_short_document(monkeypatch, sample_text: str) -> None:
    monkeypatch.setattr(settings, "chunk_size_tokens", 512)
    monkeypatch.setattr(settings, "chunk_overlap_pct", 0.15)
    chunker = FixedSizeChunker()
    document = Document(content=sample_text, metadata={"source_path": "short.txt"})

    chunks = chunker.chunk(document, doc_id="short-doc")

    assert len(chunks) == 1
    assert chunks[0].metadata["chunk_strategy"] == "fixed"
    assert chunks[0].text == sample_text


def test_semantic_chunker_preserves_sentence_boundaries(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chunk_size_tokens", 12)
    monkeypatch.setattr(settings, "chunk_overlap_pct", 0.25)
    chunker = SemanticChunker()
    content = (
        "Alpha sentence is concise. "
        "Beta sentence carries more detail for testing. "
        "Gamma sentence closes the sample cleanly!"
    )
    document = Document(content=content, metadata={"source_path": "semantic.txt"})

    chunks = chunker.chunk(document, doc_id="semantic-doc")

    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.metadata["chunk_strategy"] == "semantic"
        assert chunk.text.endswith((".", "?", "!"))


def test_chunkers_propagate_document_metadata(monkeypatch, sample_text: str) -> None:
    monkeypatch.setattr(settings, "chunk_size_tokens", 20)
    monkeypatch.setattr(settings, "chunk_overlap_pct", 0.1)
    document = Document(
        content=f"{sample_text} " * 10,
        metadata={"source_path": "meta.txt", "format": "txt"},
    )

    fixed_chunks = FixedSizeChunker().chunk(document, doc_id="fixed-doc")
    semantic_chunks = SemanticChunker().chunk(document, doc_id="semantic-doc")

    assert fixed_chunks
    assert semantic_chunks
    assert fixed_chunks[0].metadata["source_path"] == "meta.txt"
    assert semantic_chunks[0].metadata["format"] == "txt"
