import uuid
import random
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from tests.fixtures.audio_fixtures import generate_synthetic_wav_bytes

@pytest.fixture
def client():
    return TestClient(app)

def test_audio_fingerprint_deduplication_cache(client, monkeypatch):
    """
    Verifies that uploading the exact same audio bytes a second time
    instantly returns the completed analysis via content hash cache,
    consuming 0 LLM tokens and 0 Whisper compute seconds.
    """
    import random
    # Disable actual heavy background worker in unit test
    monkeypatch.setattr("app.api.v1.calls.queue_call_processing", lambda call_id, start_stage="validation": None)

    # Use unique audio bytes for this test run so it doesn't collide with persistent DB from previous runs
    freq = float(random.randint(220, 880))
    audio_bytes = generate_synthetic_wav_bytes(duration_sec=11.0, frequency_hz=freq) + uuid.uuid4().bytes[:16]
    files = {"file": ("test_cache_call.wav", audio_bytes, "audio/wav")}

    # First upload
    r1 = client.post("/api/v1/calls", files=files)
    assert r1.status_code == 202
    data1 = r1.json()
    call_id1 = data1["id"]

    # Emulate first call completion with full analysis entities
    from app.db.session import SessionLocal
    from app.db.models.calls import Call
    from app.db.models.analyses import Analysis, EvidenceItem, ActionItem, CoachingRecommendation
    from app.db.models.utterances import Utterance
    from app.db.models.speaker_roles import SpeakerRole
    from app.db.models.transcripts import Transcript

    db = SessionLocal()
    c1 = db.query(Call).filter(Call.id == call_id1).first()
    c1.status = "complete"

    t1 = Transcript(call_id=call_id1, status="completed", provider="faster_whisper")
    u1 = Utterance(id=str(uuid.uuid4()), call_id=call_id1, idx=0, speaker_label="A", start_ms=0, end_ms=2000, text="Hello there.")
    r1_role = SpeakerRole(call_id=call_id1, speaker_label="A", role="sales_rep", source="auto", status="confirmed")
    a1 = Analysis(
        id=str(uuid.uuid4()),
        call_id=call_id1,
        run_number=1,
        settings_version=1,
        status="complete",
        verdict="GREEN",
        confidence_level="high",
        rep_speaker_label="A",
        roles_source="auto",
        created_at=datetime.utcnow()
    )
    act1 = ActionItem(
        id=str(uuid.uuid4()),
        analysis_id=a1.id,
        call_id=call_id1,
        ref="A1",
        type="commitment",
        task="Follow up with client",
        modality="definite",
        utterance_id=u1.id,
        speaker_label="A",
        quote="Hello there.",
        char_start=0,
        char_end=12,
        created_at=datetime.utcnow()
    )
    coach1 = CoachingRecommendation(
        id=str(uuid.uuid4()),
        analysis_id=a1.id,
        call_id=call_id1,
        ref="C1",
        category="professionalism",
        recommendation="Good opening greeting.",
        severity="suggestion",
        utterance_id=u1.id,
        created_at=datetime.utcnow()
    )
    db.add_all([t1, u1, r1_role, a1, act1, coach1])
    db.commit()
    db.close()

    # Second upload of identical audio
    files2 = {"file": ("test_cache_call_copy.wav", audio_bytes, "audio/wav")}
    r2 = client.post("/api/v1/calls", files=files2)
    assert r2.status_code == 202
    data2 = r2.json()

    # Must be marked cached
    assert data2["cached"] is True
    assert data2["status"] == "complete"

    # Verify cloned analysis in DB
    db2 = SessionLocal()
    c2 = db2.query(Call).filter(Call.id == data2["id"]).first()
    assert c2.status == "complete"
    a2 = db2.query(Analysis).filter(Analysis.call_id == c2.id).first()
    assert a2 is not None
    assert a2.verdict == "GREEN"
    act2 = db2.query(ActionItem).filter(ActionItem.call_id == c2.id).first()
    assert act2 is not None
    assert act2.task == "Follow up with client"
    coach2 = db2.query(CoachingRecommendation).filter(CoachingRecommendation.call_id == c2.id).first()
    assert coach2 is not None
    assert coach2.recommendation == "Good opening greeting."
    db2.close()
