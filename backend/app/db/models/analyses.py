from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, UniqueConstraint, CheckConstraint, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True)
    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    run_number = Column(Integer, nullable=False, default=1)
    settings_version = Column(Integer, ForeignKey("settings_versions.version", ondelete="RESTRICT"), nullable=False)
    status = Column(String, nullable=False)  # 'complete', 'partial'
    partial_reason = Column(String, nullable=True)
    verdict = Column(String, nullable=True)  # 'RED', 'GREEN', 'NEEDS_REVIEW', or None
    confidence_level = Column(String, nullable=True)  # 'high', 'medium', 'low'
    confidence_factors = Column(JSON, nullable=True)
    limited_evidence_reason = Column(String, nullable=True)
    explanation = Column(String, nullable=True)
    rep_speaker_label = Column(String, nullable=True)
    roles_source = Column(String, nullable=True)  # 'auto', 'user'
    dropped_evidence_count = Column(Integer, nullable=False, default=0)
    dropped_details = Column(JSON, nullable=True)
    model_name = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("call_id", "run_number", name="uq_analyses_call_run_number"),
        UniqueConstraint("id", "call_id", name="uq_analyses_id_call"),
        UniqueConstraint("id", "call_id", "rep_speaker_label", name="uq_analyses_id_call_rep"),
        CheckConstraint("status IN ('complete', 'partial')", name="ck_analyses_status"),
        CheckConstraint("verdict IS NULL OR verdict IN ('RED', 'GREEN', 'NEEDS_REVIEW')", name="ck_analyses_verdict"),
    )

    call = relationship("Call", back_populates="analyses")
    evidence_items = relationship("EvidenceItem", back_populates="analysis", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="analysis", cascade="all, delete-orphan")
    coaching_recommendations = relationship("CoachingRecommendation", back_populates="analysis", cascade="all, delete-orphan")
    settings = relationship("SettingsVersion")

class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String, primary_key=True)
    analysis_id = Column(String, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    call_id = Column(String, nullable=False)
    ref = Column(String, nullable=False)  # 'E1', 'E2', etc.
    utterance_id = Column(String, ForeignKey("utterances.id", ondelete="CASCADE"), nullable=False)
    speaker_label = Column(String, nullable=False)
    quote = Column(String, nullable=False)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    criterion_id = Column(String, nullable=False)
    severity = Column(Integer, nullable=False)  # 1, 2, 3
    rationale = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("analysis_id", "ref", name="uq_evidence_analysis_ref"),
    )

    analysis = relationship("Analysis", back_populates="evidence_items")
    utterance = relationship("Utterance", back_populates="evidence_items")

class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(String, primary_key=True)
    analysis_id = Column(String, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    call_id = Column(String, nullable=False)
    ref = Column(String, nullable=False)  # 'A1', 'A2', etc.
    type = Column(String, nullable=False)  # 'commitment', 'follow_up', 'information_promised', 'customer_task'
    task = Column(String, nullable=False)
    modality = Column(String, nullable=False)  # 'definite', 'tentative'
    owner_text = Column(String, nullable=True)
    owner_basis = Column(String, nullable=False, default="none")  # 'explicit_name', 'explicit_role', 'committing_speaker', 'none'
    deadline_text = Column(String, nullable=True)
    utterance_id = Column(String, ForeignKey("utterances.id", ondelete="CASCADE"), nullable=False)
    speaker_label = Column(String, nullable=False)
    quote = Column(String, nullable=False)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("analysis_id", "ref", name="uq_actions_analysis_ref"),
    )

    analysis = relationship("Analysis", back_populates="action_items")
    utterance = relationship("Utterance", back_populates="action_items")

class CoachingRecommendation(Base):
    __tablename__ = "coaching_recommendations"

    id = Column(String, primary_key=True)
    analysis_id = Column(String, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    ref = Column(String, nullable=False)  # 'C1', 'C2', etc.
    category = Column(String, nullable=False)  # 'objection_handling', 'pacing', 'active_listening', 'professionalism', 'product_knowledge'
    recommendation = Column(Text, nullable=False)
    context_quote = Column(Text, nullable=True)
    severity = Column(String, nullable=False, default="suggestion")  # 'suggestion' | 'important' | 'critical'
    utterance_id = Column(String, ForeignKey("utterances.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("analysis_id", "ref", name="uq_coaching_analysis_ref"),
        CheckConstraint("severity IN ('suggestion', 'important', 'critical')", name="ck_coaching_severity"),
    )

    analysis = relationship("Analysis", back_populates="coaching_recommendations")
    utterance = relationship("Utterance")
