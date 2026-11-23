from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel

class CallListItem(BaseModel):
    id: str
    name: str
    status: str
    status_group: str
    tone: Optional[str] = None
    duration_ms: Optional[int] = None
    size_bytes: int
    is_synthetic: bool
    created_at: datetime

class CallListResponse(BaseModel):
    items: list[CallListItem]
    total: int
    page: int
    page_size: int

class CallDetailResponse(BaseModel):
    id: str
    name: str
    status: str
    status_group: str
    size_bytes: int
    duration_ms: Optional[int] = None
    audio_retained: bool
    is_synthetic: bool
    failure: Optional[dict[str, Any]] = None
    latest_analysis: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class StageStatus(BaseModel):
    stage: str
    status: str  # pending, running, succeeded, failed, skipped
    attempt: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    elapsed_ms: Optional[int] = None
    message: Optional[str] = None
    error_code: Optional[str] = None

class CallStatusResponse(BaseModel):
    call_id: str
    status: str
    status_group: str
    current_stage: Optional[str] = None
    completed_stages: int
    total_stages: int = 7
    attempt_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failure: Optional[dict[str, Any]] = None
    partial_reason: Optional[str] = None
    stages: list[StageStatus]
    updated_at: datetime
