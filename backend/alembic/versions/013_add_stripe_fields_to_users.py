"""Add stripe fields to users

Revision ID: 013
Revises: 012
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('tier', sa.String(length=20), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users')
    op.drop_column('users', 'stripe_customer_id')
    op.drop_column('users', 'tier')
