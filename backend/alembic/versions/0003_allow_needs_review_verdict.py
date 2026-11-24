"""0003_allow_needs_review_verdict

Revision ID: 0003_allow_needs_review_verdict
Revises: 0002_default_settings
Create Date: 2026-11-24

"""
from alembic import op
import sqlalchemy as sa

revision = '0003_allow_needs_review_verdict'
down_revision = '0002_default_settings'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF;"))
    conn.execute(sa.text("""
        CREATE TABLE analyses_new (
            id VARCHAR NOT NULL, 
            call_id VARCHAR NOT NULL, 
            run_number INTEGER NOT NULL, 
            settings_version INTEGER NOT NULL, 
            status VARCHAR NOT NULL, 
            partial_reason VARCHAR, 
            verdict VARCHAR, 
            confidence_level VARCHAR, 
            confidence_factors JSON, 
            limited_evidence_reason VARCHAR, 
            explanation VARCHAR, 
            rep_speaker_label VARCHAR, 
            roles_source VARCHAR, 
            dropped_evidence_count INTEGER DEFAULT '0' NOT NULL, 
            dropped_details JSON, 
            model_name VARCHAR, 
            prompt_version VARCHAR, 
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
            PRIMARY KEY (id), 
            CONSTRAINT uq_analyses_call_run_number UNIQUE (call_id, run_number), 
            CONSTRAINT uq_analyses_id_call UNIQUE (id, call_id), 
            CONSTRAINT uq_analyses_id_call_rep UNIQUE (id, call_id, rep_speaker_label), 
            CONSTRAINT ck_analyses_status CHECK (status IN ('complete','partial')), 
            CONSTRAINT ck_analyses_verdict CHECK (verdict IS NULL OR verdict IN ('RED','GREEN','NEEDS_REVIEW')), 
            FOREIGN KEY(call_id) REFERENCES calls (id) ON DELETE CASCADE, 
            FOREIGN KEY(settings_version) REFERENCES settings_versions (version) ON DELETE RESTRICT
        );
    """))
    conn.execute(sa.text("INSERT INTO analyses_new SELECT * FROM analyses;"))
    conn.execute(sa.text("DROP TABLE analyses;"))
    conn.execute(sa.text("ALTER TABLE analyses_new RENAME TO analyses;"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_analyses_verdict ON analyses (verdict, call_id);"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_analyses_settings ON analyses (settings_version);"))
    conn.execute(sa.text("""
        CREATE TRIGGER IF NOT EXISTS trg_analyses_no_update BEFORE UPDATE ON analyses
        BEGIN SELECT RAISE(ABORT, 'analyses are immutable; create a new run'); END;
    """))
    conn.execute(sa.text("PRAGMA foreign_keys = ON;"))

def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys = OFF;"))
    conn.execute(sa.text("""
        CREATE TABLE analyses_old (
            id VARCHAR NOT NULL, 
            call_id VARCHAR NOT NULL, 
            run_number INTEGER NOT NULL, 
            settings_version INTEGER NOT NULL, 
            status VARCHAR NOT NULL, 
            partial_reason VARCHAR, 
            verdict VARCHAR, 
            confidence_level VARCHAR, 
            confidence_factors JSON, 
            limited_evidence_reason VARCHAR, 
            explanation VARCHAR, 
            rep_speaker_label VARCHAR, 
            roles_source VARCHAR, 
            dropped_evidence_count INTEGER DEFAULT '0' NOT NULL, 
            dropped_details JSON, 
            model_name VARCHAR, 
            prompt_version VARCHAR, 
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
            PRIMARY KEY (id), 
            CONSTRAINT uq_analyses_call_run_number UNIQUE (call_id, run_number), 
            CONSTRAINT uq_analyses_id_call UNIQUE (id, call_id), 
            CONSTRAINT uq_analyses_id_call_rep UNIQUE (id, call_id, rep_speaker_label), 
            CONSTRAINT ck_analyses_status CHECK (status IN ('complete','partial')), 
            CONSTRAINT ck_analyses_verdict CHECK (verdict IS NULL OR verdict IN ('RED','GREEN')), 
            FOREIGN KEY(call_id) REFERENCES calls (id) ON DELETE CASCADE, 
            FOREIGN KEY(settings_version) REFERENCES settings_versions (version) ON DELETE RESTRICT
        );
    """))
    conn.execute(sa.text("INSERT INTO analyses_old SELECT * FROM analyses;"))
    conn.execute(sa.text("DROP TABLE analyses;"))
    conn.execute(sa.text("ALTER TABLE analyses_old RENAME TO analyses;"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_analyses_verdict ON analyses (verdict, call_id);"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_analyses_settings ON analyses (settings_version);"))
    conn.execute(sa.text("""
        CREATE TRIGGER IF NOT EXISTS trg_analyses_no_update BEFORE UPDATE ON analyses
        BEGIN SELECT RAISE(ABORT, 'analyses are immutable; create a new run'); END;
    """))
    conn.execute(sa.text("PRAGMA foreign_keys = ON;"))
