import time
import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.calls import Call
from app.db.models.stage_runs import StageRun
from app.pipeline.stages.validation import run_validation_stage
from app.pipeline.stages.transcription import run_transcription_stage
from app.pipeline.stages.speaker_roles import run_speaker_roles_stage
from app.pipeline.stages.tone_analysis import run_tone_stage
from app.pipeline.stages.evidence_extraction import run_evidence_extraction_stage
from app.pipeline.stages.action_items import run_action_items_stage
from app.pipeline.stages.completion import run_completion_stage
from app.utils.errors import AppError

logger = logging.getLogger("tunechecker.pipeline")

STAGES = [
    ("validation", run_validation_stage, "validating"),
    ("transcription", run_transcription_stage, "transcribing"),
    ("speaker_identification", run_speaker_roles_stage, "analyzing"),
    ("tone_analysis", run_tone_stage, "analyzing"),
    ("evidence_extraction", run_evidence_extraction_stage, "analyzing"),
    ("action_items", run_action_items_stage, "analyzing"),
    ("completion", run_completion_stage, "complete"),
]

def run_pipeline_for_call(call_id: str, start_stage: str = "validation"):
    db: Session = SessionLocal()
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        db.close()
        return

    # Check whether to skip stages before start_stage
    stage_names = [s[0] for s in STAGES]
    start_idx = stage_names.index(start_stage) if start_stage in stage_names else 0

    try:
        for idx in range(start_idx, len(STAGES)):
            stage_name, stage_fn, call_status_val = STAGES[idx]
            
            # Update call status
            call.status = call_status_val
            call.locked_at = datetime.utcnow()
            db.commit()

            # Find or create stage_runs row
            existing_runs = (
                db.query(StageRun)
                .filter(StageRun.call_id == call_id, StageRun.stage == stage_name)
                .all()
            )
            attempt = len(existing_runs) + 1

            stage_run = StageRun(
                id=str(uuid.uuid4()),
                call_id=call_id,
                stage=stage_name,
                attempt=attempt,
                status="running",
                started_at=datetime.utcnow()
            )
            db.add(stage_run)
            db.commit()

            logger.info(
                f"Stage '{stage_name}' started for call {call_id} (attempt {attempt})",
                extra={"call_id": call_id, "stage": stage_name, "attempt": attempt, "stage_status": "started"}
            )

            t0 = time.time()
            try:
                res = stage_fn(db, call_id)
                duration_ms = round((time.time() - t0) * 1000, 1)
                stage_run.status = "succeeded"
                stage_run.finished_at = datetime.utcnow()
                stage_run.result_summary = res.get("message", "Stage completed successfully.")
                db.commit()
                logger.info(
                    f"Stage '{stage_name}' succeeded for call {call_id} in {duration_ms}ms: {stage_run.result_summary}",
                    extra={"call_id": call_id, "stage": stage_name, "attempt": attempt, "stage_status": "succeeded", "duration_ms": duration_ms}
                )
            except Exception as e:
                db.rollback()
                duration_ms = round((time.time() - t0) * 1000, 1)
                err_code = getattr(e, "code", "STAGE_FAILED")
                err_msg = getattr(e, "message", str(e))
                stage_run.status = "failed"
                stage_run.finished_at = datetime.utcnow()
                stage_run.error_code = err_code
                stage_run.result_summary = err_msg

                # Mark call as failed or partial
                call.failure_stage = stage_name
                call.failure_code = err_code
                call.failure_message = err_msg
                call.locked_at = None

                # If transcript exists, status is partial, else failed
                has_transcript = db.query(Call).filter(Call.id == call_id).first().transcript is not None
                call.status = "partial" if has_transcript and stage_name != "transcription" else "failed"
                db.commit()
                logger.error(
                    f"Stage '{stage_name}' failed for call {call_id} in {duration_ms}ms with {err_code}: {err_msg}",
                    extra={"call_id": call_id, "stage": stage_name, "attempt": attempt, "stage_status": "failed", "error_code": err_code, "duration_ms": duration_ms}
                )
                return

    finally:
        db.close()
