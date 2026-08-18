from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.storage.ingestion_repo import IngestionRepo


class _MappingResult:
    def __init__(
        self,
        *,
        one: dict[str, Any] | None = None,
        all_rows: list[dict[str, Any]] | None = None,
    ) -> None:
        self.one = one
        self.all_rows = all_rows or []

    def mappings(self) -> _MappingResult:
        return self

    def one_or_none(self) -> dict[str, Any] | None:
        return self.one

    def all(self) -> list[dict[str, Any]]:
        return self.all_rows


def _job(job_id: uuid.UUID, status: str = "queued") -> dict[str, Any]:
    return {
        "job_id": job_id,
        "doc_id": "doc-1",
        "source_path": "/tmp/doc.pdf",
        "tenant_id": "tenant-a",
        "status": status,
        "created_at": datetime(2026, 1, 1),
    }


async def test_create_job_inserts_queued_job() -> None:
    session = AsyncMock()
    repo = IngestionRepo(session)

    job_id = await repo.create_job("doc-1", "/tmp/doc.pdf", "tenant-a")

    assert isinstance(job_id, uuid.UUID)
    session.execute.assert_awaited_once()
    session.commit.assert_awaited_once()


async def test_update_status_allows_valid_transition() -> None:
    job_id = uuid.uuid4()
    session = AsyncMock()
    session.execute.side_effect = [_MappingResult(one=_job(job_id, "running")), _MappingResult()]
    repo = IngestionRepo(session)

    await repo.update_status(
        job_id,
        "done",
        chunk_count=8,
        skipped_count=2,
        duration_seconds=1.25,
    )

    assert session.execute.await_count == 2
    session.commit.assert_awaited_once()


async def test_update_status_rejects_invalid_transition() -> None:
    job_id = uuid.uuid4()
    session = AsyncMock()
    session.execute.return_value = _MappingResult(one=_job(job_id, "done"))
    repo = IngestionRepo(session)

    with pytest.raises(ValueError, match="invalid job status transition: done -> running"):
        await repo.update_status(job_id, "running")

    session.commit.assert_not_called()


async def test_update_status_rejects_missing_job() -> None:
    session = AsyncMock()
    session.execute.return_value = _MappingResult(one=None)
    repo = IngestionRepo(session)

    with pytest.raises(ValueError, match="ingestion job not found"):
        await repo.update_status(uuid.uuid4(), "running")

    session.commit.assert_not_called()


async def test_get_by_job_id_returns_none_for_missing_job() -> None:
    session = AsyncMock()
    session.execute.return_value = _MappingResult(one=None)
    repo = IngestionRepo(session)

    assert await repo.get_by_job_id(uuid.uuid4()) is None


async def test_list_recent_returns_job_dicts() -> None:
    job_id = uuid.uuid4()
    session = AsyncMock()
    session.execute.return_value = _MappingResult(all_rows=[_job(job_id, "queued")])
    repo = IngestionRepo(session)

    jobs = await repo.list_recent("tenant-a")

    assert jobs == [_job(job_id, "queued")]
