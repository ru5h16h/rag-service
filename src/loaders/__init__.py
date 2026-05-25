"""Document loaders for supported source formats."""

from src.loaders.base import BaseLoader, Document
from src.loaders.docx import DOCXLoader
from src.loaders.html import HTMLLoader
from src.loaders.markdown import MarkdownLoader
from src.loaders.pdf import PDFLoader
from src.loaders.registry import LoaderRegistry, load

__all__ = [
    "BaseLoader",
    "DOCXLoader",
    "Document",
    "HTMLLoader",
    "LoaderRegistry",
    "MarkdownLoader",
    "PDFLoader",
    "load",
]
