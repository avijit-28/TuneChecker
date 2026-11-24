from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

class StageRun(Base):
    __tablename__ = "stage_runs"

    id = Column(String, primary_key=True)
    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String, nullable=False)
    attempt = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False)  # 'running', 'succeeded', 'failed', 'skipped'
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    result_summary = Column(String, nullable=True)
    error_code = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("call_id", "stage", "attempt", name="uq_stage_runs_call_stage_attempt"),
    )

    call = relationship("Call", back_populates="stage_runs")
