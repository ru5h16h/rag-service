from __future__ import annotations

from abc import ABC, abstractmethod


class EmbedderBase(ABC):
    """Common async interface for embedding backends."""

    vector_size: int

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts, returning one vector per input text."""
        ...
