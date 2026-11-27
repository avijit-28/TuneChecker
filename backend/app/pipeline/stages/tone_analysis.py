import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from app.config import settings
from app.db.models.calls import Call
from app.db.models.speaker_roles import SpeakerRole
from app.db.models.utterances import Utterance
from app.db.models.analyses import Analysis, EvidenceItem
from app.services.settings_service import SettingsService
from app.pipeline.providers.llm.ollama import OllamaLlmProvider
from app.pipeline.safeguards.tone_decision import evaluate_tone_verdict
from app.pipeline.safeguards.voice_acoustics import analyze_utterance_acoustics

TONE_ANALYSIS_SYSTEM = """You are a 2-layer (Text + Voice Acoustics) sales call quality tone evaluator. Your job is to detect whether a sales representative was rude, hostile, dismissive, or unprofessional to a customer.

CRITICAL INSTRUCTIONS:
1. You will receive Sales Rep utterances annotated with real [Voice Acoustics: ...] prosody tags (loudness vs baseline, pitch, vocal sharpness) AND read-only [Customer - CONTEXT ONLY] lines.
2. NEVER flag or cite [Customer - CONTEXT ONLY] utterances. Only evaluate and cite Sales Rep utterances.
3. Use BOTH the words AND the Voice Acoustics + Customer context to judge intent:
   - Playful banter or light teasing spoken in a [calm/normal voice] with friendly customer context is NOT hostile or rude.
   - Insulting, mocking, or aggressive remarks spoken in a [loud/agitated voice] or [tense/sharp voice] (or blatantly abusive language regardless of tone) MUST be flagged.
4. Normal business courtesy, helpful explanations, polite answers, and scheduling follow-ups are NOT violations.
5. If the sales rep is polite, helpful, and professional, you MUST return:
   {"has_negative_tone": false, "candidate_findings": []}
6. Flag violations matching these criteria:
   - "rude": blatantly disrespectful, mocking, or offensive remarks
   - "hostile": shouting, verbal attacks, aggressive confrontations, or threats
   - "dismissive": outright refusing to answer or brushing off customer concerns ("not my problem", "whatever")
   - "unprofessional": overly casual slang (e.g. calling prospect "bro", "baby", "dude") or inappropriate familiarity in business sales

Output strictly valid JSON with this exact structure:
{
  "has_negative_tone": boolean,
  "candidate_findings": [
    {
      "utterance_id": string,
      "quote": string,
      "criterion_id": "rude" | "hostile" | "dismissive" | "unprofessional",
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
Utterance [b1]: "Well, look, happy sales, bro. That's where it boils, baby."
Response:
{"has_negative_tone": true, "candidate_findings": [{"utterance_id": "b1", "quote": "Well, look, happy sales, bro.", "criterion_id": "unprofessional", "severity": 2, "rationale": "Rep used overly casual slang ('bro') addressing business prospect."}]}
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

    rep_utt_dicts = [
        {"id": u.id, "speaker_label": u.speaker_label, "text": u.text, "start_ms": u.start_ms, "end_ms": u.end_ms}
        for u in rep_utterances
    ]

    # Layer 2: Compute per-utterance voice acoustics (RMS dB, pitch F0, sharpness)
    call_row = db.query(Call).filter(Call.id == call_id).first()
    audio_path = (Path(settings.STORAGE_LOCAL_PATH) / call_row.storage_key) if (call_row and call_row.storage_key) else None
    acoustics_map = analyze_utterance_acoustics(audio_path, rep_utt_dicts) if audio_path else {}

    # Format prompt with Sales Rep utterances + Voice Acoustics + read-only Customer context
    prompt_lines = []
    for u in all_utterances:
        if u.speaker_label == rep_role.speaker_label:
            ac = acoustics_map.get(str(u.id))
            ac_tag = f" [Voice Acoustics: {ac['tag']}]" if ac else ""
            prompt_lines.append(f"Sales Rep Utterance [{u.id}]{ac_tag}: \"{u.text}\"")
        else:
            prompt_lines.append(f"[Customer - CONTEXT ONLY, NEVER flag]: \"{u.text}\"")
    formatted_conversation = "\n".join(prompt_lines)
    user_prompt = f"Evaluate ONLY the Sales Rep utterances using both text and Voice Acoustics:\n\n{formatted_conversation}"

    candidate_findings = []
    try:
        llm = OllamaLlmProvider()
        res = llm.generate_json(TONE_ANALYSIS_SYSTEM, user_prompt)
        if res.get("has_negative_tone") is False:
            candidate_findings = []
        else:
            candidate_findings = res.get("candidate_findings", [])
    except Exception:
        candidate_findings = []

    # Enrich findings with measured voice acoustics & boost severity for extreme shouting
    for f in candidate_findings:
        if not isinstance(f, dict):
            continue
        uid = str(f.get("utterance_id", ""))
        ac = acoustics_map.get(uid)
        if ac:
            if ac.get("emotion_hint") == "loud_or_agitated" and ac.get("delta_db", 0.0) >= 7.0:
                f["severity"] = min(3, int(f.get("severity", 2)) + 1)
            rationale = str(f.get("rationale", "")).strip()
            f["rationale"] = f"{rationale} [Voice: {ac['tag']}]".strip()

    # Safeguard decision
    decision = evaluate_tone_verdict(
        candidate_findings=candidate_findings,
        rep_utterances=rep_utt_dicts,
        enabled_criteria_ids=enabled_criteria,
        sensitivity=sensitivity,
        rep_total_seconds=rep_total_sec,
        role_level=rep_role.level or "medium",
        role_status=rep_role.status or "resolved"
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
