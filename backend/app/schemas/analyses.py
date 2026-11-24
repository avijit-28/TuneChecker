from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel

class CoachingRecommendationResponse(BaseModel):
    id: str
    analysis_id: str
    call_id: str
    ref: str
    category: str
    recommendation: str
    context_quote: Optional[str] = None
    severity: str = "suggestion"
    utterance_id: Optional[str] = None
    start_ms: Optional[int] = None
    created_at: Optional[datetime] = None

class ActionItemResponse(BaseModel):
    id: str
    ref: str
    type: str
    task: str
    modality: str
    owner: dict[str, Any]
    deadline: Optional[str] = None
    quote: str
    char_start: int
    char_end: int
    utterance_id: str
    start_ms: int

class EvidenceItemResponse(BaseModel):
    id: str
    ref: str
    utterance_id: str
    speaker_label: str
    quote: str
    char_start: int
    char_end: int
    criterion_id: str
    severity: int
    rationale: str
    start_ms: int

class AnalysisResponse(BaseModel):
    id: str
    call_id: str
    run_number: int
    status: str
    verdict: Optional[str] = None
    confidence: dict[str, Any]
    calibrated_model: Optional[dict[str, Any]] = None
    limited_evidence_reason: Optional[str] = None
    explanation: Optional[str] = None
    sales_rep: Optional[dict[str, Any]] = None
    evidence: List[EvidenceItemResponse] = []
    action_items: List[ActionItemResponse] = []
    coaching_recommendations: List[CoachingRecommendationResponse] = []
    settings_snapshot: Optional[dict[str, Any]] = None
    created_at: datetime
