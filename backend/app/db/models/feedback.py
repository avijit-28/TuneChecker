import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class AuditorFeedback(Base):
    __tablename__ = "auditor_feedback"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    analysis_id = Column(String, nullable=True)
    agreed = Column(Boolean, nullable=False, default=True)
    auditor_verdict = Column(String, nullable=False)  # 'RED', 'GREEN', 'UNCERTAIN'
    notes = Column(Text, nullable=True, default="")
    auditor_name = Column(String, nullable=False, default="Sales Quality Auditor")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    call = relationship("Call", backref="feedback_entries")
