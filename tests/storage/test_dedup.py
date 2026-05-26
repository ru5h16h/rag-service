from __future__ import annotations

import uuid
from types import SimpleNamespace

from src.chunking.base import Chunk
from src.storage.dedup import chunk_to_point_id, compute_chunk_hash, filter_new_chunks


def _chunk(text: str, *, tenant_id: str | None = None) -> Chunk:
    metadata = {"source_path": "fixture.txt"}
    if tenant_id is not None:
        metadata["tenant_id"] = tenant_id
    return Chunk(
        text=text,
        doc_id="doc-1",
        chunk_index=0,
        start_char=0,
        end_char=len(text),
        metadata=metadata,
    )


def test_compute_chunk_hash_is_deterministic() -> None:
    text = "same text"
    assert compute_chunk_hash(text) == compute_chunk_hash(text)


def test_chunk_to_point_id_returns_valid_uuid() -> None:
    point_id = chunk_to_point_id(compute_chunk_hash("chunk text"))
    assert str(uuid.UUID(point_id)) == point_id


async def test_filter_new_chunks_excludes_existing_hashes(
    monkeypatch,
    mock_qdrant_client,
) -> None:
    existing_chunk = _chunk("already indexed")
    new_chunk = _chunk("fresh chunk")
    existing_hash = compute_chunk_hash(existing_chunk.text)
    mock_qdrant_client.scroll.return_value = (
        [SimpleNamespace(payload={"chunk_hash": existing_hash})],
        None,
    )
    monkeypatch.setattr("src.storage.dedup.get_client", lambda: mock_qdrant_client)

    new_chunks, skipped = await filter_new_chunks([existing_chunk, new_chunk])

    assert new_chunks == [new_chunk]
    assert skipped == 1


async def test_filter_new_chunks_skips_duplicates_within_same_batch(
    monkeypatch,
    mock_qdrant_client,
) -> None:
    chunk_a = _chunk("duplicate text", tenant_id="tenant-a")
    chunk_b = _chunk("duplicate text", tenant_id="tenant-a")
    mock_qdrant_client.scroll.return_value = ([], None)
    monkeypatch.setattr("src.storage.dedup.get_client", lambda: mock_qdrant_client)

    new_chunks, skipped = await filter_new_chunks([chunk_a, chunk_b])

    assert new_chunks == [chunk_a]
    assert skipped == 1


async def test_filter_new_chunks_scopes_hash_checks_by_tenant(
    monkeypatch,
    mock_qdrant_client,
) -> None:
    tenant_a_chunk = _chunk("shared content", tenant_id="tenant-a")
    tenant_b_chunk = _chunk("shared content", tenant_id="tenant-b")

    async def scroll_side_effect(*args, **kwargs):
        must_conditions = kwargs["scroll_filter"].must or []
        tenant_id = None
        for condition in must_conditions:
            match = getattr(condition, "match", None)
            value = getattr(match, "value", None)
            if value in {"tenant-a", "tenant-b"}:
                tenant_id = value
                break
        if tenant_id == "tenant-a":
            return (
                [SimpleNamespace(payload={"chunk_hash": compute_chunk_hash(tenant_a_chunk.text)})],
                None,
            )
        return ([], None)

    mock_qdrant_client.scroll.side_effect = scroll_side_effect
    monkeypatch.setattr("src.storage.dedup.get_client", lambda: mock_qdrant_client)

    new_chunks, skipped = await filter_new_chunks([tenant_a_chunk, tenant_b_chunk])

    assert new_chunks == [tenant_b_chunk]
    assert skipped == 1
