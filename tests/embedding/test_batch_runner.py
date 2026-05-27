from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, cast

from src.config import settings
from src.embedding.base import EmbedderBase
from src.embedding.batch_runner import embed_chunks


def _chunk(index: int) -> Any:
    text = f"chunk-{index}"
    return cast(
        Any,
        SimpleNamespace(
            text=text,
            doc_id="doc-1",
            chunk_index=index,
            start_char=index,
            end_char=index + len(text),
            metadata={"source_path": "fixture.txt"},
        ),
    )


class DelayedEmbedder(EmbedderBase):
    vector_size = 2

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if texts[0] == "chunk-0":
            await asyncio.sleep(0.02)
        return [[float(text.rsplit("-", maxsplit=1)[1]), 1.0] for text in texts]


async def test_embed_chunks_preserves_original_order_after_parallel_batches(monkeypatch) -> None:
    monkeypatch.setattr(settings, "embed_batch_size", 2)
    monkeypatch.setattr(settings, "embed_max_concurrency", 2)
    chunks = [_chunk(index) for index in range(4)]

    pairs = await embed_chunks(chunks, DelayedEmbedder())

    assert [chunk.chunk_index for chunk, _ in pairs] == [0, 1, 2, 3]
    assert [vector[0] for _, vector in pairs] == [0.0, 1.0, 2.0, 3.0]


async def test_embed_chunks_returns_empty_list_for_empty_input() -> None:
    assert await embed_chunks([], DelayedEmbedder()) == []
