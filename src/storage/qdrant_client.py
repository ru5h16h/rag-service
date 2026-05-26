from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from src.config import settings

_client: AsyncQdrantClient | None = None


def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
    return _client


async def ensure_collection(vector_size: int) -> None:
    """Create the configured collection and payload indexes if needed."""
    if vector_size <= 0:
        msg = "vector_size must be greater than zero"
        raise ValueError(msg)

    client = get_client()
    exists = await client.collection_exists(settings.qdrant_collection)
    if exists:
        return

    await client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    await client.create_payload_index(
        collection_name=settings.qdrant_collection,
        field_name="tenant_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    await client.create_payload_index(
        collection_name=settings.qdrant_collection,
        field_name="chunk_hash",
        field_schema=PayloadSchemaType.KEYWORD,
    )
