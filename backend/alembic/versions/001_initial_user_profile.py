"""Initial user and profile tables

Revision ID: 001
Revises:
Create Date: 2024-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('risk_tolerance', sa.String(20), nullable=True),
        sa.Column('investment_horizon', sa.String(20), nullable=True),
        sa.Column('experience_level', sa.String(20), nullable=True),
        sa.Column('goals', sa.JSON(), nullable=True),
        sa.Column('interests', sa.JSON(), nullable=True),
        sa.Column('onboarding_complete', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('profiles')
    op.drop_table('users')
