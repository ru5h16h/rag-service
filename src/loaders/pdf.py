from __future__ import annotations

import logging
from pathlib import Path

import fitz

from src.loaders.base import BaseLoader, Document, build_base_metadata

logger = logging.getLogger(__name__)


class PDFLoader(BaseLoader):
    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def load(self, path: Path) -> list[Document]:
        try:
            pdf_document = fitz.open(path)
        except fitz.FileDataError:
            logger.warning("Skipping unreadable PDF: %s", path)
            return []

        with pdf_document:
            page_count = pdf_document.page_count
            documents: list[Document] = []

            for page_index in range(page_count):
                text = pdf_document.load_page(page_index).get_text("text").strip()
                if not text:
                    continue

                metadata = build_base_metadata(
                    path,
                    file_format="pdf",
                    page_number=page_index + 1,
                    page_count=page_count,
                )
                documents.append(Document(content=text, metadata=metadata))

        return documents
