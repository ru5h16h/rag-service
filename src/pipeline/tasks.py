from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from prefect import task
from prefect.cache_policies import NO_CACHE
from qdrant_client.models import PointStruct

from src.chunking.base import Chunk
from src.chunking.fixed import FixedSizeChunker
from src.chunking.semantic import SemanticChunker
from src.config import settings
from src.embedding.base import EmbedderBase
from src.embedding.batch_runner import embed_chunks
from src.loaders.base import Document
from src.loaders.registry import load as load_doc
from src.pipeline.cleaning_pipeline import build_pipeline, clean_document
from src.storage.dedup import chunk_to_point_id, compute_chunk_hash, filter_new_chunks
from src.storage.ingestion_repo import IngestionRepo, JobStatus
from src.storage.qdrant_client import get_client

_UPSERT_BATCH_SIZE = 256


@task(retries=2, retry_delay_seconds=5, name="load-document")
def load(path: Path) -> list[Document]:
    return load_doc(path)


@task(name="clean-documents")
def clean(documents: list[Document]) -> list[Document]:
    pipeline = build_pipeline()
    return [d for doc in documents if (d := clean_document(doc, pipeline)) is not None]


@task(name="chunk-documents")
def chunk(documents: list[Document]) -> list[Chunk]:
    chunker = FixedSizeChunker() if settings.chunker_strategy == "fixed" else SemanticChunker()

    all_chunks: list[Chunk] = []
    for doc in documents:
        doc_id = str(uuid.uuid4())
        all_chunks.extend(chunker.chunk(doc, doc_id))
    return all_chunks


@task(name="dedup-check")
async def dedup(chunks: list[Chunk]) -> tuple[list[Chunk], int]:
    return await filter_new_chunks(chunks)


@task(name="embed-chunks", cache_policy=NO_CACHE)
async def embed(
    chunks: list[Chunk],
    embedder: EmbedderBase,
) -> list[tuple[Chunk, list[float]]]:
    return await embed_chunks(chunks, embedder)


def _iter_batches(
    items: list[tuple[Chunk, list[float]]],
    batch_size: int,
) -> list[list[tuple[Chunk, list[float]]]]:
    return [items[start : start + batch_size] for start in range(0, len(items), batch_size)]


def _build_point(chunk: Chunk, vector: list[float]) -> PointStruct:
    chunk_hash = compute_chunk_hash(chunk.text)
    payload: dict[str, Any] = {
        **chunk.metadata,
        "doc_id": chunk.doc_id,
        "chunk_index": chunk.chunk_index,
        "start_char": chunk.start_char,
        "end_char": chunk.end_char,
        "text": chunk.text,
        "chunk_hash": chunk_hash,
    }
    return PointStruct(
        id=chunk_to_point_id(chunk_hash),
        vector=vector,
        payload=payload,
    )


@task(name="upsert-to-qdrant")
async def upsert(
    chunk_vector_pairs: list[tuple[Chunk, list[float]]],
    collection: str,
) -> int:
    if not chunk_vector_pairs:
        return 0

    client = get_client()
    written_count = 0

    for batch in _iter_batches(chunk_vector_pairs, _UPSERT_BATCH_SIZE):
        points = [_build_point(chunk, vector) for chunk, vector in batch]
        await client.upsert(collection_name=collection, points=points)
        written_count += len(points)

    return written_count


@task(name="update-job-status", cache_policy=NO_CACHE)
async def update_status(
    repo: IngestionRepo,
    job_id: uuid.UUID,
    status: JobStatus,
    **kwargs: Any,
) -> None:
    await repo.update_status(job_id, status, **kwargs)
