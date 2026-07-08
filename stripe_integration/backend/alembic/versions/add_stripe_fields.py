"""add tier and stripe_customer_id to users

Revision ID: add_stripe_fields
Revises: (replace with your current head revision ID)
Create Date: 2026-04-10
"""
from alembic import op
import sqlalchemy as sa

revision = "add_stripe_fields"
down_revision = None  # ← replace with your current head: run `alembic heads` to find it
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "tier",
            sa.String(20),
            nullable=False,
            server_default="free",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "stripe_customer_id",
            sa.String(100),
            nullable=True,
            unique=True,
        ),
    )
    op.create_index("ix_users_stripe_customer_id", "users", ["stripe_customer_id"])


def downgrade():
    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_column("users", "stripe_customer_id")
    op.drop_column("users", "tier")
