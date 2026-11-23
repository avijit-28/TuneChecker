import time
from pathlib import Path
from sqlalchemy.orm import Session
from app.audio.validation import validate_audio_file
from app.db.models.calls import Call
from app.config import settings

def run_validation_stage(db: Session, call_id: str) -> dict:
    call = db.query(Call).filter(Call.id == call_id).first()
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / call.storage_key
    
    meta = validate_audio_file(audio_path)
    call.duration_ms = meta["duration_ms"]
    db.commit()

    return {
        "message": f"Audio readable and within limits ({meta['duration_sec']:.1f}s, {meta['codec']}).",
        "duration_ms": meta["duration_ms"]
    }
