from sqlalchemy.orm import Session
from app.db.models.speaker_roles import SpeakerRole
from app.db.models.utterances import Utterance
from app.pipeline.providers.llm.ollama import OllamaLlmProvider
from app.pipeline.safeguards.quote_matcher import find_quote_offsets

ROLE_INFERENCE_SYSTEM = """You are a sales call speaker identification analyzer.
Given a two-party call transcript with speakers labeled 'A' and 'B', identify which speaker is the Sales Representative and which is the Customer.
Output strictly valid JSON with keys:
- "rep_speaker": string ("A" or "B")
- "confidence": string ("high", "medium", "low")
- "evidence_cues": list of strings (exact verbatim phrases spoken by the sales rep identifying their role, e.g. company intro, product explanation)"""

def run_speaker_roles_stage(db: Session, call_id: str) -> dict:
    roles = db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id).all()
    if len(roles) < 2:
        # Only 1 speaker found, mark unresolved
        for r in roles:
            r.role = "unknown"
            r.status = "unresolved"
            r.level = "low"
        db.commit()
        return {"message": "Single speaker detected; roles marked unresolved.", "rep_speaker": None}

    utterances = db.query(Utterance).filter(Utterance.call_id == call_id).order_by(Utterance.idx.asc()).all()
    transcript_summary = "\n".join([f"Speaker {u.speaker_label}: \"{u.text}\"" for u in utterances[:8]])

    # Heuristic check on first 3 utterances
    rep_speaker = None
    heuristic_cues = []
    for u in utterances[:4]:
        text_lower = u.text.lower()
        if any(g in text_lower for g in ["thanks for taking my call", "speaking", "software", "our enterprise", "how can i help", "our pricing", "how are things going"]):
            rep_speaker = u.speaker_label
            heuristic_cues.append(u.text)
            break

    # If heuristic didn't find it, ask LLM
    llm_confidence = "medium"
    if not rep_speaker:
        try:
            llm = OllamaLlmProvider()
            user_prompt = f"Identify the Sales Representative in this conversation excerpt:\n\n{transcript_summary}"
            res = llm.generate_json(ROLE_INFERENCE_SYSTEM, user_prompt)
            suggested_rep = res.get("rep_speaker", "A").strip().upper()
            if suggested_rep in ["A", "B"]:
                rep_speaker = suggested_rep
                llm_confidence = res.get("confidence", "medium")
        except Exception:
            rep_speaker = "A"
            llm_confidence = "low"

    if not rep_speaker:
        rep_speaker = "A"

    customer_speaker = "B" if rep_speaker == "A" else "A"

    # Update database rows
    for r in roles:
        if r.speaker_label == rep_speaker:
            r.role = "sales_rep"
            r.source = "auto"
            r.status = "confident" if llm_confidence in ["high", "medium"] else "uncertain"
            r.level = llm_confidence
            r.factors = {"method": "hybrid_heuristic_llm", "cues": heuristic_cues[:2]}
        else:
            r.role = "customer"
            r.source = "auto"
            r.status = "confident" if llm_confidence in ["high", "medium"] else "uncertain"
            r.level = llm_confidence
            r.factors = {"method": "complement"}
    db.commit()

    return {
        "message": f"Assigned Speaker {rep_speaker} as Sales Rep ({llm_confidence} confidence).",
        "rep_speaker": rep_speaker,
        "confidence": llm_confidence
    }
