"""Add user_training_interventions table

Revision ID: 019_interventions
Revises: 018_gamification
Create Date: 2026-08-10

Portable by design: status/type/slug are plain String columns (mirroring
InsightLoop.status), so this migration runs identically on PostgreSQL and
SQLite — no native-enum DDL like 018 required.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "019_interventions"
down_revision: Union[str, None] = "018_gamification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_training_interventions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("weakness_slug", sa.String(length=50), nullable=False),
        sa.Column("intervention_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_count", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("progress_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "baseline_qualifying_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("metric_key", sa.String(length=50), nullable=True),
        sa.Column("baseline_metric", sa.Float(), nullable=True),
        sa.Column("post_metric", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_interventions_user_id", "user_training_interventions", ["user_id"]
    )
    op.create_index(
        "ix_interventions_user_status",
        "user_training_interventions",
        ["user_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_interventions_user_status", table_name="user_training_interventions")
    op.drop_index("ix_interventions_user_id", table_name="user_training_interventions")
    op.drop_table("user_training_interventions")
