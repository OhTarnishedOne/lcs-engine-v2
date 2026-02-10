"""Add strategy tables

Revision ID: 004
Revises: 003
Create Date: 2024-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Strategies table
    op.create_table(
        'strategies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('strategy_type', sa.String(50), nullable=False),
        sa.Column('risk_level', sa.Integer(), nullable=False),
        sa.Column('time_horizon', sa.String(50), nullable=False),
        sa.Column('assets', sa.JSON(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('risks', sa.Text(), nullable=False),
        sa.Column('learning_points', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Strategy comparisons table
    op.create_table(
        'strategy_comparisons',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strategy_ids', sa.JSON(), nullable=False),
        sa.Column('comparison_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create indexes
    op.create_index('ix_strategies_user_id', 'strategies', ['user_id'])
    op.create_index('ix_strategies_strategy_type', 'strategies', ['strategy_type'])
    op.create_index('ix_strategies_created_at', 'strategies', ['created_at'])
    op.create_index('ix_strategy_comparisons_user_id', 'strategy_comparisons', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_strategy_comparisons_user_id', 'strategy_comparisons')
    op.drop_index('ix_strategies_created_at', 'strategies')
    op.drop_index('ix_strategies_strategy_type', 'strategies')
    op.drop_index('ix_strategies_user_id', 'strategies')
    op.drop_table('strategy_comparisons')
    op.drop_table('strategies')
