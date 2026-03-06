"""Add tap_responses JSON column to user_profiles

Revision ID: 011
Revises: 010
Create Date: 2026-03-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_profiles', sa.Column('tap_responses', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('user_profiles', 'tap_responses')
