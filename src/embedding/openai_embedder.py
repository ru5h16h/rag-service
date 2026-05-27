from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, cast

from tenacity import AsyncRetrying

from src.config import settings
from src.embedding.base import EmbedderBase
from src.embedding.retry import RETRY_POLICY


class _EmbeddingData(Protocol):
    embedding: Sequence[float]


class _EmbeddingResponse(Protocol):
    data: Sequence[_EmbeddingData]


class _EmbeddingsClient(Protocol):
    async def create(self, *, model: str, input: list[str]) -> _EmbeddingResponse: ...


class _OpenAIClient(Protocol):
    embeddings: _EmbeddingsClient


class OpenAIEmbedder(EmbedderBase):
    """OpenAI embedding backend with tenacity retry handling."""

    vector_size = 1536

    def __init__(
        self,
        *,
        client: _OpenAIClient | None = None,
        model: str | None = None,
        retry_policy: Mapping[str, Any] | None = None,
    ) -> None:
        self.client = client or self._build_client()
        self.model = model or settings.openai_embedding_model
        self.retry_policy: dict[str, Any] = dict(retry_policy or RETRY_POLICY)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response: _EmbeddingResponse | None = None
        async for attempt in AsyncRetrying(**self.retry_policy):
            with attempt:
                response = await self.client.embeddings.create(model=self.model, input=texts)

        if response is None:
            raise RuntimeError("OpenAI embedding request did not return a response")

        vectors = [[float(value) for value in item.embedding] for item in response.data]
        if len(vectors) != len(texts):
            raise ValueError(
                f"OpenAI returned {len(vectors)} embeddings for {len(texts)} input texts"
            )
        return vectors

    def _build_client(self) -> _OpenAIClient:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI embedding backend requires the 'openai' package. "
                "Install the embedding extra before using EMBEDDING_BACKEND=openai."
            ) from exc

        return cast(_OpenAIClient, AsyncOpenAI(api_key=settings.openai_api_key))
