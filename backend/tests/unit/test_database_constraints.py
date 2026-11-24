import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["settings"] == "ok"
    assert data["checks"]["ffmpeg"] == "ok"

def test_settings_endpoints(client):
    # GET settings
    r = client.get("/api/v1/settings")
    assert r.status_code == 200
    data = r.json()
    assert data["version"] >= 1
    assert data["sensitivity"] == "medium"
    assert "tone" in data["config"]

    # PUT settings invalid sensitivity
    bad_payload = dict(data["config"])
    bad_payload["tone"]["sensitivity"] = "ultra_high"
    r_bad = client.put("/api/v1/settings", json=bad_payload)
    assert r_bad.status_code == 422
    err = r_bad.json()
    assert "error" in err
    assert err["error"]["code"] == "REQUEST_INVALID"

    # POST reset
    r_reset = client.post("/api/v1/settings/reset")
    assert r_reset.status_code == 200
    assert r_reset.json()["source"] == "reset"

def test_dashboard_summary_zero_state(client):
    r = client.get("/api/v1/dashboard/summary")
    assert r.status_code == 200
    data = r.json()
    assert "kpis" in data
    assert "tone_distribution" in data
    assert isinstance(data["recent_calls"], list)

def test_calls_list_and_404(client):
    # List calls
    r = client.get("/api/v1/calls")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data

    # 404 for unknown call
    r_not_found = client.get("/api/v1/calls/non-existent-uuid")
    assert r_not_found.status_code == 404
    err = r_not_found.json()
    assert err["error"]["code"] == "CALL_NOT_FOUND"

def test_trigger_settings_versions_immutable(db):
    # Updating settings_versions must be aborted by trigger
    with pytest.raises(Exception) as exc:
        db.execute(text("UPDATE settings_versions SET sensitivity='high' WHERE version=1"))
        db.commit()
    assert "settings_versions rows are immutable" in str(exc.value)
    db.rollback()

    # Deleting settings_versions must be aborted by trigger
    with pytest.raises(Exception) as exc:
        db.execute(text("DELETE FROM settings_versions WHERE version=1"))
        db.commit()
    assert "settings_versions rows cannot be deleted" in str(exc.value)
    db.rollback()

def test_auditor_feedback_endpoints(client):
    # Feedback train endpoint with low data
    r_train = client.post("/api/v1/calls/feedback/train")
    assert r_train.status_code == 200
    res = r_train.json()
    assert res["status"] in ("not_enough_data", "need_more_examples", "success")

def test_speaker_alignment_pauses():
    from app.pipeline.providers.stt.base import SttSegment
    from app.pipeline.safeguards.speaker_alignment import align_segments_to_speakers

    # 500ms pause should NOT switch speaker (stays with same speaker during breath pauses)
    segs = [
        SttSegment(id="1", text="Hello I am calling from software company", start_ms=0, end_ms=2000, words=[]),
        SttSegment(id="2", text="and I wanted to show you our platform", start_ms=2500, end_ms=4500, words=[]), # 500ms pause
        SttSegment(id="3", text="Who is this please?", start_ms=6000, end_ms=7500, words=[]), # 1500ms pause -> should alternate!
    ]
    aligned = align_segments_to_speakers(segs)
    assert aligned[0].speaker_label == "A"
    assert aligned[1].speaker_label == "A" # Kept as same speaker because pause <= 1200ms
    assert aligned[2].speaker_label == "B" # Switched because pause > 1200ms

def test_analysis_verdict_constraints(db):
    import uuid
    from app.db.models.calls import Call
    from app.db.models.analyses import Analysis

    call_id = f"test-call-{uuid.uuid4().hex[:8]}"
    test_call = Call(
        id=call_id,
        original_filename="test.mp3",
        storage_key="test.mp3",
        size_bytes=1000,
        duration_ms=20000,
        status="uploaded"
    )
    db.add(test_call)
    db.commit()

    try:
        # Test 1: NEEDS_REVIEW is permitted
        a_review = Analysis(
            id=f"analysis-{uuid.uuid4().hex[:8]}",
            call_id=call_id,
            run_number=1,
            settings_version=1,
            status="complete",
            verdict="NEEDS_REVIEW",
            confidence_level="medium",
            explanation="Uncertain tone evidence requires human review."
        )
        db.add(a_review)
        db.commit()
        assert a_review.verdict == "NEEDS_REVIEW"

        # Test 2: GREEN and RED and None are permitted
        a_green = Analysis(
            id=f"analysis-{uuid.uuid4().hex[:8]}",
            call_id=call_id,
            run_number=2,
            settings_version=1,
            status="complete",
            verdict="GREEN"
        )
        db.add(a_green)
        db.commit()
        assert a_green.verdict == "GREEN"

        a_none = Analysis(
            id=f"analysis-{uuid.uuid4().hex[:8]}",
            call_id=call_id,
            run_number=3,
            settings_version=1,
            status="partial",
            verdict=None
        )
        db.add(a_none)
        db.commit()
        assert a_none.verdict is None

        # Test 3: Invalid verdict raises IntegrityError
        a_bad = Analysis(
            id=f"analysis-{uuid.uuid4().hex[:8]}",
            call_id=call_id,
            run_number=4,
            settings_version=1,
            status="complete",
            verdict="INVALID_VERDICT"
        )
        db.add(a_bad)
        with pytest.raises(Exception) as exc:
            db.commit()
        assert "ck_analyses_verdict" in str(exc.value) or "CHECK constraint failed" in str(exc.value)
        db.rollback()

    finally:
        db.query(Analysis).filter(Analysis.call_id == call_id).delete()
        db.query(Call).filter(Call.id == call_id).delete()
        db.commit()
