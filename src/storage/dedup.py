from __future__ import annotations

import hashlib
import uuid
from collections.abc import Iterable
from typing import TypeAlias

from qdrant_client.models import Condition, FieldCondition, Filter, MatchAny, MatchValue

from src.chunking.base import Chunk
from src.config import settings
from src.storage.qdrant_client import get_client

_HASH_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
_HASH_BATCH_SIZE = 256
TenantKey: TypeAlias = str | None


def compute_chunk_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_to_point_id(chunk_hash: str) -> str:
    """Derive a deterministic point ID from a chunk hash."""
    return str(uuid.uuid5(_HASH_NAMESPACE, chunk_hash))


async def filter_new_chunks(chunks: list[Chunk]) -> tuple[list[Chunk], int]:
    """
    Return only chunks that do not already exist in Qdrant.

    Chunks are checked by content hash and, when present in metadata, tenant ID.
    Duplicate chunks within the same input batch are also skipped so upserts stay idempotent.
    """
    if not chunks:
        return [], 0

    existing_by_tenant: dict[TenantKey, set[str]] = {}
    grouped_hashes = _group_hashes_by_tenant(chunks)

    for tenant_id, hashes in grouped_hashes.items():
        existing_by_tenant[tenant_id] = await _fetch_existing_hashes(hashes, tenant_id)

    new_chunks: list[Chunk] = []
    seen_by_tenant: dict[TenantKey, set[str]] = {}
    skipped_count = 0

    for chunk in chunks:
        tenant_id = _tenant_id_for_chunk(chunk)
        chunk_hash = compute_chunk_hash(chunk.text)
        seen_hashes = seen_by_tenant.setdefault(tenant_id, set())
        existing_hashes = existing_by_tenant.get(tenant_id, set())

        if chunk_hash in existing_hashes or chunk_hash in seen_hashes:
            skipped_count += 1
            continue

        seen_hashes.add(chunk_hash)
        new_chunks.append(chunk)

    return new_chunks, skipped_count


def _tenant_id_for_chunk(chunk: Chunk) -> TenantKey:
    tenant_value = chunk.metadata.get("tenant_id")
    return tenant_value if isinstance(tenant_value, str) and tenant_value else None


def _group_hashes_by_tenant(chunks: Iterable[Chunk]) -> dict[TenantKey, list[str]]:
    grouped: dict[TenantKey, list[str]] = {}
    for chunk in chunks:
        grouped.setdefault(_tenant_id_for_chunk(chunk), []).append(compute_chunk_hash(chunk.text))
    return grouped


async def _fetch_existing_hashes(hashes: list[str], tenant_id: TenantKey) -> set[str]:
    client = get_client()
    existing: set[str] = set()

    for hash_batch in _iter_hash_batches(hashes):
        offset: str | int | uuid.UUID | None = None
        must_conditions: list[Condition] = [
            FieldCondition(key="chunk_hash", match=MatchAny(any=hash_batch))
        ]
        if tenant_id is not None:
            must_conditions.append(
                FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))
            )

        while True:
            points, offset = await client.scroll(
                collection_name=settings.qdrant_collection,
                scroll_filter=Filter(must=must_conditions),
                limit=_HASH_BATCH_SIZE,
                with_payload=["chunk_hash"],
                offset=offset,
            )
            for point in points:
                payload = point.payload or {}
                chunk_hash = payload.get("chunk_hash")
                if isinstance(chunk_hash, str):
                    existing.add(chunk_hash)
            if offset is None:
                break

    return existing


def _iter_hash_batches(hashes: list[str]) -> Iterable[list[str]]:
    for start in range(0, len(hashes), _HASH_BATCH_SIZE):
        yield hashes[start : start + _HASH_BATCH_SIZE]
