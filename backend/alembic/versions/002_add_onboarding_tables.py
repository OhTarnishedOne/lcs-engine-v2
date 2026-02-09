"""Add onboarding tables (user_profiles, onboarding_responses)

Revision ID: 002
Revises: 001
Create Date: 2024-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User profiles - extended onboarding data
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),

        # Section 1: Where They Are
        sa.Column('experience_level', sa.String(20), nullable=True),
        sa.Column('current_situation', sa.String(20), nullable=True),
        sa.Column('has_investment_account', sa.Boolean(), nullable=True),
        sa.Column('has_retirement_account', sa.Boolean(), nullable=True),

        # Section 2: What's Holding Them Back
        sa.Column('barriers', sa.JSON(), nullable=True),
        sa.Column('biggest_barrier', sa.String(50), nullable=True),

        # Section 3: What They Want
        sa.Column('primary_goal', sa.String(30), nullable=True),
        sa.Column('specific_goal_description', sa.Text(), nullable=True),
        sa.Column('time_horizon', sa.String(20), nullable=True),

        # Section 4: Risk & Comfort
        sa.Column('risk_tolerance', sa.String(20), nullable=True),
        sa.Column('loss_reaction', sa.String(20), nullable=True),
        sa.Column('monthly_investable', sa.String(20), nullable=True),

        # Section 5: Learning Style
        sa.Column('learning_preference', sa.String(20), nullable=True),
        sa.Column('time_commitment', sa.String(20), nullable=True),
        sa.Column('interests', sa.JSON(), nullable=True),

        # Derived / Computed
        sa.Column('persona', sa.String(50), nullable=True),
        sa.Column('persona_description', sa.Text(), nullable=True),

        # Status
        sa.Column('onboarding_completed', sa.Boolean(), default=False),
        sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Onboarding responses - individual question responses for analytics
    op.create_table(
        'onboarding_responses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),

        sa.Column('question_key', sa.String(50), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('answer_value', sa.Text(), nullable=False),
        sa.Column('answer_display', sa.Text(), nullable=False),

        sa.Column('section', sa.Integer(), nullable=False),
        sa.Column('question_order', sa.Integer(), nullable=False),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create indexes
    op.create_index('ix_user_profiles_user_id', 'user_profiles', ['user_id'])
    op.create_index('ix_onboarding_responses_user_id', 'onboarding_responses', ['user_id'])
    op.create_index('ix_onboarding_responses_question_key', 'onboarding_responses', ['question_key'])


def downgrade() -> None:
    op.drop_index('ix_onboarding_responses_question_key', 'onboarding_responses')
    op.drop_index('ix_onboarding_responses_user_id', 'onboarding_responses')
    op.drop_index('ix_user_profiles_user_id', 'user_profiles')
    op.drop_table('onboarding_responses')
    op.drop_table('user_profiles')
