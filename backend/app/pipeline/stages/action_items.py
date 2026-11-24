import uuid
from sqlalchemy.orm import Session
from app.db.models.analyses import Analysis, ActionItem, CoachingRecommendation
from app.db.models.utterances import Utterance
from app.services.settings_service import SettingsService
from app.pipeline.providers.llm.ollama import OllamaLlmProvider
from app.pipeline.safeguards.action_rules import evaluate_action_items
from app.pipeline.safeguards.coaching_rules import evaluate_coaching_recommendations

ACTION_ITEMS_SYSTEM = """You are a sales call commitment and coaching evaluation engine.
Extract both:
1. Concrete commitments and follow-ups made during the conversation.
2. Constructive sales coaching recommendations for the sales representative.

Rules for Commitments ("candidate_actions"):
- Task: Clear description of the promised action.
- Quote: The EXACT verbatim sentence where the commitment was stated.
- Owner: Extract the owner ONLY if explicitly mentioned (e.g. "I will", "David will", "Sarah will"). If no specific person or role is stated, set owner_text to null.
- Deadline: Extract the deadline ONLY if explicitly stated (e.g. "by tomorrow at 5 PM", "by Friday"). If no timeframe is given, set deadline_text to null.
- Modality: "definite" (firm commitment) or "tentative" ("we might", "maybe", "could look into").

Rules for Coaching Recommendations ("candidate_coaching"):
- Identify areas for improvement across:
  - "objection_handling": handling price, competitor, or timing hesitations
  - "pacing": monologue duration, interrupting, or conversational rhythm
  - "active_listening": acknowledging customer statements and asking clarifying questions
  - "professionalism": tone, executive presence, and business etiquette
  - "product_knowledge": explaining features and technical capabilities
- Severity: "suggestion", "important", or "critical".

Output strictly valid JSON with keys:
- "candidate_actions": list of commitment objects containing:
  - "utterance_id": string
  - "task": string
  - "type": "commitment" | "follow_up" | "information_promised" | "customer_task"
  - "modality": "definite" | "tentative"
  - "owner_text": string or null
  - "owner_basis": "explicit_name" | "explicit_role" | "committing_speaker" | "none"
  - "deadline_text": string or null
  - "quote": string
- "candidate_coaching": list of coaching objects containing:
  - "utterance_id": string or null
  - "category": "objection_handling" | "pacing" | "active_listening" | "professionalism" | "product_knowledge"
  - "recommendation": string
  - "context_quote": string or null
  - "severity": "suggestion" | "important" | "critical" """

def run_action_items_stage(db: Session, call_id: str) -> dict:
    analysis = (
        db.query(Analysis)
        .filter(Analysis.call_id == call_id)
        .order_by(Analysis.run_number.desc())
        .first()
    )
    if not analysis or analysis.status != "complete":
        return {"message": "Action item extraction skipped.", "action_count": 0, "coaching_count": 0}

    active_settings = SettingsService.get_latest_settings(db)
    actions_config = active_settings.config.get("actions", {})

    utterances = db.query(Utterance).filter(Utterance.call_id == call_id).order_by(Utterance.idx.asc()).all()
    utt_dicts = [{"id": u.id, "speaker_label": u.speaker_label, "text": u.text} for u in utterances]

    formatted_transcript = "\n".join([f"Utterance [{u['id']}] Speaker {u['speaker_label']}: \"{u['text']}\"" for u in utt_dicts])
    user_prompt = f"Extract all commitments and sales coaching recommendations from this call:\n\n{formatted_transcript}"

    candidate_actions = []
    candidate_coaching = []
    try:
        llm = OllamaLlmProvider()
        res = llm.generate_json(ACTION_ITEMS_SYSTEM, user_prompt)
        candidate_actions = res.get("candidate_actions", [])
        candidate_coaching = res.get("candidate_coaching", [])
    except Exception:
        candidate_actions = []
        candidate_coaching = []

    verified_actions = evaluate_action_items(
        candidate_actions=candidate_actions,
        utterances=utt_dicts,
        action_settings=actions_config
    )

    verified_coaching = evaluate_coaching_recommendations(
        candidate_coaching=candidate_coaching,
        utterances=utt_dicts,
        rep_speaker_label=analysis.rep_speaker_label or "A"
    )

    # Persist Action Items
    db.query(ActionItem).filter(ActionItem.call_id == call_id).delete()
    for act in verified_actions:
        item = ActionItem(
            id=str(uuid.uuid4()),
            analysis_id=analysis.id,
            call_id=call_id,
            ref=act["ref"],
            type=act["type"],
            task=act["task"],
            modality=act["modality"],
            owner_text=act["owner_text"],
            owner_basis=act["owner_basis"],
            deadline_text=act["deadline_text"],
            utterance_id=act["utterance_id"],
            speaker_label=act["speaker_label"],
            quote=act["quote"],
            char_start=act["char_start"],
            char_end=act["char_end"]
        )
        db.add(item)

    # Persist Coaching Recommendations
    db.query(CoachingRecommendation).filter(CoachingRecommendation.call_id == call_id).delete()
    for coach in verified_coaching:
        rec = CoachingRecommendation(
            id=str(uuid.uuid4()),
            analysis_id=analysis.id,
            call_id=call_id,
            ref=coach["ref"],
            category=coach["category"],
            recommendation=coach["recommendation"],
            context_quote=coach.get("context_quote"),
            severity=coach.get("severity", "suggestion"),
            utterance_id=coach.get("utterance_id")
        )
        db.add(rec)

    db.commit()

    return {
        "message": f"Extracted {len(verified_actions)} verified action item(s) and {len(verified_coaching)} coaching recommendation(s).",
        "action_count": len(verified_actions),
        "coaching_count": len(verified_coaching)
    }
