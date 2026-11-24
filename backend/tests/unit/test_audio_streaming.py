import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.db.session import SessionLocal
from app.db.models.calls import Call
from tests.fixtures.audio_fixtures import create_synthetic_wav_file

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_audio_stream_full_file(client, db):
    call_id = f"test-unit-audio-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.wav"
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / storage_key
    create_synthetic_wav_file(audio_path, duration_sec=1.5)
    file_size = audio_path.stat().st_size

    call = Call(id=call_id, original_filename="customer_call.wav", size_bytes=file_size, storage_key=storage_key)
    db.add(call)
    db.commit()

    try:
        r = client.get(f"/api/v1/calls/{call_id}/audio")
        assert r.status_code == 200
        assert r.headers.get("accept-ranges") == "bytes"
        assert r.headers.get("content-type") == "audio/wav"
        assert len(r.content) == file_size
    finally:
        if audio_path.exists():
            audio_path.unlink()
        db.delete(call)
        db.commit()

def test_audio_stream_range_requests(client, db):
    call_id = f"test-unit-range-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.wav"
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / storage_key
    create_synthetic_wav_file(audio_path, duration_sec=2.0)
    file_size = audio_path.stat().st_size

    call = Call(id=call_id, original_filename="range_call.wav", size_bytes=file_size, storage_key=storage_key)
    db.add(call)
    db.commit()

    try:
        # Range 0-511 (512 bytes)
        r1 = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=0-511"})
        assert r1.status_code == 206
        assert len(r1.content) == 512
        assert f"bytes 0-511/{file_size}" == r1.headers.get("Content-Range")

        # Range 512-1023 (512 bytes)
        r2 = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=512-1023"})
        assert r2.status_code == 206
        assert len(r2.content) == 512
        assert f"bytes 512-1023/{file_size}" == r2.headers.get("Content-Range")

        # Suffix range (last 256 bytes)
        r3 = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=-256"})
        assert r3.status_code == 206
        assert len(r3.content) == 256
        assert f"bytes {file_size - 256}-{file_size - 1}/{file_size}" == r3.headers.get("Content-Range")
    finally:
        if audio_path.exists():
            audio_path.unlink()
        db.delete(call)
        db.commit()

def test_audio_stream_not_found_handling(client, db):
    # Non-existent call ID
    r1 = client.get("/api/v1/calls/missing-call-id-9999/audio")
    assert r1.status_code == 404

    # Call with missing file on disk
    call_id = f"test-missing-file-{uuid.uuid4().hex[:8]}"
    call = Call(id=call_id, original_filename="ghost.wav", size_bytes=1000, storage_key="ghost_nonexistent.wav")
    db.add(call)
    db.commit()

    try:
        r2 = client.get(f"/api/v1/calls/{call_id}/audio")
        assert r2.status_code == 404
    finally:
        db.delete(call)
        db.commit()
