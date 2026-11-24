from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

class SpeakerRole(Base):
    __tablename__ = "speaker_roles"

    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    speaker_label = Column(String, nullable=False)
    role = Column(String, nullable=False, default="unknown")  # 'sales_rep', 'customer', 'unknown'
    source = Column(String, nullable=False, default="auto")    # 'auto', 'user'
    status = Column(String, nullable=False, default="unresolved")  # 'unresolved', 'uncertain', 'confident', 'confirmed'
    level = Column(String, nullable=True)                      # 'high', 'medium', 'low'
    factors = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint("call_id", "speaker_label"),
    )

    call = relationship("Call", back_populates="speaker_roles")
