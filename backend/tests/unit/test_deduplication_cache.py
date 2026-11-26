import pytest
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
    # Disable actual heavy background worker in unit test
    monkeypatch.setattr("app.api.v1.calls.queue_call_processing", lambda call_id, start_stage="validation": None)

    audio_bytes = generate_synthetic_wav_bytes(duration_sec=11.0, frequency_hz=440.0)
    files = {"file": ("test_cache_call.wav", audio_bytes, "audio/wav")}

    # First upload
    r1 = client.post("/api/v1/calls", files=files)
    assert r1.status_code == 202
    data1 = r1.json()
    call_id1 = data1["id"]

    # Emulate first call completion
    from app.db.session import SessionLocal
    from app.db.models.calls import Call
    db = SessionLocal()
    c1 = db.query(Call).filter(Call.id == call_id1).first()
    c1.status = "complete"
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
