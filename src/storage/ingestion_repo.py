from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.pg_client import ingestion_jobs

JobStatus = Literal["queued", "running", "done", "failed"]

VALID_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    "queued": {"running"},
    "running": {"done", "failed"},
    "done": set(),
    "failed": set(),
}


class IngestionRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(self, doc_id: str, source_path: str, tenant_id: str) -> uuid.UUID:
        """Insert a queued ingestion job and return its job ID."""
        job_id = uuid.uuid4()
        statement = ingestion_jobs.insert().values(
            job_id=job_id,
            doc_id=doc_id,
            source_path=source_path,
            tenant_id=tenant_id,
            status="queued",
        )
        await self.session.execute(statement)
        await self.session.commit()
        return job_id

    async def update_status(
        self,
        job_id: uuid.UUID,
        status: JobStatus,
        *,
        error_message: str | None = None,
        chunk_count: int | None = None,
        skipped_count: int | None = None,
        duration_seconds: float | None = None,
    ) -> None:
        """Update job status when the requested state transition is valid."""
        current = await self.get_by_job_id(job_id)
        if current is None:
            msg = f"ingestion job not found: {job_id}"
            raise ValueError(msg)

        current_status = current["status"]
        if not _is_job_status(current_status) or status not in VALID_TRANSITIONS[current_status]:
            msg = f"invalid job status transition: {current_status} -> {status}"
            raise ValueError(msg)

        values: dict[str, Any] = {
            "status": status,
            "error_message": error_message,
            "chunk_count": chunk_count,
            "skipped_count": skipped_count,
            "duration_seconds": duration_seconds,
        }
        if status == "done":
            values["indexed_at"] = datetime.now(UTC)

        statement = (
            ingestion_jobs.update().where(ingestion_jobs.c.job_id == job_id).values(**values)
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def get_by_job_id(self, job_id: uuid.UUID) -> dict[str, Any] | None:
        """Return a job as a plain dict, or None when it does not exist."""
        statement = sa.select(ingestion_jobs).where(ingestion_jobs.c.job_id == job_id)
        result = await self.session.execute(statement)
        row = result.mappings().one_or_none()
        return dict(row) if row is not None else None

    async def list_recent(self, tenant_id: str, limit: int = 50) -> list[dict[str, Any]]:
        statement = (
            sa.select(ingestion_jobs)
            .where(ingestion_jobs.c.tenant_id == tenant_id)
            .order_by(ingestion_jobs.c.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return [dict(row) for row in result.mappings().all()]


def _is_job_status(value: object) -> bool:
    return value in VALID_TRANSITIONS
