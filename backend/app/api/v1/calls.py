import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, Response, status
from fastapi.responses import PlainTextResponse, FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.call_service import CallService
from app.audio.upload_checks import validate_filename_and_mime, validate_audio_container
from app.config import settings
from app.utils.errors import AppError
from app.jobs.worker import queue_call_processing
from app.schemas.calls import (
    CallListResponse,
    CallDetailResponse,
    CallStatusResponse
)
from app.db.models.feedback import AuditorFeedback
from app.learning.feedback_trainer import train_and_evaluate_feedback, predict_calibrated_tone

router = APIRouter(prefix="/calls", tags=["Calls"])

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_call(
    response: Response,
    file: UploadFile = File(...),
    language_mode: Optional[str] = Form(None),
    force_reanalyze: bool = Form(False),
    db: Session = Depends(get_db)
):
    import hashlib
    if language_mode:
        settings.WHISPER_LANGUAGE_MODE = language_mode.strip().lower()
    sanitized_name = validate_filename_and_mime(file.filename, file.content_type)

    # Ensure storage directory exists
    os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
    ext = os.path.splitext(sanitized_name)[1].lower() or ".m4a"
    storage_key = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(settings.STORAGE_LOCAL_PATH, storage_key)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_bytes = 0
    header_bytes = b""
    hasher = hashlib.sha256()

    try:
        with open(dest_path, "wb") as f:
            while chunk := await file.read(64 * 1024):
                if len(header_bytes) < 32:
                    header_bytes += chunk[: 32 - len(header_bytes)]
                total_bytes += len(chunk)
                hasher.update(chunk)
                if total_bytes > max_bytes:
                    raise AppError(
                        "FILE_TOO_LARGE",
                        f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
                        413,
                        details={"limit_mb": settings.MAX_UPLOAD_SIZE_MB}
                    )
                f.write(chunk)
    except Exception:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise

    if total_bytes == 0:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise AppError("FILE_EMPTY", "Uploaded file is empty (0 bytes).", 422)

    if not validate_audio_container(header_bytes, sanitized_name):
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise AppError("INVALID_FILE_TYPE", f"File header does not match expected audio container format for '{ext}'.", 415)

    raw_hash = hasher.hexdigest()
    lang_mode = getattr(settings, "WHISPER_LANGUAGE_MODE", "hinglish")
    cache_version = "v4-pcm"
    audio_hash = hashlib.sha256(f"{raw_hash}:{cache_version}:{lang_mode}".encode("utf-8")).hexdigest()
    call = CallService.create_call(db, sanitized_name, total_bytes, storage_key, audio_hash=audio_hash)

    # Fast Fingerprint Deduplication Cache
    existing_completed = CallService.find_completed_by_hash(db, audio_hash) if not force_reanalyze else None
    if existing_completed and existing_completed.id != call.id:
        # Instant cache hit: Clone previous analysis without burning Whisper or LLM tokens!
        CallService.clone_completed_analysis(db, existing_completed.id, call)
    else:
        # First time seeing this audio: queue full async pipeline
        queue_call_processing(call.id, start_stage="validation")

    response.headers["Location"] = f"/api/v1/calls/{call.id}/status"
    return {
        "id": call.id,
        "name": call.original_filename,
        "status": call.status,
        "size_bytes": call.size_bytes,
        "created_at": call.created_at,
        "cached": bool(existing_completed)
    }

@router.post("/cache/clear")
def clear_audio_cache(db: Session = Depends(get_db)):
    """Invalidates all audio fingerprint cache entries without deleting call history."""
    cleared = CallService.clear_fingerprint_cache(db)
    return {"cleared_entries": cleared}

@router.get("", response_model=CallListResponse)
def list_calls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, max_length=100),
    tone: Optional[str] = Query(None, pattern="^(red|green|needs_review|none)$"),
    status: Optional[str] = Query(None, pattern="^(in_progress|complete|partial|failed)$"),
    sort: str = Query("newest", pattern="^(newest|oldest)$"),
    db: Session = Depends(get_db)
):
    items, total = CallService.list_calls(
        db=db,
        page=page,
        page_size=page_size,
        q=q,
        tone=tone,
        status_filter=status,
        sort=sort
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{call_id}", response_model=CallDetailResponse)
def get_call_detail(call_id: str, db: Session = Depends(get_db)):
    return CallService.get_call_detail(db, call_id)

@router.get("/{call_id}/status", response_model=CallStatusResponse)
def get_call_status(call_id: str, db: Session = Depends(get_db)):
    return CallService.get_call_status(db, call_id)

@router.get("/{call_id}/transcript")
def get_call_transcript(call_id: str, db: Session = Depends(get_db)):
    res = CallService.get_transcript(db, call_id)
    return Response(
        content=res if isinstance(res, str) else None,
        headers={"Cache-Control": "no-store"}
    ) if isinstance(res, str) else res

@router.get("/{call_id}/analysis")
def get_call_analysis(call_id: str, db: Session = Depends(get_db)):
    return CallService.get_analysis(db, call_id)

@router.get("/{call_id}/report")
def get_call_report(call_id: str, db: Session = Depends(get_db)):
    return CallService.get_call_report(db, call_id)

@router.get("/{call_id}/audio")
def stream_call_audio(call_id: str, db: Session = Depends(get_db)):
    audio_path, media_type = CallService.get_audio_file(db, call_id)
    return FileResponse(
        path=str(audio_path),
        media_type=media_type,
        content_disposition_type="inline",
        headers={"Accept-Ranges": "bytes"}
    )

@router.put("/{call_id}/speaker-roles", status_code=status.HTTP_202_ACCEPTED)
def update_speaker_roles(call_id: str, payload: dict, db: Session = Depends(get_db)):
    new_roles = payload.get("roles", {})
    if not new_roles:
        raise AppError("INVALID_ROLES", "Payload must contain 'roles' dictionary.", 422)

    CallService.update_speaker_roles(db, call_id, new_roles)
    
    # Re-run analysis from tone_analysis stage
    queue_call_processing(call_id, start_stage="tone_analysis")

    return {
        "call_id": call_id,
        "status": "analyzing"
    }

@router.post("/{call_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_call(call_id: str, payload: dict, db: Session = Depends(get_db)):
    stage = payload.get("stage")
    allowed_stages = ["validation", "transcription", "speaker_identification", "tone_analysis", "evidence_extraction", "action_items"]
    if stage not in allowed_stages:
        raise AppError("REQUEST_INVALID", f"Invalid retry stage '{stage}'.", 422)

    c = CallService.get_call_detail(db, call_id)
    if c["status_group"] == "in_progress":
        raise AppError("NOT_RETRYABLE", "Cannot retry while call is currently processing.", 409, details={"reason": "IN_PROGRESS"})

    queue_call_processing(call_id, start_stage=stage)
    return {
        "call_id": call_id,
        "status": "validating" if stage == "validation" else ("transcribing" if stage == "transcription" else "analyzing")
    }

@router.post("/{call_id}/reanalyze", status_code=status.HTTP_202_ACCEPTED)
def reanalyze_call(call_id: str, db: Session = Depends(get_db)):
    c = CallService.get_call_detail(db, call_id)
    if c["status_group"] == "in_progress":
        raise AppError("NOT_RETRYABLE", "Cannot re-analyze while call is currently processing.", 409, details={"reason": "IN_PROGRESS"})
    queue_call_processing(call_id, start_stage="validation")
    return {
        "call_id": call_id,
        "status": "validating",
        "message": "Full audio re-analysis queued with surgical enhancement."
    }

@router.get("/{call_id}/export")
def export_call(call_id: str, format: str = Query("json", pattern="^(json|markdown)$"), db: Session = Depends(get_db)):
    detail = CallService.get_call_detail(db, call_id)
    analysis = CallService.get_analysis(db, call_id)
    transcript = CallService.get_transcript(db, call_id)

    if format == "markdown":
        md = [
            f"# Sales Call Audit Report: {detail['name']}",
            f"**Call ID:** {call_id}  ",
            f"**Audited At:** {analysis['created_at']}  ",
            f"**Verdict:** {analysis['verdict']} (Confidence: {analysis['confidence']['level']})  ",
            f"**Sales Rep:** Speaker {analysis['sales_rep']['label'] if analysis['sales_rep'] else 'N/A'}  ",
            "",
            "## Explanation",
            analysis['explanation'] or "No explanation provided.",
            "",
            "## Verified Evidence",
        ]
        if analysis["evidence"]:
            for e in analysis["evidence"]:
                md.append(f"- **[{e['ref']}]** \"{e['quote']}\" (Criterion: {e['criterion_id']}, Severity: {e['severity']}) - {e['rationale']}")
        else:
            md.append("No negative behavior evidence found.")

        md.append("\n## Action Items & Commitments")
        if analysis["action_items"]:
            for a in analysis["action_items"]:
                md.append(f"- **[{a['ref']}]** {a['task']} | Owner: {a['owner']['text'] or 'Not specified'} | Deadline: {a['deadline'] or 'Not specified'}")
        else:
            md.append("No action items tracked.")

        md.append("\n## Transcript")
        for u in transcript["utterances"]:
            sec_start = u["start_ms"] / 1000.0
            sec_end = u["end_ms"] / 1000.0
            md.append(f"**[{sec_start:04.1f} - {sec_end:04.1f}] Speaker {u['speaker_label']}:** {u['text']}")

        return PlainTextResponse(
            "\n".join(md),
            headers={"Content-Disposition": f'attachment; filename="call_audit_{call_id[:8]}.md"'}
        )

    # Default JSON
    return {
        "call": detail,
        "analysis": analysis,
        "transcript": transcript
    }

@router.post("/feedback/train")
def train_feedback_model(db: Session = Depends(get_db)):
    """Trains a conservative TF-IDF + Logistic Regression model from human auditor reviews."""
    result = train_and_evaluate_feedback(db)
    return result

@router.get("/{call_id}/feedback")
def get_call_feedback(call_id: str, db: Session = Depends(get_db)):
    """Fetches all auditor feedback records for a given call."""
    entries = db.query(AuditorFeedback).filter(AuditorFeedback.call_id == call_id).order_by(AuditorFeedback.created_at.desc()).all()
    return [
        {
            "id": fb.id,
            "call_id": fb.call_id,
            "agreed": fb.agreed,
            "auditor_verdict": fb.auditor_verdict,
            "notes": fb.notes,
            "auditor_name": fb.auditor_name,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        }
        for fb in entries
    ]

@router.post("/{call_id}/feedback", status_code=status.HTTP_201_CREATED)
def submit_call_feedback(call_id: str, payload: dict, db: Session = Depends(get_db)):
    """Submits auditor feedback on the call quality verdict for continuous learning."""
    agreed = payload.get("agreed", True)
    auditor_verdict = payload.get("auditor_verdict", "GREEN").upper()
    notes = payload.get("notes", "")
    auditor_name = payload.get("auditor_name", "Sales Quality Auditor")

    fb = AuditorFeedback(
        id=uuid.uuid4().hex,
        call_id=call_id,
        analysis_id=payload.get("analysis_id"),
        agreed=bool(agreed),
        auditor_verdict=auditor_verdict,
        notes=notes,
        auditor_name=auditor_name
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)

    return {
        "id": fb.id,
        "call_id": fb.call_id,
        "agreed": fb.agreed,
        "auditor_verdict": fb.auditor_verdict,
        "notes": fb.notes,
        "auditor_name": fb.auditor_name,
        "created_at": fb.created_at.isoformat() if fb.created_at else None,
        "message": "Auditor review recorded successfully."
    }

@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_call(call_id: str, db: Session = Depends(get_db)):
    CallService.delete_call(db, call_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
