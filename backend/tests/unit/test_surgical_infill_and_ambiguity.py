import uuid
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.calls import Call
from app.db.models.transcripts import Transcript
from app.db.models.utterances import Utterance
from app.db.models.speaker_roles import SpeakerRole
from app.db.models.analyses import Analysis
from app.pipeline.providers.stt.base import SttSegment
from app.pipeline.stages.transcription import surgically_infill_segments
from app.pipeline.stages.speaker_roles import run_speaker_roles_stage
from app.pipeline.stages.tone_analysis import run_tone_stage

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_surgically_infill_segments_empty_candidates():
    # If segments have good confidence, surgical infilling does nothing
    segs = [
        SttSegment(id="s1", text="Hello world", start_ms=0, end_ms=2000, confidence=0.92, words=[]),
        SttSegment(id="s2", text="Thank you for calling", start_ms=2100, end_ms=4500, confidence=0.88, words=[]),
    ]
    res = surgically_infill_segments(segs, Path("fake.wav"))
    assert len(res) == 2
    assert res[0].text == "Hello world"
    assert res[1].text == "Thank you for calling"

def test_short_call_snippet_ambiguity_protection(db, monkeypatch):
    """
    Test that a short/mid-call snippet (<= 3 utterances, < 25 words) with no greeting
    is assigned 'low' role confidence and does not trigger an unfair RED penalty.
    """
    monkeypatch.setattr(
        "app.pipeline.providers.llm.ollama.OllamaLlmProvider.generate_json",
        lambda self, sys, usr: {
            "has_negative_tone": True,
            "candidate_findings": [
                {
                    "utterance_id": "u-mock-1",
                    "quote": "Haan theek hai, kal se nahi milenge.",
                    "criterion_id": "dismissive",
                    "severity": 3,
                    "rationale": "Dismissive and aggressive statement."
                }
            ]
        }
    )
    call_id = f"test-ambig-{uuid.uuid4().hex[:8]}"
    call = Call(
        id=call_id,
        original_filename="heated_short_snippet.wav",
        size_bytes=4096,
        storage_key=f"{call_id}.wav",
        status="complete"
    )
    db.add(call)

    transcript = Transcript(call_id=call_id, status="completed", provider="faster_whisper")
    db.add(transcript)

    # Short 2-utterance snippet: "Haan theek hai, kal se nahi milenge"
    role_a = SpeakerRole(call_id=call_id, speaker_label="A", role="unknown", source="auto", status="unresolved", level="low")
    role_b = SpeakerRole(call_id=call_id, speaker_label="B", role="unknown", source="auto", status="unresolved", level="low")
    db.add_all([role_a, role_b])

    utts = [
        Utterance(id=f"u-{call_id}-1", call_id=call_id, idx=0, speaker_label="A", start_ms=0, end_ms=2500,
                  text="Haan theek hai, kal se nahi milenge."),
        Utterance(id=f"u-{call_id}-2", call_id=call_id, idx=1, speaker_label="B", start_ms=2600, end_ms=4800,
                  text="Okay, whatever you know.")
    ]
    db.add_all(utts)
    db.commit()

    try:
        # Run speaker roles stage
        roles_res = run_speaker_roles_stage(db, call_id)
        assert roles_res["confidence"] == "low"

        # Check DB speaker role rows
        rep = db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id, SpeakerRole.role == "sales_rep").first()
        assert rep is not None
        assert rep.level == "low"
        assert rep.status == "uncertain"

        # Run tone stage - since confidence is low, verdict MUST be NEEDS_REVIEW, never RED!
        tone_res = run_tone_stage(db, call_id)
        assert tone_res["verdict"] in ["NEEDS_REVIEW", "GREEN"]
        assert tone_res["verdict"] != "RED"

        analysis = db.query(Analysis).filter(Analysis.call_id == call_id).first()
        assert analysis.verdict != "RED"
        assert analysis.confidence_level == "low"
    finally:
        db.query(Analysis).filter(Analysis.call_id == call_id).delete()
        db.query(Utterance).filter(Utterance.call_id == call_id).delete()
        db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id).delete()
        db.query(Transcript).filter(Transcript.call_id == call_id).delete()
        db.query(Call).filter(Call.id == call_id).delete()
        db.commit()
