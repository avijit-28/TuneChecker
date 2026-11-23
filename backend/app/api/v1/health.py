import os
import subprocess
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.config import settings

router = APIRouter(tags=["Operations"])

@router.get("/health")
def get_health(response: Response, db: Session = Depends(get_db)):
    checks = {
        "database": "failed",
        "settings": "failed",
        "ffmpeg": "failed"
    }

    # 1. Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "failed"

    # 2. Settings check (verify table exists and latest row exists)
    try:
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='settings_versions'")).fetchone()
        if result:
            row = db.execute(text("SELECT version FROM settings_versions ORDER BY version DESC LIMIT 1")).fetchone()
            if row:
                checks["settings"] = "ok"
            else:
                checks["settings"] = "missing_active_version"
        else:
            checks["settings"] = "uninitialized"
    except Exception:
        checks["settings"] = "failed"

    # 3. FFmpeg check
    try:
        proc = subprocess.run(
            [settings.FFMPEG_PATH, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        if proc.returncode == 0:
            checks["ffmpeg"] = "ok"
        else:
            checks["ffmpeg"] = "failed"
    except Exception:
        checks["ffmpeg"] = "failed"

    all_ok = all(v == "ok" for v in checks.values())
    
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unavailable",
            "checks": checks
        }

    return {
        "status": "ok",
        "checks": checks
    }
