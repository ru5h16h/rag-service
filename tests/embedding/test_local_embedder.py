from __future__ import annotations

from src.embedding.local_embedder import LocalEmbedder


class FakeVectorArray:
    def __init__(self, values: list[list[float]]) -> None:
        self.values = values

    def tolist(self) -> list[list[float]]:
        return self.values


class FakeSentenceTransformer:
    def __init__(self) -> None:
        self.received_texts: list[str] = []
        self.normalize_embeddings: bool | None = None

    def encode(self, texts: list[str], *, normalize_embeddings: bool) -> FakeVectorArray:
        self.received_texts = texts
        self.normalize_embeddings = normalize_embeddings
        return FakeVectorArray([[0.1] * LocalEmbedder.vector_size for _ in texts])


async def test_local_embedder_returns_768_dimensional_vectors() -> None:
    model = FakeSentenceTransformer()
    embedder = LocalEmbedder(model=model)

    vectors = await embedder.embed_batch(["alpha", "beta"])

    assert model.received_texts == ["alpha", "beta"]
    assert model.normalize_embeddings is True
    assert len(vectors) == 2
    assert all(len(vector) == 768 for vector in vectors)
