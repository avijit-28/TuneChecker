import uuid
from sqlalchemy.orm import Session
from app.db.models.speaker_roles import SpeakerRole
from app.db.models.utterances import Utterance
from app.db.models.analyses import Analysis, EvidenceItem
from app.services.settings_service import SettingsService
from app.pipeline.providers.llm.ollama import OllamaLlmProvider
from app.pipeline.safeguards.tone_decision import evaluate_tone_verdict

TONE_ANALYSIS_SYSTEM = """You are a sales call quality tone evaluator. Your job is to detect whether a sales representative was rude, hostile, or dismissive to a customer.

CRITICAL INSTRUCTIONS:
1. Normal business courtesy, helpful explanations, polite answers, and scheduling follow-ups are NOT violations.
2. If the sales rep is polite, helpful, and professional, you MUST return:
   {"has_negative_tone": false, "candidate_findings": []}
3. ONLY flag clear, undeniable violations:
   - "rude": blatantly disrespectful, mocking, or offensive remarks
   - "hostile": shouting, verbal attacks, aggressive confrontations, or threats
   - "dismissive": outright refusing to answer or brushing off customer concerns ("not my problem", "whatever")

Output strictly valid JSON with this exact structure:
{
  "has_negative_tone": boolean,
  "candidate_findings": [
    {
      "utterance_id": string,
      "quote": string,
      "criterion_id": "rude" | "hostile" | "dismissive",
      "severity": 1 | 2 | 3,
      "rationale": string
    }
  ]
}

Example 1 (Polite Professional Call):
Utterances:
Utterance [a1]: "Thanks for joining today, happy to walk you through the product."
Utterance [a2]: "I completely understand your budget concerns. Let me follow up with pricing options."
Response:
{"has_negative_tone": false, "candidate_findings": []}

Example 2 (Unprofessional Call):
Utterances:
Utterance [b1]: "Are you kidding me right now? That is ridiculous."
Response:
{"has_negative_tone": true, "candidate_findings": [{"utterance_id": "b1", "quote": "Are you kidding me right now? That is ridiculous.", "criterion_id": "rude", "severity": 3, "rationale": "Rep insulted the customer."}]}
"""

def run_tone_stage(db: Session, call_id: str) -> dict:
    # 1. Identify rep speaker
    rep_role = (
        db.query(SpeakerRole)
        .filter(SpeakerRole.call_id == call_id, SpeakerRole.role == "sales_rep")
        .first()
    )

    active_settings = SettingsService.get_latest_settings(db)
    config = active_settings.config
    tone_config = config.get("tone", {})
    sensitivity = tone_config.get("sensitivity", "medium")
    enabled_criteria = {c["id"].lower() for c in tone_config.get("criteria", []) if c.get("enabled", True)}

    # Check existing analysis run_number
    latest_run = (
        db.query(Analysis)
        .filter(Analysis.call_id == call_id)
        .order_by(Analysis.run_number.desc())
        .first()
    )
    next_run = (latest_run.run_number + 1) if latest_run else 1

    if not rep_role or rep_role.status == "unresolved":
        # Cannot run tone without identified sales rep
        analysis = Analysis(
            id=str(uuid.uuid4()),
            call_id=call_id,
            run_number=next_run,
            settings_version=active_settings.version,
            status="partial",
            partial_reason="ROLES_UNRESOLVED",
            rep_speaker_label=None,
            roles_source=None
        )
        db.add(analysis)
        db.commit()
        return {"message": "Tone analysis skipped: speaker roles unresolved.", "verdict": None}

    # Fetch utterances
    all_utterances = db.query(Utterance).filter(Utterance.call_id == call_id).order_by(Utterance.idx.asc()).all()
    rep_utterances = [u for u in all_utterances if u.speaker_label == rep_role.speaker_label]

    rep_total_sec = sum((u.end_ms - u.start_ms) / 1000.0 for u in rep_utterances)

    rep_utt_dicts = [{"id": u.id, "speaker_label": u.speaker_label, "text": u.text} for u in rep_utterances]

    # Format prompt with rep utterances only
    formatted_rep_speech = "\n".join([f"Utterance [{u['id']}]: \"{u['text']}\"" for u in rep_utt_dicts])
    user_prompt = f"Evaluate the sales representative's utterances:\n\n{formatted_rep_speech}"

    candidate_findings = []
    try:
        llm = OllamaLlmProvider()
        res = llm.generate_json(TONE_ANALYSIS_SYSTEM, user_prompt)
        if res.get("has_negative_tone") is False:
            candidate_findings = []
        else:
            candidate_findings = res.get("candidate_findings", [])
    except Exception as e:
        candidate_findings = []

    # Safeguard decision
    decision = evaluate_tone_verdict(
        candidate_findings=candidate_findings,
        rep_utterances=rep_utt_dicts,
        enabled_criteria_ids=enabled_criteria,
        sensitivity=sensitivity,
        rep_total_seconds=rep_total_sec,
        role_level=rep_role.level or "medium"
    )

    analysis_id = str(uuid.uuid4())
    analysis = Analysis(
        id=analysis_id,
        call_id=call_id,
        run_number=next_run,
        settings_version=active_settings.version,
        status="complete",
        verdict=decision["verdict"],
        confidence_level=decision["confidence_level"],
        confidence_factors={"rep_seconds": rep_total_sec, "sensitivity": sensitivity},
        limited_evidence_reason=decision["limited_evidence_reason"],
        explanation=decision["explanation"],
        rep_speaker_label=rep_role.speaker_label,
        roles_source=rep_role.source,
        dropped_evidence_count=decision["dropped_evidence_count"],
        dropped_details=decision["dropped_details"],
        model_name=llm.model if 'llm' in locals() else "qwen2.5:1.5b-instruct",
        prompt_version="v1.0"
    )
    db.add(analysis)
    db.commit()

    # Save evidence items
    for ev in decision["evidence_items"]:
        item = EvidenceItem(
            id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            call_id=call_id,
            ref=ev["ref"],
            utterance_id=ev["utterance_id"],
            speaker_label=ev["speaker_label"],
            quote=ev["quote"],
            char_start=ev["char_start"],
            char_end=ev["char_end"],
            criterion_id=ev["criterion_id"],
            severity=ev["severity"],
            rationale=ev["rationale"]
        )
        db.add(item)
    db.commit()

    return {
        "message": f"Tone verdict: {decision['verdict']} ({decision['confidence_level']} confidence).",
        "verdict": decision["verdict"],
        "evidence_count": len(decision["evidence_items"])
    }
