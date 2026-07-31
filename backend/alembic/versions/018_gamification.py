"""Add gamification tables

Revision ID: 018_gamification
Revises: 017
Create Date: 2026-07-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '018_gamification'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DECISION_DOMAIN = (
    'investing', 'career', 'personal_finance', 'business', 'life',
)
DECISION_STATUS = ('pending', 'resolved', 'expired', 'cancelled')
OUTCOME_SOURCE = ('auto_market', 'self_reported')
TIER_LEVEL = ('instinctive', 'reflective', 'calibrated', 'strategic', 'architect')
BADGE_SLUG = (
    'first_call', 'what_would_change', 'process_builder', 'seven_day_streak',
    'thirty_day_streak',
    'calibrated_run', 'stayed_calibrated_drawdown',
    'good_loser', 'humble_winner', 'avoided_revenge', 'revised_thesis',
    'bias_corrected', 'loop_closed', 'skill_transferred', 'stable_under_pressure',
)

# postgresql.ENUM required — sa.Enum ignores create_type=False and re-emits CREATE TYPE.
decisiondomain_enum = postgresql.ENUM(*DECISION_DOMAIN, name='decisiondomain', create_type=False)
decisionstatus_enum = postgresql.ENUM(*DECISION_STATUS, name='decisionstatus', create_type=False)
outcomesource_enum = postgresql.ENUM(*OUTCOME_SOURCE, name='outcomesource', create_type=False)
tierlevel_enum = postgresql.ENUM(*TIER_LEVEL, name='tierlevel', create_type=False)
badgeslug_enum = postgresql.ENUM(*BADGE_SLUG, name='badgeslug', create_type=False)


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE decisiondomain AS ENUM ('investing', 'career', 'personal_finance', 'business', 'life');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE decisionstatus AS ENUM ('pending', 'resolved', 'expired', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE outcomesource AS ENUM ('auto_market', 'self_reported');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE tierlevel AS ENUM ('instinctive', 'reflective', 'calibrated', 'strategic', 'architect');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE badgeslug AS ENUM ('first_call', 'what_would_change', 'process_builder', 'seven_day_streak', 'thirty_day_streak', 'calibrated_run', 'stayed_calibrated_drawdown', 'good_loser', 'humble_winner', 'avoided_revenge', 'revised_thesis', 'bias_corrected', 'loop_closed', 'skill_transferred', 'stable_under_pressure');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.create_table(
        'curated_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column(
            'domain',
            decisiondomain_enum,
            nullable=False,
        ),
        sa.Column('resolution_type', sa.String(length=50), nullable=True),
        sa.Column('resolution_ticker', sa.String(length=20), nullable=True),
        sa.Column('resolution_condition', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('active_from', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_outcome', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_curated_questions_domain', 'curated_questions', ['domain'])
    op.create_index('ix_curated_questions_is_active', 'curated_questions', ['is_active'])

    op.create_table(
        'decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column(
            'domain',
            decisiondomain_enum,
            nullable=False,
        ),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('falsification', sa.Text(), nullable=True),
        sa.Column('resolution_date', sa.DateTime(), nullable=True),
        sa.Column('is_curated', sa.Boolean(), server_default=sa.text('false')),
        sa.Column(
            'question_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('curated_questions.id'),
            nullable=True,
        ),
        sa.Column(
            'status',
            decisionstatus_enum,
            nullable=False,
            server_default='pending',
        ),
        sa.Column('locked_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('outcome_binary', sa.Boolean(), nullable=True),
        sa.Column(
            'outcome_source',
            outcomesource_enum,
            nullable=True,
        ),
        sa.Column('outcome_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('brier_score', sa.Float(), nullable=True),
        sa.Column('calibration_delta', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('extra', postgresql.JSONB(), nullable=True),
        sa.CheckConstraint(
            'confidence >= 0.0 AND confidence <= 1.0',
            name='confidence_range',
        ),
    )
    op.create_index('ix_decisions_user_id', 'decisions', ['user_id'])
    op.create_index('ix_decisions_status', 'decisions', ['status'])
    op.create_index('ix_decisions_domain', 'decisions', ['domain'])
    op.create_index('ix_decisions_locked_at', 'decisions', ['locked_at'])

    op.create_table(
        'decision_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'decision_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('decisions.id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('outcome_attribution', sa.Text(), nullable=True),
        sa.Column('was_process_sound', sa.Boolean(), nullable=True),
        sa.Column('identified_bias', sa.Text(), nullable=True),
        sa.Column('luck_vs_process', sa.String(length=20), nullable=True),
        sa.Column('thesis_revised', sa.Boolean(), server_default=sa.text('false')),
        sa.Column(
            'self_flagged_bias_before_ai',
            sa.Boolean(),
            server_default=sa.text('false'),
        ),
        sa.Column('reflection_points', sa.Integer(), server_default=sa.text('0')),
        sa.Column('triggers_good_loser', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('triggers_humble_winner', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('triggers_avoided_revenge', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_reviews_user_id', 'decision_reviews', ['user_id'])
    op.create_index('ix_reviews_decision_id', 'decision_reviews', ['decision_id'])

    op.create_table(
        'user_gamification_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
        ),
        sa.Column('process_score', sa.Float(), server_default=sa.text('0.0')),
        sa.Column('calibration_score', sa.Float(), nullable=True),
        sa.Column('reflection_score', sa.Float(), nullable=True),
        sa.Column('improvement_score', sa.Float(), nullable=True),
        sa.Column('lcs_score', sa.Float(), server_default=sa.text('0.0')),
        sa.Column(
            'tier',
            tierlevel_enum,
            server_default='instinctive',
        ),
        sa.Column('tier_updated_at', sa.DateTime(), nullable=True),
        sa.Column('total_points', sa.Integer(), server_default=sa.text('0')),
        sa.Column('logging_streak_days', sa.Integer(), server_default=sa.text('0')),
        sa.Column('logging_streak_last_date', sa.DateTime(), nullable=True),
        sa.Column('grace_days_used', sa.Integer(), server_default=sa.text('0')),
        sa.Column('grace_days_reset_at', sa.DateTime(), nullable=True),
        sa.Column('calibration_streak', sa.Integer(), server_default=sa.text('0')),
        sa.Column('review_streak', sa.Integer(), server_default=sa.text('0')),
        sa.Column('total_calls', sa.Integer(), server_default=sa.text('0')),
        sa.Column('resolved_calls', sa.Integer(), server_default=sa.text('0')),
        sa.Column('calibrated_calls', sa.Integer(), server_default=sa.text('0')),
        sa.Column('reviewed_calls', sa.Integer(), server_default=sa.text('0')),
        sa.Column('known_biases', postgresql.JSONB(), nullable=True),
        sa.Column('stable_under_pressure', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('stable_under_pressure_earned_at', sa.DateTime(), nullable=True),
        sa.Column(
            'domains_unlocked',
            postgresql.JSONB(),
            server_default=sa.text("'[\"investing\"]'::jsonb"),
        ),
        sa.Column('last_trend_bonus_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        'ix_gamification_profiles_user_id',
        'user_gamification_profiles',
        ['user_id'],
    )
    op.create_index(
        'ix_gamification_profiles_tier',
        'user_gamification_profiles',
        ['tier'],
    )

    op.create_table(
        'user_score_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('process_score', sa.Float(), server_default=sa.text('0.0')),
        sa.Column('calibration_score', sa.Float(), server_default=sa.text('0.0')),
        sa.Column('reflection_score', sa.Float(), server_default=sa.text('0.0')),
        sa.Column('improvement_score', sa.Float(), server_default=sa.text('0.0')),
        sa.Column('lcs_score', sa.Float(), server_default=sa.text('0.0')),
        sa.Column(
            'tier',
            tierlevel_enum,
            server_default='instinctive',
        ),
        sa.Column('total_calls', sa.Integer(), server_default=sa.text('0')),
        sa.Column('resolved_calls', sa.Integer(), server_default=sa.text('0')),
        sa.Column('reviewed_calls', sa.Integer(), server_default=sa.text('0')),
        sa.Column('domain_scores', postgresql.JSONB(), nullable=True),
        sa.Column('rolling_brier', sa.Float(), nullable=True),
        sa.Column(
            'triggered_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('decisions.id'),
            nullable=True,
        ),
        sa.Column('snapshot_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_snapshots_user_id', 'user_score_snapshots', ['user_id'])
    op.create_index('ix_snapshots_snapshot_at', 'user_score_snapshots', ['snapshot_at'])

    op.create_table(
        'user_badges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'badge_slug',
            badgeslug_enum,
            nullable=False,
        ),
        sa.Column(
            'triggered_by_decision_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('decisions.id'),
            nullable=True,
        ),
        sa.Column(
            'triggered_by_review_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('decision_reviews.id'),
            nullable=True,
        ),
        sa.Column('points_awarded', sa.Integer(), server_default=sa.text('0')),
        sa.Column('earned_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        'ix_user_badges_user_badge',
        'user_badges',
        ['user_id', 'badge_slug'],
        unique=True,
    )

    op.create_table(
        'points_ledger',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column(
            'decision_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('decisions.id'),
            nullable=True,
        ),
        sa.Column(
            'review_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('decision_reviews.id'),
            nullable=True,
        ),
        sa.Column(
            'badge_slug',
            badgeslug_enum,
            nullable=True,
        ),
        sa.Column('running_total', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_points_ledger_user_id', 'points_ledger', ['user_id'])
    op.create_index('ix_points_ledger_created_at', 'points_ledger', ['created_at'])

    op.create_table(
        'ai_tutor_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'decision_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('decisions.id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
        ),
        sa.Column('bias_flagged', sa.String(length=100), nullable=True),
        sa.Column('bias_severity', sa.Float(), nullable=True),
        sa.Column('clarifying_question', sa.Text(), nullable=True),
        sa.Column('user_responded', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('points_awarded', sa.Integer(), server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'insight_loops',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('bias_name', sa.String(length=100), nullable=False),
        sa.Column(
            'domain',
            decisiondomain_enum,
            nullable=False,
        ),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('improved_at', sa.DateTime(), nullable=True),
        sa.Column('pre_bias_score', sa.Float(), nullable=True),
        sa.Column('post_bias_score', sa.Float(), nullable=True),
        sa.Column('improvement_delta', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='detected'),
        sa.Column('points_awarded', sa.Integer(), server_default=sa.text('0')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_insight_loops_user_id', 'insight_loops', ['user_id'])
    op.create_index('ix_insight_loops_status', 'insight_loops', ['status'])


def downgrade() -> None:
    op.drop_table('insight_loops')
    op.drop_table('ai_tutor_sessions')
    op.drop_table('points_ledger')
    op.drop_table('user_badges')
    op.drop_table('user_score_snapshots')
    op.drop_table('user_gamification_profiles')
    op.drop_table('decision_reviews')
    op.drop_table('decisions')
    op.drop_table('curated_questions')

    op.execute('DROP TYPE IF EXISTS badgeslug')
    op.execute('DROP TYPE IF EXISTS tierlevel')
    op.execute('DROP TYPE IF EXISTS outcomesource')
    op.execute('DROP TYPE IF EXISTS decisionstatus')
    op.execute('DROP TYPE IF EXISTS decisiondomain')
