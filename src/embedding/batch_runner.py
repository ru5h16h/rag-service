from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from src.config import settings
from src.embedding.base import EmbedderBase

if TYPE_CHECKING:
    from src.chunking.base import Chunk

logger = logging.getLogger(__name__)


async def embed_chunks(
    chunks: list[Chunk],
    embedder: EmbedderBase,
) -> list[tuple[Chunk, list[float]]]:
    """
    Embed chunks in configured batches with concurrency control.

    The returned pairs preserve the same order as the incoming chunks.
    """
    if not chunks:
        return []
    if settings.embed_batch_size <= 0:
        raise ValueError("embed_batch_size must be greater than 0")
    if settings.embed_max_concurrency <= 0:
        raise ValueError("embed_max_concurrency must be greater than 0")

    semaphore = asyncio.Semaphore(settings.embed_max_concurrency)
    batches = [
        chunks[start : start + settings.embed_batch_size]
        for start in range(0, len(chunks), settings.embed_batch_size)
    ]

    async def embed_one_batch(batch: list[Chunk], batch_index: int) -> list[list[float]]:
        async with semaphore:
            vectors = await embedder.embed_batch([chunk.text for chunk in batch])
            if len(vectors) != len(batch):
                raise ValueError(
                    f"Embedder returned {len(vectors)} vectors for {len(batch)} chunks "
                    f"in batch {batch_index + 1}"
                )
            logger.info(
                "Embedded batch %s/%s (%s chunks)",
                batch_index + 1,
                len(batches),
                len(batch),
            )
            return vectors

    batch_vectors = await asyncio.gather(
        *[embed_one_batch(batch, index) for index, batch in enumerate(batches)]
    )
    flat_vectors = [vector for vectors in batch_vectors for vector in vectors]
    return list(zip(chunks, flat_vectors, strict=True))
