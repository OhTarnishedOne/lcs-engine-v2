"""Add conversation-derived fields to user_profiles

Revision ID: 010
Revises: 009
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_profiles', sa.Column('motivation', sa.Text, nullable=True))
    op.add_column('user_profiles', sa.Column('life_context', sa.Text, nullable=True))
    op.add_column('user_profiles', sa.Column('emotional_relationship', sa.Text, nullable=True))
    op.add_column('user_profiles', sa.Column('goals', sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column('user_profiles', 'goals')
    op.drop_column('user_profiles', 'emotional_relationship')
    op.drop_column('user_profiles', 'life_context')
    op.drop_column('user_profiles', 'motivation')
