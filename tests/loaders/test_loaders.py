from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.loaders.docx import DOCXLoader
from src.loaders.html import HTMLLoader
from src.loaders.markdown import MarkdownLoader
from src.loaders.pdf import PDFLoader
from src.loaders.registry import LoaderRegistry

FIXTURES_DIR = Path(__file__).parent / "fixtures"
HTML_TAG_RE = re.compile(r"<[^>]+>")


@pytest.mark.parametrize(
    ("loader", "fixture_name", "expected_format"),
    [
        (PDFLoader(), "sample.pdf", "pdf"),
        (HTMLLoader(), "sample.html", "html"),
        (MarkdownLoader(), "sample.md", "markdown"),
        (DOCXLoader(), "sample.docx", "docx"),
    ],
)
def test_each_loader_returns_documents_with_required_metadata(
    loader: object,
    fixture_name: str,
    expected_format: str,
) -> None:
    path = FIXTURES_DIR / fixture_name
    documents = loader.load(path)  # type: ignore[attr-defined]

    assert documents
    assert all(document.content.strip() for document in documents)
    assert all(document.metadata["source_path"] == str(path.resolve()) for document in documents)
    assert all(document.metadata["format"] == expected_format for document in documents)
    assert all("loaded_at" in document.metadata for document in documents)


def test_pdf_loader_returns_one_document_per_page() -> None:
    documents = PDFLoader().load(FIXTURES_DIR / "sample.pdf")

    assert len(documents) == 2
    assert documents[0].metadata["page_number"] == 1
    assert documents[1].metadata["page_number"] == 2
    assert all(document.metadata["page_count"] == 2 for document in documents)
    assert all(HTML_TAG_RE.search(document.content) is None for document in documents)


def test_html_loader_strips_navigation_footer_and_tags() -> None:
    document = HTMLLoader().load(FIXTURES_DIR / "sample.html")[0]

    assert "Top navigation" not in document.content
    assert "Footer links" not in document.content
    assert HTML_TAG_RE.search(document.content) is None
    assert document.metadata["title"] == "Sample HTML Document"


def test_markdown_loader_strips_front_matter_and_heading_markers() -> None:
    document = MarkdownLoader().load(FIXTURES_DIR / "sample.md")[0]

    assert "title: Markdown Fixture" not in document.content
    assert "tags:" not in document.content
    assert document.content.splitlines()[0] == "Markdown Fixture"
    assert document.metadata["h1_title"] == "Markdown Fixture"


def test_docx_loader_includes_table_text_and_counts_metadata() -> None:
    document = DOCXLoader().load(FIXTURES_DIR / "sample.docx")[0]

    assert "Heading Example" in document.content
    assert "Column A\tColumn B" in document.content
    assert document.metadata["heading_count"] == 1
    assert document.metadata["table_count"] == 1


def test_loader_registry_dispatches_by_extension() -> None:
    pdf_documents = LoaderRegistry.load(FIXTURES_DIR / "sample.pdf")
    html_documents = LoaderRegistry.load(FIXTURES_DIR / "sample.html")
    markdown_documents = LoaderRegistry.load(FIXTURES_DIR / "sample.md")
    docx_documents = LoaderRegistry.load(FIXTURES_DIR / "sample.docx")

    assert len(pdf_documents) == 2
    assert html_documents[0].metadata["format"] == "html"
    assert markdown_documents[0].metadata["format"] == "markdown"
    assert docx_documents[0].metadata["format"] == "docx"


def test_loader_registry_raises_for_unknown_extension(tmp_path: Path) -> None:
    unknown_file = tmp_path / "sample.txt"
    unknown_file.write_text("plain text", encoding="utf-8")

    with pytest.raises(ValueError, match=r"No loader found for \.txt"):
        LoaderRegistry.load(unknown_file)
