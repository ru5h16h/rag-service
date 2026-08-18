import time
import uuid
from pathlib import Path
from typing import Any

from prefect import flow

from src.config import settings
from src.embedding.local_embedder import LocalEmbedder
from src.embedding.openai_embedder import OpenAIEmbedder
from src.loaders.base import Document
from src.pipeline.tasks import chunk, clean, dedup, embed, load, update_status, upsert
from src.storage.ingestion_repo import IngestionRepo
from src.storage.pg_client import get_session
from src.storage.qdrant_client import ensure_collection


@flow(name="ingest-document", log_prints=True)
async def ingest_document(source_path: str, tenant_id: str = "default") -> dict[str, Any]:
    path = Path(source_path)
    start = time.perf_counter()
    job_id: uuid.UUID | None = None
    is_running = False

    doc_id = str(uuid.uuid4())

    async with get_session() as session:
        repo = IngestionRepo(session)

        try:
            job_id = await repo.create_job(
                doc_id=doc_id,
                source_path=str(path),
                tenant_id=tenant_id,
            )
            await update_status(repo, job_id, "running")
            is_running = True

            documents = load(path)
            documents = _attach_tenant(documents, tenant_id)
            cleaned_documents = clean(documents)
            chunks = chunk(cleaned_documents)
            new_chunks, skipped_count = await dedup(chunks)

            embedder = (
                OpenAIEmbedder() if settings.embedding_backend == "openai" else LocalEmbedder()
            )

            await ensure_collection(embedder.vector_size)

            chunk_vector_pairs = await embed(new_chunks, embedder)
            indexed_count = await upsert(
                chunk_vector_pairs,
                settings.qdrant_collection,
            )

            duration_seconds = time.perf_counter() - start
            await update_status(
                repo,
                job_id,
                "done",
                chunk_count=indexed_count,
                skipped_count=skipped_count,
                duration_seconds=duration_seconds,
            )

            return {
                "status": "done",
                "job_id": str(job_id),
                "doc_id": doc_id,
                "source_path": str(path),
                "tenant_id": tenant_id,
                "document_count": len(documents),
                "cleaned_document_count": len(cleaned_documents),
                "total_chunk_count": len(chunks),
                "chunk_count": indexed_count,
                "skipped_count": skipped_count,
                "duration_seconds": duration_seconds,
            }

        except Exception as exc:
            duration_seconds = time.perf_counter() - start

            if job_id is not None and is_running:
                await update_status(
                    repo,
                    job_id,
                    "failed",
                    error_message=str(exc),
                    duration_seconds=duration_seconds,
                )

            return {
                "status": "failed",
                "job_id": str(job_id) if job_id is not None else None,
                "doc_id": doc_id,
                "source_path": str(path),
                "tenant_id": tenant_id,
                "error_message": str(exc),
                "duration_seconds": duration_seconds,
            }


@flow(name="ingest-directory")
async def ingest_directory(dir_path: str, tenant_id: str = "default") -> None:
    from tqdm import tqdm

    path = Path(dir_path)
    supported = [".pdf", ".html", ".md", ".docx"]
    files = sorted(f for f in path.rglob("*") if f.suffix in supported)

    progress = tqdm(files, desc="Ingesting", unit="file")
    for file in progress:
        progress.set_postfix_str(file.name)
        await ingest_document(str(file), tenant_id)


def _attach_tenant(documents: list[Document], tenant_id: str) -> list[Document]:
    return [
        Document(
            content=doc.content,
            metadata={**doc.metadata, "tenant_id": tenant_id},
        )
        for doc in documents
    ]
