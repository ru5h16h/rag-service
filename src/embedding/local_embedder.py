from __future__ import annotations

import asyncio
from typing import Any, Protocol, cast

from src.config import settings
from src.embedding.base import EmbedderBase


class _SentenceTransformerModel(Protocol):
    def encode(self, texts: list[str], *, normalize_embeddings: bool) -> Any: ...


class LocalEmbedder(EmbedderBase):
    """Local sentence-transformers backend for offline/free embeddings."""

    vector_size = 768

    def __init__(self, model: _SentenceTransformerModel | None = None) -> None:
        self.model = model or self._load_model()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        vectors = await asyncio.to_thread(
            self.model.encode,
            texts,
            normalize_embeddings=True,
        )
        vector_lists = self._coerce_vectors(vectors)
        if len(vector_lists) != len(texts):
            raise ValueError(
                f"Local embedder returned {len(vector_lists)} embeddings for {len(texts)} texts"
            )
        return vector_lists

    def _load_model(self) -> _SentenceTransformerModel:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Local embedding backend requires the 'sentence-transformers' package. "
                "Install the embedding extra before using EMBEDDING_BACKEND=local."
            ) from exc

        return cast(_SentenceTransformerModel, SentenceTransformer(settings.local_embedding_model))

    def _coerce_vectors(self, vectors: Any) -> list[list[float]]:
        if hasattr(vectors, "tolist"):
            vectors = vectors.tolist()
        return [[float(value) for value in vector] for vector in vectors]
