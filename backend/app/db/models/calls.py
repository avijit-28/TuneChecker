from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base

class Call(Base):
    __tablename__ = "calls"

    id = Column(String, primary_key=True)
    original_filename = Column(String, nullable=False)
    storage_key = Column(String, unique=True, nullable=True)
    audio_hash = Column(String, index=True, nullable=True)
    audio_deleted_at = Column(DateTime, nullable=True)
    size_bytes = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="uploaded")
    failure_stage = Column(String, nullable=True)
    failure_code = Column(String, nullable=True)
    failure_message = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    is_synthetic = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stage_runs = relationship("StageRun", back_populates="call", cascade="all, delete-orphan")
    transcript = relationship("Transcript", back_populates="call", uselist=False, cascade="all, delete-orphan")
    speaker_roles = relationship("SpeakerRole", back_populates="call", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="call", cascade="all, delete-orphan")
