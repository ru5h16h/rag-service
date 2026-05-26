from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.loaders.base import Document


@dataclass(slots=True)
class Chunk:
    text: str
    doc_id: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, doc: Document, doc_id: str) -> list[Chunk]:
        """Split a document into chunks for embedding and indexing."""
