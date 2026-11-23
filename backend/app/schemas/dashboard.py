from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel
from app.schemas.calls import CallListItem

class DashboardKpis(BaseModel):
    total_calls: int
    total_analyzed: int
    red: int
    green: int
    awaiting_analysis: int
    needs_attention: int

class ToneDistribution(BaseModel):
    red: int
    green: int
    not_analyzed: int

class RecentActionItem(BaseModel):
    id: str
    task: str
    owner_text: Optional[str] = None
    deadline_text: Optional[str] = None
    call_id: str
    call_name: str
    start_ms: int

class DashboardSummaryResponse(BaseModel):
    generated_at: datetime
    kpis: DashboardKpis
    tone_distribution: ToneDistribution
    recent_calls: list[CallListItem]
    recent_action_items: list[RecentActionItem]
