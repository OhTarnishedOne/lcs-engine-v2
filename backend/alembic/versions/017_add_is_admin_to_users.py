"""Add is_admin to users and set rico@lcsengine.com as admin

Revision ID: 017
Revises: 016
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '017'
down_revision: Union[str, None] = '016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    # Set founder as admin
    op.execute("UPDATE users SET is_admin = true WHERE email = 'rico@lcsengine.com'")
    op.execute("UPDATE users SET is_admin = true WHERE email = 'ricorobertsjr@gmail.com'")


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
