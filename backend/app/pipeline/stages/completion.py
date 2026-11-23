from sqlalchemy.orm import Session
from app.db.models.calls import Call
from app.db.models.analyses import Analysis

def run_completion_stage(db: Session, call_id: str) -> dict:
    call = db.query(Call).filter(Call.id == call_id).first()
    latest_analysis = (
        db.query(Analysis)
        .filter(Analysis.call_id == call_id)
        .order_by(Analysis.run_number.desc())
        .first()
    )

    if latest_analysis and latest_analysis.status == "complete":
        call.status = "complete"
    else:
        call.status = "partial"

    call.locked_at = None
    call.failure_stage = None
    call.failure_code = None
    call.failure_message = None
    db.commit()

    return {
        "message": f"Pipeline completed successfully. Status: {call.status}.",
        "final_status": call.status
    }
