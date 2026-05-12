"""Add guest session fields to users

Revision ID: 015
Revises: 014
Create Date: 2026-05-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '015'
down_revision: Union[str, None] = '014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_guest', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('guest_created_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('guest_expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'guest_expires_at')
    op.drop_column('users', 'guest_created_at')
    op.drop_column('users', 'is_guest')
