from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Criterion(BaseModel):
    id: Optional[str] = None
    label: str = Field(..., min_length=1, max_length=140)
    description: Optional[str] = None
    enabled: bool = True
    custom: bool = False

class ToneSettings(BaseModel):
    criteria: list[Criterion]
    sensitivity: str = Field("medium", pattern="^(low|medium|high)$")
    guidance: str = Field("", max_length=500)

class ActionTypes(BaseModel):
    commitments: bool = True
    follow_ups: bool = True
    information_promised: bool = True
    customer_tasks: bool = False

class ActionSettings(BaseModel):
    types: ActionTypes
    include_tentative: bool = False
    owner_rule: str = Field("explicit_or_committing_speaker", pattern="^(explicit_or_committing_speaker|explicit_only)$")
    capture_relative_deadlines: bool = True
    guidance: str = Field("", max_length=500)

class SettingsConfig(BaseModel):
    tone: ToneSettings
    actions: ActionSettings

class SettingsResponse(BaseModel):
    version: int
    sensitivity: str
    source: str
    created_at: datetime
    config: SettingsConfig
