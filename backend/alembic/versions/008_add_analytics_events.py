"""Add analytics_events table

Revision ID: 008
Revises: 007
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('event_name', sa.String(50), nullable=False),
        sa.Column('event_properties', sa.JSON, nullable=True),
        sa.Column('path', sa.String(500), nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_analytics_events_event_name', 'analytics_events', ['event_name'])
    op.create_index('ix_analytics_events_user_id', 'analytics_events', ['user_id'])
    op.create_index('ix_analytics_events_created_at', 'analytics_events', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_analytics_events_created_at', table_name='analytics_events')
    op.drop_index('ix_analytics_events_user_id', table_name='analytics_events')
    op.drop_index('ix_analytics_events_event_name', table_name='analytics_events')
    op.drop_table('analytics_events')
