"""0001_initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-11-23

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. settings_versions
    op.create_table(
        'settings_versions',
        sa.Column('version', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('sensitivity', sa.String(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.CheckConstraint("sensitivity IN ('low','medium','high')", name="ck_settings_sensitivity"),
        sa.CheckConstraint("source IN ('default','user','reset')", name="ck_settings_source"),
    )

    # 2. calls
    op.create_table(
        'calls',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('storage_key', sa.String(), unique=True, nullable=True),
        sa.Column('audio_deleted_at', sa.DateTime(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), server_default='uploaded', nullable=False),
        sa.Column('failure_stage', sa.String(), nullable=True),
        sa.Column('failure_code', sa.String(), nullable=True),
        sa.Column('failure_message', sa.String(), nullable=True),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_synthetic', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.CheckConstraint("length(original_filename) BETWEEN 1 AND 255", name="ck_calls_filename_len"),
        sa.CheckConstraint("size_bytes > 0", name="ck_calls_size_bytes"),
        sa.CheckConstraint("duration_ms IS NULL OR duration_ms >= 0", name="ck_calls_duration_ms"),
        sa.CheckConstraint("status IN ('uploaded','validating','transcribing','analyzing','complete','partial','failed')", name="ck_calls_status"),
        sa.CheckConstraint("is_synthetic IN (0,1)", name="ck_calls_synthetic"),
        sa.CheckConstraint("(storage_key IS NOT NULL AND audio_deleted_at IS NULL) OR (storage_key IS NULL AND audio_deleted_at IS NOT NULL)", name="ck_calls_audio_storage"),
    )
    op.create_index('ix_calls_created_at', 'calls', [sa.text('created_at DESC')])
    op.create_index('ix_calls_status_locked', 'calls', ['status', 'locked_at'])

    # 3. stage_runs
    op.create_table(
        'stage_runs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('call_id', sa.String(), sa.ForeignKey('calls.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stage', sa.String(), nullable=False),
        sa.Column('attempt', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('result_summary', sa.String(), nullable=True),
        sa.Column('error_code', sa.String(), nullable=True),
        sa.UniqueConstraint('call_id', 'stage', 'attempt', name='uq_stage_runs_call_stage_attempt'),
        sa.CheckConstraint("stage IN ('validation','transcription','speaker_identification','tone_analysis','evidence_extraction','action_items','completion')", name="ck_stage_runs_stage"),
        sa.CheckConstraint("status IN ('running','succeeded','failed','skipped')", name="ck_stage_runs_status"),
        sa.CheckConstraint("attempt >= 1", name="ck_stage_runs_attempt"),
    )
    op.create_index('ix_stage_runs_call', 'stage_runs', ['call_id', 'stage'])

    # 4. transcripts
    op.create_table(
        'transcripts',
        sa.Column('call_id', sa.String(), sa.ForeignKey('calls.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_transcript_id', sa.String(), unique=True, nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('language', sa.String(), server_default='en', nullable=False),
        sa.Column('speaker_count', sa.Integer(), nullable=True),
        sa.Column('audio_seconds', sa.Float(), nullable=True),
        sa.Column('raw_response', sa.LargeBinary(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.CheckConstraint("status IN ('submitted','completed','failed')", name="ck_transcripts_status"),
    )

    # 5. speaker_roles
    op.create_table(
        'speaker_roles',
        sa.Column('call_id', sa.String(), sa.ForeignKey('calls.id', ondelete='CASCADE'), nullable=False),
        sa.Column('speaker_label', sa.String(), nullable=False),
        sa.Column('role', sa.String(), server_default='unknown', nullable=False),
        sa.Column('source', sa.String(), server_default='auto', nullable=False),
        sa.Column('status', sa.String(), server_default='unresolved', nullable=False),
        sa.Column('level', sa.String(), nullable=True),
        sa.Column('factors', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint('call_id', 'speaker_label'),
        sa.CheckConstraint("role IN ('sales_rep','customer','unknown')", name="ck_speaker_roles_role"),
        sa.CheckConstraint("source IN ('auto','user')", name="ck_speaker_roles_source"),
        sa.CheckConstraint("status IN ('unresolved','uncertain','confident','confirmed')", name="ck_speaker_roles_status"),
    )
    op.create_index('uq_speaker_roles_one_rep', 'speaker_roles', ['call_id'], unique=True, sqlite_where=sa.text("role = 'sales_rep'"))

    # 6. utterances
    op.create_table(
        'utterances',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('call_id', sa.String(), sa.ForeignKey('transcripts.call_id', ondelete='CASCADE'), nullable=False),
        sa.Column('idx', sa.Integer(), nullable=False),
        sa.Column('speaker_label', sa.String(), nullable=False),
        sa.Column('start_ms', sa.Integer(), nullable=False),
        sa.Column('end_ms', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('asr_confidence', sa.Float(), nullable=True),
        sa.Column('speaker_confidence', sa.Float(), nullable=True),
        sa.Column('low_attribution', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint('call_id', 'idx', name='uq_utterances_call_idx'),
        sa.UniqueConstraint('id', 'call_id', 'speaker_label', name='uq_utterances_id_call_speaker'),
        sa.CheckConstraint('end_ms >= start_ms', name='ck_utterances_ms_range'),
        sa.ForeignKeyConstraint(['call_id', 'speaker_label'], ['speaker_roles.call_id', 'speaker_roles.speaker_label'], ondelete='CASCADE'),
    )

    # 7. analyses
    op.create_table(
        'analyses',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('call_id', sa.String(), sa.ForeignKey('calls.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_number', sa.Integer(), nullable=False),
        sa.Column('settings_version', sa.Integer(), sa.ForeignKey('settings_versions.version', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('partial_reason', sa.String(), nullable=True),
        sa.Column('verdict', sa.String(), nullable=True),
        sa.Column('confidence_level', sa.String(), nullable=True),
        sa.Column('confidence_factors', sa.JSON(), nullable=True),
        sa.Column('limited_evidence_reason', sa.String(), nullable=True),
        sa.Column('explanation', sa.String(), nullable=True),
        sa.Column('rep_speaker_label', sa.String(), nullable=True),
        sa.Column('roles_source', sa.String(), nullable=True),
        sa.Column('dropped_evidence_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('dropped_details', sa.JSON(), nullable=True),
        sa.Column('model_name', sa.String(), nullable=True),
        sa.Column('prompt_version', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint('call_id', 'run_number', name='uq_analyses_call_run_number'),
        sa.UniqueConstraint('id', 'call_id', name='uq_analyses_id_call'),
        sa.UniqueConstraint('id', 'call_id', 'rep_speaker_label', name='uq_analyses_id_call_rep'),
        sa.CheckConstraint("status IN ('complete','partial')", name="ck_analyses_status"),
        sa.CheckConstraint("verdict IS NULL OR verdict IN ('RED','GREEN')", name="ck_analyses_verdict"),
    )
    op.create_index('ix_analyses_verdict', 'analyses', ['verdict', 'call_id'])
    op.create_index('ix_analyses_settings', 'analyses', ['settings_version'])

    # 8. evidence_items
    op.create_table(
        'evidence_items',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('analysis_id', sa.String(), sa.ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('call_id', sa.String(), nullable=False),
        sa.Column('ref', sa.String(), nullable=False),
        sa.Column('utterance_id', sa.String(), sa.ForeignKey('utterances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('speaker_label', sa.String(), nullable=False),
        sa.Column('quote', sa.String(), nullable=False),
        sa.Column('char_start', sa.Integer(), nullable=False),
        sa.Column('char_end', sa.Integer(), nullable=False),
        sa.Column('criterion_id', sa.String(), nullable=False),
        sa.Column('severity', sa.Integer(), nullable=False),
        sa.Column('rationale', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint('analysis_id', 'ref', name='uq_evidence_analysis_ref'),
        sa.CheckConstraint('char_end > char_start', name='ck_evidence_char_range'),
        sa.CheckConstraint('severity IN (1,2,3)', name='ck_evidence_severity'),
    )
    op.create_index('ix_evidence_analysis', 'evidence_items', ['analysis_id'])
    op.create_index('ix_evidence_utterance', 'evidence_items', ['utterance_id'])

    # 9. action_items
    op.create_table(
        'action_items',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('analysis_id', sa.String(), sa.ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('call_id', sa.String(), nullable=False),
        sa.Column('ref', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('task', sa.String(), nullable=False),
        sa.Column('modality', sa.String(), nullable=False),
        sa.Column('owner_text', sa.String(), nullable=True),
        sa.Column('owner_basis', sa.String(), server_default='none', nullable=False),
        sa.Column('deadline_text', sa.String(), nullable=True),
        sa.Column('utterance_id', sa.String(), sa.ForeignKey('utterances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('speaker_label', sa.String(), nullable=False),
        sa.Column('quote', sa.String(), nullable=False),
        sa.Column('char_start', sa.Integer(), nullable=False),
        sa.Column('char_end', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.UniqueConstraint('analysis_id', 'ref', name='uq_actions_analysis_ref'),
        sa.CheckConstraint('char_end > char_start', name='ck_actions_char_range'),
        sa.CheckConstraint("type IN ('commitment','follow_up','information_promised','customer_task')", name="ck_actions_type"),
        sa.CheckConstraint("modality IN ('definite','tentative')", name="ck_actions_modality"),
        sa.CheckConstraint("owner_basis IN ('explicit_name','explicit_role','committing_speaker','none')", name="ck_actions_owner_basis"),
    )
    op.create_index('ix_actions_analysis', 'action_items', ['analysis_id'])
    op.create_index('ix_actions_call', 'action_items', ['call_id'])
    op.create_index('ix_actions_utterance', 'action_items', ['utterance_id'])

    # Create SQLite Triggers
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE TRIGGER IF NOT EXISTS trg_evidence_quote_is_transcript_span BEFORE INSERT ON evidence_items
        WHEN (SELECT substr(text, NEW.char_start + 1, NEW.char_end - NEW.char_start)
                FROM utterances WHERE id = NEW.utterance_id) IS NOT NEW.quote
        BEGIN SELECT RAISE(ABORT, 'evidence quote is not the transcript span at the given offsets'); END;
    """))

    conn.execute(sa.text("""
        CREATE TRIGGER IF NOT EXISTS trg_action_quote_is_transcript_span BEFORE INSERT ON action_items
        WHEN (SELECT substr(text, NEW.char_start + 1, NEW.char_end - NEW.char_start)
                FROM utterances WHERE id = NEW.utterance_id) IS NOT NEW.quote
        BEGIN SELECT RAISE(ABORT, 'action-item quote is not the transcript span at the given offsets'); END;
    """))

    conn.execute(sa.text("""
        CREATE TRIGGER IF NOT EXISTS trg_settings_versions_no_update BEFORE UPDATE ON settings_versions
        BEGIN SELECT RAISE(ABORT, 'settings_versions rows are immutable'); END;
    """))

    conn.execute(sa.text("""
        CREATE TRIGGER IF NOT EXISTS trg_utterances_no_update BEFORE UPDATE ON utterances
        BEGIN SELECT RAISE(ABORT, 'utterances are immutable'); END;
    """))

    conn.execute(sa.text("""
        CREATE TRIGGER IF NOT EXISTS trg_analyses_no_update BEFORE UPDATE ON analyses
        BEGIN SELECT RAISE(ABORT, 'analyses are immutable; create a new run'); END;
    """))

def downgrade() -> None:
    op.drop_table('action_items')
    op.drop_table('evidence_items')
    op.drop_table('analyses')
    op.drop_table('utterances')
    op.drop_table('speaker_roles')
    op.drop_table('transcripts')
    op.drop_table('stage_runs')
    op.drop_table('calls')
    op.drop_table('settings_versions')
