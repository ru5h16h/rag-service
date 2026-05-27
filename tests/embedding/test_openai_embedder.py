from __future__ import annotations

from types import SimpleNamespace

from tenacity import retry_if_exception_type, stop_after_attempt, wait_none

from src.embedding.openai_embedder import OpenAIEmbedder
from src.embedding.retry import RETRY_POLICY


class TransientEmbeddingError(Exception):
    pass


class FakeEmbeddingsClient:
    def __init__(self, *, fail_once: bool = False) -> None:
        self.fail_once = fail_once
        self.calls = 0

    async def create(self, *, model: str, input: list[str]) -> SimpleNamespace:
        self.calls += 1
        if self.fail_once and self.calls == 1:
            raise TransientEmbeddingError("rate limit")
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.1] * OpenAIEmbedder.vector_size) for _ in input]
        )


class FakeOpenAIClient:
    def __init__(self, embeddings: FakeEmbeddingsClient) -> None:
        self.embeddings = embeddings


def _retry_policy_for_test() -> dict[str, object]:
    return {
        **RETRY_POLICY,
        "retry": retry_if_exception_type(TransientEmbeddingError),
        "stop": stop_after_attempt(2),
        "wait": wait_none(),
    }


async def test_openai_embedder_retries_transient_rate_limit_like_errors() -> None:
    embeddings = FakeEmbeddingsClient(fail_once=True)
    embedder = OpenAIEmbedder(
        client=FakeOpenAIClient(embeddings),
        retry_policy=_retry_policy_for_test(),
    )

    vectors = await embedder.embed_batch(["alpha"])

    assert embeddings.calls == 2
    assert len(vectors) == 1
    assert len(vectors[0]) == 1536


async def test_openai_embedder_returns_one_1536_dimensional_vector_per_text() -> None:
    embeddings = FakeEmbeddingsClient()
    embedder = OpenAIEmbedder(
        client=FakeOpenAIClient(embeddings),
        retry_policy=_retry_policy_for_test(),
    )

    vectors = await embedder.embed_batch(["alpha", "beta"])

    assert embeddings.calls == 1
    assert len(vectors) == 2
    assert all(len(vector) == 1536 for vector in vectors)
