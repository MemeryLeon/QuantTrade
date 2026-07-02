"""create data snapshots

Revision ID: 20260702_0002
Revises: 20260702_0001
Create Date: 2026-07-02
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260702_0002"
down_revision: str | None = "20260702_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("market", sa.String(length=32), nullable=False),
        sa.Column("instrument_scope", sa.Text(), nullable=False),
        sa.Column("resolution", sa.String(length=32), nullable=False),
        sa.Column("adjustment", sa.String(length=32), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("calendar_version", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("object_uri", sa.String(length=1024), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("row_count", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("row_count >= 0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_snapshots_market", "data_snapshots", ["market"])
    op.create_index("ix_data_snapshots_source_id", "data_snapshots", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_data_snapshots_source_id", table_name="data_snapshots")
    op.drop_index("ix_data_snapshots_market", table_name="data_snapshots")
    op.drop_table("data_snapshots")

