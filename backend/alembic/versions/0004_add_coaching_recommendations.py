"""0004_add_coaching_recommendations

Revision ID: 0004_add_coaching_recommendations
Revises: 0003_allow_needs_review_verdict
Create Date: 2026-11-24

"""
from alembic import op
import sqlalchemy as sa

revision = '0004_add_coaching_recommendations'
down_revision = '0003_allow_needs_review_verdict'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'coaching_recommendations',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('analysis_id', sa.String(), sa.ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('call_id', sa.String(), sa.ForeignKey('calls.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ref', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=False),
        sa.Column('context_quote', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(), server_default='suggestion', nullable=False),
        sa.Column('utterance_id', sa.String(), sa.ForeignKey('utterances.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint('analysis_id', 'ref', name='uq_coaching_analysis_ref'),
        sa.CheckConstraint("severity IN ('suggestion', 'important', 'critical')", name='ck_coaching_severity')
    )
    op.create_index('ix_coaching_analysis', 'coaching_recommendations', ['analysis_id'])
    op.create_index('ix_coaching_call', 'coaching_recommendations', ['call_id'])
    op.create_index('ix_coaching_utterance', 'coaching_recommendations', ['utterance_id'])

def downgrade() -> None:
    op.drop_table('coaching_recommendations')
