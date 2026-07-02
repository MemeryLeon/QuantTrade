"""create job runs

Revision ID: 20260702_0001
Revises:
Create Date: 2026-07-02
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260702_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("queue_name", sa.String(length=64), nullable=False),
        sa.Column("task_name", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("artifact_uri", sa.String(length=512), nullable=True),
        sa.Column("operator_id", sa.String(length=64), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("max_retries >= 0"),
        sa.CheckConstraint("progress_percent >= 0 AND progress_percent <= 100"),
        sa.CheckConstraint("retry_count >= 0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_runs_queue_name", "job_runs", ["queue_name"])
    op.create_index("ix_job_runs_state", "job_runs", ["state"])


def downgrade() -> None:
    op.drop_index("ix_job_runs_state", table_name="job_runs")
    op.drop_index("ix_job_runs_queue_name", table_name="job_runs")
    op.drop_table("job_runs")
