"""Add probability tables

Revision ID: 006
Revises: 005
Create Date: 2026-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Prediction markets table
    op.create_table(
        'prediction_markets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('external_id', sa.String(100), nullable=True, unique=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('market_probability', sa.Float, nullable=True),
        sa.Column('close_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_resolved', sa.Boolean, default=False),
        sa.Column('resolution', sa.String(10), nullable=True),
        sa.Column('explainer', sa.Text, nullable=True),
        sa.Column('investing_connection', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index('ix_prediction_markets_category', 'prediction_markets', ['category'])
    op.create_index('ix_prediction_markets_is_resolved', 'prediction_markets', ['is_resolved'])

    # User predictions table
    op.create_table(
        'user_predictions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('market_id', sa.String(36), sa.ForeignKey('prediction_markets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('predicted_probability', sa.Float, nullable=False),
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('brier_score', sa.Float, nullable=True),
        sa.Column('saw_market_price', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index('ix_user_predictions_user_id', 'user_predictions', ['user_id'])
    op.create_index('ix_user_predictions_market_id', 'user_predictions', ['market_id'])
    # Unique constraint handled via unique index for SQLite compatibility
    op.create_index('ix_user_predictions_user_market', 'user_predictions', ['user_id', 'market_id'], unique=True)

    # Calibration scores table
    op.create_table(
        'calibration_scores',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('total_predictions', sa.Integer, default=0),
        sa.Column('resolved_predictions', sa.Integer, default=0),
        sa.Column('average_brier_score', sa.Float, nullable=True),
        sa.Column('calibration_data', sa.JSON, nullable=True),
        sa.Column('detected_biases', sa.JSON, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('calibration_scores')
    op.drop_index('ix_user_predictions_user_market', 'user_predictions')
    op.drop_index('ix_user_predictions_market_id', 'user_predictions')
    op.drop_index('ix_user_predictions_user_id', 'user_predictions')
    op.drop_table('user_predictions')
    op.drop_index('ix_prediction_markets_is_resolved', 'prediction_markets')
    op.drop_index('ix_prediction_markets_category', 'prediction_markets')
    op.drop_table('prediction_markets')
