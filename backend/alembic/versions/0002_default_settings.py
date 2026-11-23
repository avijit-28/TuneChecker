"""0002_default_settings

Revision ID: 0002_default_settings
Revises: 0001_initial
Create Date: 2026-11-23

"""
import json
from alembic import op
import sqlalchemy as sa
from app.services.settings_service import DEFAULT_SETTINGS_CONFIG

revision = '0002_default_settings'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    settings_table = sa.table(
        'settings_versions',
        sa.column('version', sa.Integer),
        sa.column('sensitivity', sa.String),
        sa.column('config', sa.JSON),
        sa.column('source', sa.String),
    )
    op.bulk_insert(settings_table, [
        {
            'version': 1,
            'sensitivity': 'medium',
            'config': DEFAULT_SETTINGS_CONFIG,
            'source': 'default'
        }
    ])

    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE TRIGGER IF NOT EXISTS trg_settings_versions_no_delete BEFORE DELETE ON settings_versions
        BEGIN SELECT RAISE(ABORT, 'settings_versions rows cannot be deleted'); END;
    """))

def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_settings_versions_no_delete"))
    op.execute(sa.text("DELETE FROM settings_versions WHERE version = 1"))
