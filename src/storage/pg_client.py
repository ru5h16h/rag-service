from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings

metadata = sa.MetaData()

job_status_enum = sa.Enum(
    "queued",
    "running",
    "done",
    "failed",
    name="job_status",
)

ingestion_jobs = sa.Table(
    "ingestion_jobs",
    metadata,
    sa.Column("job_id", sa.UUID(), primary_key=True),
    sa.Column("doc_id", sa.Text(), nullable=False),
    sa.Column("source_path", sa.Text(), nullable=False),
    sa.Column("tenant_id", sa.Text(), nullable=False, server_default="default"),
    sa.Column("status", job_status_enum, nullable=False, server_default="queued"),
    sa.Column("error_message", sa.Text(), nullable=True),
    sa.Column("chunk_count", sa.Integer(), nullable=True),
    sa.Column("skipped_count", sa.Integer(), nullable=True),
    sa.Column("duration_seconds", sa.Float(), nullable=True),
    sa.Column("indexed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column(
        "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")
    ),
)

sa.Index(
    "ix_jobs_tenant_status_created",
    ingestion_jobs.c.tenant_id,
    ingestion_jobs.c.status,
    ingestion_jobs.c.created_at,
)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.pg_dsn, pool_pre_ping=True)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session
