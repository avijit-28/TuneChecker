from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Transcript(Base):
    __tablename__ = "transcripts"

    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True)
    status = Column(String, nullable=False)  # 'submitted', 'completed', 'failed'
    provider = Column(String, nullable=False)
    provider_transcript_id = Column(String, unique=True, nullable=True)
    model = Column(String, nullable=True)
    language = Column(String, nullable=False, default="en")
    speaker_count = Column(Integer, nullable=True)
    audio_seconds = Column(Float, nullable=True)
    raw_response = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    call = relationship("Call", back_populates="transcript")
    utterances = relationship("Utterance", back_populates="transcript", cascade="all, delete-orphan")
