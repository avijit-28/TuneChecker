import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.settings_service import SettingsService
from app.schemas.settings import SettingsResponse, SettingsConfig
from app.utils.errors import AppError

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    latest = SettingsService.get_latest_settings(db)
    return {
        "version": latest.version,
        "sensitivity": latest.sensitivity,
        "source": latest.source,
        "created_at": latest.created_at,
        "config": latest.config
    }

@router.put("", response_model=SettingsResponse)
def update_settings(payload: SettingsConfig, db: Session = Depends(get_db)):
    config_dict = payload.model_dump()
    
    # Process criteria IDs: preserve built-in or assign new IDs for custom
    criteria = config_dict.get("tone", {}).get("criteria", [])
    built_in_ids = {"rude", "hostile", "dismissive"}
    present_builtins = set()
    custom_count = 0
    
    for c in criteria:
        cid = c.get("id")
        if cid in built_in_ids:
            present_builtins.add(cid)
            c["custom"] = False
        else:
            custom_count += 1
            c["custom"] = True
            if not cid:
                c["id"] = f"custom_{uuid.uuid4().hex[:8]}"
            if not c.get("description"):
                c["description"] = c["label"]

    if not built_in_ids.issubset(present_builtins):
        missing = built_in_ids - present_builtins
        raise AppError("SETTINGS_INVALID", f"Missing built-in criteria: {missing}", 422)
        
    if custom_count > 5:
        raise AppError("SETTINGS_INVALID", "At most 5 custom criteria may be configured.", 422)
        
    if not any(c.get("enabled", False) for c in criteria):
        raise AppError("SETTINGS_INVALID", "At least one tone criterion must be enabled.", 422)

    action_types = config_dict.get("actions", {}).get("types", {})
    if not any(action_types.values()):
        raise AppError("SETTINGS_INVALID", "At least one action-item type must be enabled.", 422)

    new_version = SettingsService.update_settings(db, config_dict, source="user")
    return {
        "version": new_version.version,
        "sensitivity": new_version.sensitivity,
        "source": new_version.source,
        "created_at": new_version.created_at,
        "config": new_version.config
    }

@router.post("/reset", response_model=SettingsResponse)
def reset_settings(db: Session = Depends(get_db)):
    reset_version = SettingsService.reset_to_defaults(db)
    return {
        "version": reset_version.version,
        "sensitivity": reset_version.sensitivity,
        "source": reset_version.source,
        "created_at": reset_version.created_at,
        "config": reset_version.config
    }
