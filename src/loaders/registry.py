from __future__ import annotations

from pathlib import Path

from src.loaders.base import BaseLoader, Document
from src.loaders.docx import DOCXLoader
from src.loaders.html import HTMLLoader
from src.loaders.markdown import MarkdownLoader
from src.loaders.pdf import PDFLoader

_LOADERS: list[BaseLoader] = [
    PDFLoader(),
    HTMLLoader(),
    MarkdownLoader(),
    DOCXLoader(),
]


class LoaderRegistry:
    @staticmethod
    def load(path: Path) -> list[Document]:
        for loader in _LOADERS:
            if loader.supports(path):
                return loader.load(path)
        raise ValueError(f"No loader found for {path.suffix}")


def load(path: Path) -> list[Document]:
    return LoaderRegistry.load(path)
