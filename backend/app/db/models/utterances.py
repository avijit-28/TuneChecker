from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

class Utterance(Base):
    __tablename__ = "utterances"

    id = Column(String, primary_key=True)
    call_id = Column(String, ForeignKey("transcripts.call_id", ondelete="CASCADE"), nullable=False)
    idx = Column(Integer, nullable=False)
    speaker_label = Column(String, nullable=False)
    start_ms = Column(Integer, nullable=False)
    end_ms = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    asr_confidence = Column(Float, nullable=True)
    speaker_confidence = Column(Float, nullable=True)
    low_attribution = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("call_id", "idx", name="uq_utterances_call_idx"),
        UniqueConstraint("id", "call_id", "speaker_label", name="uq_utterances_id_call_speaker"),
    )

    transcript = relationship("Transcript", back_populates="utterances")
    evidence_items = relationship("EvidenceItem", back_populates="utterance")
    action_items = relationship("ActionItem", back_populates="utterance")
