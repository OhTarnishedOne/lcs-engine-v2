"""Add trading tables

Revision ID: 005
Revises: 004
Create Date: 2026-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'trade_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alpaca_order_id', sa.String(100), nullable=True),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('side', sa.String(10), nullable=False),
        sa.Column('qty', sa.Float, nullable=False),
        sa.Column('order_type', sa.String(20), nullable=False),
        sa.Column('limit_price', sa.Float, nullable=True),
        sa.Column('filled_price', sa.Float, nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index('ix_trade_logs_user_id', 'trade_logs', ['user_id'])
    op.create_index('ix_trade_logs_symbol', 'trade_logs', ['symbol'])
    op.create_index('ix_trade_logs_strategy_id', 'trade_logs', ['strategy_id'])


def downgrade() -> None:
    op.drop_index('ix_trade_logs_strategy_id', 'trade_logs')
    op.drop_index('ix_trade_logs_symbol', 'trade_logs')
    op.drop_index('ix_trade_logs_user_id', 'trade_logs')
    op.drop_table('trade_logs')
