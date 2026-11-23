import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models.settings import SettingsVersion
from app.utils.errors import AppError

DEFAULT_SETTINGS_CONFIG = {
    "tone": {
        "criteria": [
            {
                "id": "rude",
                "label": "Rude",
                "description": "Disrespectful or impolite remarks",
                "enabled": True,
                "custom": False
            },
            {
                "id": "hostile",
                "label": "Hostile",
                "description": "Aggressive, insulting or threatening language",
                "enabled": True,
                "custom": False
            },
            {
                "id": "dismissive",
                "label": "Dismissive",
                "description": "Brushing off or ignoring the customer's concern",
                "enabled": True,
                "custom": False
            }
        ],
        "sensitivity": "medium",
        "guidance": ""
    },
    "actions": {
        "types": {
            "commitments": True,
            "follow_ups": True,
            "information_promised": True,
            "customer_tasks": False
        },
        "include_tentative": False,
        "owner_rule": "explicit_or_committing_speaker",
        "capture_relative_deadlines": True,
        "guidance": ""
    }
}

class SettingsService:
    @staticmethod
    def get_latest_settings(db: Session) -> SettingsVersion:
        latest = db.query(SettingsVersion).order_by(desc(SettingsVersion.version)).first()
        if not latest:
            latest = SettingsService.seed_default_settings(db)
        return latest

    @staticmethod
    def get_settings_by_version(db: Session, version: int) -> Optional[SettingsVersion]:
        return db.query(SettingsVersion).filter(SettingsVersion.version == version).first()

    @staticmethod
    def seed_default_settings(db: Session) -> SettingsVersion:
        existing = db.query(SettingsVersion).filter(SettingsVersion.version == 1).first()
        if existing:
            return existing
        default_version = SettingsVersion(
            version=1,
            sensitivity="medium",
            config=DEFAULT_SETTINGS_CONFIG,
            source="default"
        )
        db.add(default_version)
        db.commit()
        db.refresh(default_version)
        return default_version

    @staticmethod
    def update_settings(db: Session, new_config: dict[str, Any], source: str = "user") -> SettingsVersion:
        tone = new_config.get("tone", {})
        actions = new_config.get("actions", {})

        sensitivity = tone.get("sensitivity", "medium")
        if sensitivity not in ["low", "medium", "high"]:
            raise AppError("INVALID_SETTINGS", f"Sensitivity must be 'low', 'medium', or 'high', got '{sensitivity}'.", 422)

        criteria = tone.get("criteria", [])
        if not isinstance(criteria, list) or len(criteria) == 0:
            raise AppError("INVALID_SETTINGS", "At least one tone criterion must be configured.", 422)

        # Get latest version number
        latest = SettingsService.get_latest_settings(db)
        next_version = (latest.version if latest else 0) + 1

        new_version_row = SettingsVersion(
            version=next_version,
            sensitivity=sensitivity,
            config=new_config,
            source=source
        )
        db.add(new_version_row)
        db.commit()
        db.refresh(new_version_row)
        return new_version_row

    @staticmethod
    def reset_to_defaults(db: Session) -> SettingsVersion:
        return SettingsService.update_settings(db, DEFAULT_SETTINGS_CONFIG, source="reset")
