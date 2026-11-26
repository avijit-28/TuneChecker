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
    # Sample up to 25 utterances to capture the opening discovery, pitch, and objection handling
    sample_utterances = utterances[:25]
    transcript_summary = "\n".join([f"Speaker {u.speaker_label}: \"{u.text}\"" for u in sample_utterances])

    # Enhanced heuristic scoring for Sales Rep vs Customer
    seller_keywords = [
        "calling from", "my name is", "thanks for taking my call", "how can i help",
        "our solution", "our platform", "our product", "per month", "software",
        "pricing", "features", "quick demo", "reach out", "we provide", "we help",
        "wondering if", "schedule a time", "follow up", "custom design", "inventory",
        "wholesale", "order management", "streamline"
    ]
    buyer_keywords = [
        "how much does it cost", "send me an email", "not interested", "we already have",
        "who is this", "i am busy", "call me back", "my email is", "our owner",
        "decision maker", "talk to my partner", "send over details"
    ]

    scores = {"A": 0, "B": 0}
    evidence_found = []

    for u in sample_utterances:
        text_lower = u.text.lower()
        for kw in seller_keywords:
            if kw in text_lower:
                scores[u.speaker_label] += 2
                if len(evidence_found) < 3:
                    evidence_found.append(f"Speaker {u.speaker_label}: '{kw}' in '{u.text[:60]}...'")
        for kw in buyer_keywords:
            if kw in text_lower:
                # If someone says buyer keyword, other speaker is likely seller
                opp = "B" if u.speaker_label == "A" else "A"
                scores[opp] += 1

    rep_speaker = None
    heuristic_confidence = "low"
    if abs(scores["A"] - scores["B"]) >= 2:
        rep_speaker = "A" if scores["A"] > scores["B"] else "B"
        heuristic_confidence = "high" if abs(scores["A"] - scores["B"]) >= 4 else "medium"

    # If heuristic is uncertain, verify with LLM using wider context
    llm_confidence = heuristic_confidence
    if not rep_speaker or heuristic_confidence == "low":
        try:
            llm = OllamaLlmProvider()
            user_prompt = (
                "Identify which speaker is the Sales Representative pitching/offering products or services, "
                f"and which is the Customer/Prospect:\n\n{transcript_summary}"
            )
            res = llm.generate_json(ROLE_INFERENCE_SYSTEM, user_prompt)
            suggested_rep = res.get("rep_speaker", "").strip().upper()
            if suggested_rep in ["A", "B"]:
                rep_speaker = suggested_rep
                llm_confidence = res.get("confidence", "high")
        except Exception:
            if not rep_speaker:
                rep_speaker = "A" if scores["A"] >= scores["B"] else "B"
            llm_confidence = "medium" if rep_speaker else "low"

    if not rep_speaker:
        rep_speaker = "A"

    # Edge Case: Short / Mid-call audio snippet (< 4 utterances or < 25 total words)
    total_words = sum(len(u.text.split()) for u in utterances)
    if len(utterances) <= 3 or total_words < 25:
        # Mark as ambiguous / uncertain to protect innocent sales rep from false RED penalties
        llm_confidence = "low"

    customer_speaker = "B" if rep_speaker == "A" else "A"

    # Update database rows
    for r in roles:
        if r.speaker_label == rep_speaker:
            r.role = "sales_rep"
            r.source = "auto"
            r.status = "confident" if llm_confidence in ["high", "medium"] else "uncertain"
            r.level = llm_confidence
            r.factors = {"method": "hybrid_heuristic_llm", "cues": evidence_found[:2], "total_words": total_words}
        else:
            r.role = "customer"
            r.source = "auto"
            r.status = "confident" if llm_confidence in ["high", "medium"] else "uncertain"
            r.level = llm_confidence
            r.factors = {"method": "complement", "total_words": total_words}
    db.commit()

    return {
        "message": f"Assigned Speaker {rep_speaker} as Sales Rep ({llm_confidence} confidence).",
        "rep_speaker": rep_speaker,
        "confidence": llm_confidence
    }
