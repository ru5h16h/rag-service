from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Document:
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseLoader(ABC):
    @abstractmethod
    def load(self, path: Path) -> list[Document]:
        """Load a file and return one or more normalized documents."""

    @abstractmethod
    def supports(self, path: Path) -> bool:
        """Return True when the loader can handle the given file path."""


def build_base_metadata(path: Path, *, file_format: str, **extra: Any) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "source_path": str(path.resolve()),
        "format": file_format,
        "loaded_at": datetime.now(UTC).isoformat(),
    }
    metadata.update(extra)
    return metadata
