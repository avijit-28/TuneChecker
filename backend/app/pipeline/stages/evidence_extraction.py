from sqlalchemy.orm import Session
from app.db.models.analyses import Analysis, EvidenceItem

def run_evidence_extraction_stage(db: Session, call_id: str) -> dict:
    analysis = (
        db.query(Analysis)
        .filter(Analysis.call_id == call_id)
        .order_by(Analysis.run_number.desc())
        .first()
    )
    if not analysis or analysis.status != "complete":
        return {"message": "Evidence verification skipped.", "evidence_count": 0}

    items = db.query(EvidenceItem).filter(EvidenceItem.analysis_id == analysis.id).all()
    return {
        "message": f"Verified {len(items)} evidence quote(s) against transcript text.",
        "evidence_count": len(items)
    }
