"""Add onboarding progress columns

Revision ID: 007
Revises: 006
Create Date: 2026-02-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_profiles', sa.Column('current_section', sa.Integer, server_default='1'))
    op.add_column('user_profiles', sa.Column('recommended_path', sa.String(50)))

    # Backfill existing rows
    op.execute("UPDATE user_profiles SET current_section = 1 WHERE current_section IS NULL")


def downgrade() -> None:
    op.drop_column('user_profiles', 'recommended_path')
    op.drop_column('user_profiles', 'current_section')
