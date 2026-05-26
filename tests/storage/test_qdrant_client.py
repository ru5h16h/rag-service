from __future__ import annotations

from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from src.config import settings
from src.storage.qdrant_client import ensure_collection


async def test_ensure_collection_creates_collection_and_indexes(
    monkeypatch,
    mock_qdrant_client,
) -> None:
    mock_qdrant_client.collection_exists.side_effect = [False, True]
    monkeypatch.setattr("src.storage.qdrant_client.get_client", lambda: mock_qdrant_client)

    await ensure_collection(768)
    await ensure_collection(768)

    mock_qdrant_client.create_collection.assert_awaited_once_with(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )
    assert mock_qdrant_client.create_payload_index.await_count == 2
    mock_qdrant_client.create_payload_index.assert_any_await(
        collection_name=settings.qdrant_collection,
        field_name="tenant_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    mock_qdrant_client.create_payload_index.assert_any_await(
        collection_name=settings.qdrant_collection,
        field_name="chunk_hash",
        field_schema=PayloadSchemaType.KEYWORD,
    )


async def test_ensure_collection_rejects_non_positive_vector_size() -> None:
    try:
        await ensure_collection(0)
    except ValueError as exc:
        assert str(exc) == "vector_size must be greater than zero"
    else:
        raise AssertionError("ensure_collection should reject invalid vector sizes")
