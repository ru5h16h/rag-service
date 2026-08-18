from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "001_ingestion_jobs"
down_revision = None
branch_labels = None
depends_on = None


JOB_STATUS = postgresql.ENUM(
    "queued",
    "running",
    "done",
    "failed",
    name="job_status",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE TYPE job_status AS ENUM ('queued', 'running', 'done', 'failed')")
    op.create_table(
        "ingestion_jobs",
        sa.Column("job_id", sa.UUID(), primary_key=True),
        sa.Column("doc_id", sa.Text(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("tenant_id", sa.Text(), nullable=False, server_default="default"),
        sa.Column(
            "status",
            JOB_STATUS,
            nullable=False,
            server_default="queued",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=True),
        sa.Column("skipped_count", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("indexed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_jobs_tenant_status_created",
        "ingestion_jobs",
        ["tenant_id", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_tenant_status_created", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
    op.execute("DROP TYPE job_status")
