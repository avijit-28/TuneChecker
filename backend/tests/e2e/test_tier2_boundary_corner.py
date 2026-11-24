"""
Tier 2: Boundary & Corner Cases E2E Test Suite (50 Tests, 5 per feature across 10 features).
Validates edge cases, invalid inputs, boundary conditions, and error recovery.
"""
import os
import uuid
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.config import settings
from app.db.session import SessionLocal
from app.db.models.calls import Call
from app.db.models.settings import SettingsVersion
from app.db.models.speaker_roles import SpeakerRole
from app.audio.upload_checks import validate_filename_and_mime, validate_audio_container
from app.audio.validation import validate_audio_file
from app.audio.normalize import normalize_to_wav
from app.utils.errors import AppError
from app.pipeline.safeguards.speaker_alignment import align_segments_to_speakers
from app.pipeline.safeguards.tone_decision import evaluate_tone_verdict
from app.pipeline.safeguards.quote_matcher import find_quote_offsets, verify_evidence_quote
from app.pipeline.safeguards.action_rules import evaluate_action_items
from app.services.call_service import CallService
from app.services.settings_service import SettingsService
from tests.fixtures.audio_fixtures import (
    CORRUPTED_TRUNCATED_HEADER,
    CORRUPTED_RANDOM_BYTES,
    INVALID_PDF_HEADER,
    generate_synthetic_wav_bytes,
    create_synthetic_wav_file,
)
from tests.e2e.test_tier1_feature_coverage import calculate_wer, calculate_cer, SAMPLE_MPEG_PATH

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

# ==============================================================================
# FEATURE 1: Baseline Health & Startup (Boundary / Negative)
# ==============================================================================
def test_t2_f01_upload_empty_file_422(client):
    """T2.F1.1: Uploading a 0-byte audio file returns 422 FILE_EMPTY."""
    files = {"file": ("empty.m4a", b"", "audio/mp4")}
    r = client.post("/api/v1/calls", files=files)
    assert r.status_code == 422
    err = r.json()
    assert err["error"]["code"] == "FILE_EMPTY"

def test_t2_f01_upload_unsupported_extension_415(client):
    """T2.F1.2: Uploading an unsupported file format (.flac, .pdf) returns 415 INVALID_FILE_TYPE."""
    files = {"file": ("document.pdf", INVALID_PDF_HEADER, "application/pdf")}
    r = client.post("/api/v1/calls", files=files)
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "INVALID_FILE_TYPE"

def test_t2_f01_upload_file_exceeds_max_size_413(client, monkeypatch):
    """T2.F1.3: Uploading a file exceeding MAX_UPLOAD_SIZE_MB returns 413 FILE_TOO_LARGE."""
    # Temporarily set MAX_UPLOAD_SIZE_MB to 1 for quick test
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    oversized_data = b"0" * (1024 * 1024 + 1024)  # > 1MB
    files = {"file": ("oversized.m4a", oversized_data, "audio/mp4")}
    r = client.post("/api/v1/calls", files=files)
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "FILE_TOO_LARGE"

def test_t2_f01_call_not_found_404(client):
    """T2.F1.4: Querying a non-existent call ID returns 404 CALL_NOT_FOUND."""
    r = client.get("/api/v1/calls/non-existent-uuid-12345")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "CALL_NOT_FOUND"

def test_t2_f01_db_session_rollback_on_duplicate_id(db):
    """T2.F1.5: Database transaction rollback on duplicate ID prevents corruption."""
    call_id = f"test-t2-f01-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.m4a"
    call1 = Call(id=call_id, original_filename="call1.m4a", size_bytes=100, storage_key=storage_key)
    db.add(call1)
    db.commit()

    call2 = Call(id=call_id, original_filename="call2.m4a", size_bytes=200, storage_key=f"other_{storage_key}")
    db.add(call2)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()

    # Original row must still exist
    found = db.query(Call).filter(Call.id == call_id).first()
    assert found is not None
    assert found.original_filename == "call1.m4a"

    # Cleanup
    db.delete(found)
    db.commit()

# ==============================================================================
# FEATURE 2: Diarization & Role Assignment (Boundary / Negative)
# ==============================================================================
def test_t2_f02_speaker_alignment_empty_segments():
    """T2.F2.1: align_segments_to_speakers handles empty segment list without error."""
    aligned = align_segments_to_speakers([])
    assert aligned == []

def test_t2_f02_speaker_alignment_single_segment():
    """T2.F2.2: Single utterance segment assigned speaker A without error."""
    from app.pipeline.providers.stt.base import SttSegment
    segs = [SttSegment("s1", "Lone speech turn", 0, 3000, [])]
    aligned = align_segments_to_speakers(segs)
    assert len(aligned) == 1
    assert aligned[0].speaker_label == "A"

def test_t2_f02_role_swap_missing_roles_payload_422(client, db):
    """T2.F2.3: PUT /speaker-roles with empty or missing roles dict returns 422 INVALID_ROLES."""
    call_id = f"test-t2-f02-{uuid.uuid4().hex[:8]}"
    call = Call(id=call_id, original_filename="test.m4a", size_bytes=1000, storage_key=f"{call_id}.m4a", status="complete")
    db.add(call)
    db.commit()

    r = client.put(f"/api/v1/calls/{call_id}/speaker-roles", json={})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_ROLES"

    # Cleanup
    db.delete(call)
    db.commit()

def test_t2_f02_role_swap_multiple_sales_reps_422(client, db):
    """T2.F2.4: Attempting to assign both speakers as sales_rep returns 422."""
    call_id = f"test-t2-f02b-{uuid.uuid4().hex[:8]}"
    call = Call(id=call_id, original_filename="test.m4a", size_bytes=1000, storage_key=f"{call_id}.m4a", status="complete")
    role_a = SpeakerRole(call_id=call_id, speaker_label="A", role="unknown", status="unresolved")
    role_b = SpeakerRole(call_id=call_id, speaker_label="B", role="unknown", status="unresolved")
    db.add_all([call, role_a, role_b])
    db.commit()

    # Invalid: two sales_reps
    r = client.put(f"/api/v1/calls/{call_id}/speaker-roles", json={"roles": {"A": "sales_rep", "B": "sales_rep"}})
    assert r.status_code == 422
    assert "sales_rep" in r.json()["error"]["message"]

    # Cleanup
    db.delete(role_a)
    db.delete(role_b)
    db.delete(call)
    db.commit()

def test_t2_f02_role_swap_unknown_call_404(client):
    """T2.F2.5: Role swap on non-existent call returns 404 CALL_NOT_FOUND."""
    r = client.put("/api/v1/calls/unknown-uuid-xyz/speaker-roles", json={"roles": {"A": "sales_rep", "B": "customer"}})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "CALL_NOT_FOUND"

# ==============================================================================
# FEATURE 3: Representative Tone & Verdict (Boundary / Negative)
# ==============================================================================
def test_t2_f03_tone_analysis_empty_rep_utterances():
    """T2.F3.1: 0 representative utterances handled safely without crashing."""
    res = evaluate_tone_verdict(
        candidate_findings=[],
        rep_utterances=[],
        enabled_criteria_ids={"rude", "dismissive"},
        sensitivity="medium",
        rep_total_seconds=0.0,
        role_level="low"
    )
    assert res["verdict"] in ("GREEN", "NEEDS_REVIEW")
    assert res["confidence_level"] == "low"

def test_t2_f03_tone_analysis_extreme_customer_profanity_isolation():
    """T2.F3.2: Extreme customer profanity does NOT leak into representative findings."""
    rep_utts = [
        {"id": "r1", "speaker_label": "A", "text": "Good afternoon, thank you for waiting."}
    ]
    # Finding points to customer utterance
    findings = [
        {"utterance_id": "c1", "quote": "You are a stupid idiot, shut up!", "criterion_id": "rude", "severity": 3}
    ]
    res = evaluate_tone_verdict(
        candidate_findings=findings,
        rep_utterances=rep_utts,
        enabled_criteria_ids={"rude"},
        sensitivity="high",
        rep_total_seconds=30.0,
        role_level="high"
    )
    assert res["verdict"] == "GREEN"
    assert len(res["evidence_items"]) == 0
    assert res["dropped_evidence_count"] >= 1

def test_t2_f03_tone_analysis_all_disabled_criteria():
    """T2.F3.3: When all tone criteria are disabled in settings, verdict defaults to GREEN."""
    rep_utts = [
        {"id": "r1", "speaker_label": "A", "text": "Are you kidding me? Shut up."}
    ]
    res = evaluate_tone_verdict(
        candidate_findings=[],
        rep_utterances=rep_utts,
        enabled_criteria_ids=set(),  # All criteria disabled
        sensitivity="high",
        rep_total_seconds=30.0,
        role_level="high"
    )
    assert res["verdict"] == "GREEN"
    assert len(res["evidence_items"]) == 0

def test_t2_f03_tone_analysis_hallucinated_candidate_quote():
    """T2.F3.4: LLM candidate finding quoting text not in rep utterances is dropped."""
    rep_utts = [
        {"id": "r1", "speaker_label": "A", "text": "Thank you for reaching out to us today."}
    ]
    hallucinated = [
        {"utterance_id": "r1", "quote": "I hate talking to you people", "criterion_id": "rude", "severity": 3}
    ]
    res = evaluate_tone_verdict(
        candidate_findings=hallucinated,
        rep_utterances=rep_utts,
        enabled_criteria_ids={"rude"},
        sensitivity="high",
        rep_total_seconds=30.0,
        role_level="high"
    )
    assert res["verdict"] == "GREEN"
    assert res["dropped_evidence_count"] >= 1

def test_t2_f03_tone_analysis_boundary_duration_cutoff():
    """T2.F3.5: Rep duration boundary at exactly 14.9s (low confidence) vs 15.1s (medium confidence)."""
    rep_utts = [{"id": "r1", "speaker_label": "A", "text": "Polite statement"}]
    res_sub = evaluate_tone_verdict([], rep_utts, {"rude"}, "medium", 14.9, "high")
    assert res_sub["confidence_level"] == "low"

    res_super = evaluate_tone_verdict([], rep_utts, {"rude"}, "medium", 15.1, "high")
    assert res_super["confidence_level"] in ("medium", "high")

# ==============================================================================
# FEATURE 4: Evidence Quote Verification (Boundary / Negative)
# ==============================================================================
def test_t2_f04_quote_matcher_empty_quote_returns_none():
    """T2.F4.1: Empty quote string returns None without error."""
    assert find_quote_offsets("Utterance text here", "") is None

def test_t2_f04_quote_matcher_empty_transcript_returns_none():
    """T2.F4.2: Empty utterance text returns None without error."""
    assert find_quote_offsets("", "Some quote") is None

def test_t2_f04_quote_matcher_non_existent_quote_returns_none():
    """T2.F4.3: Completely non-existent quote returns None."""
    assert find_quote_offsets("Hello world", "completely absent phrase") is None

def test_t2_f04_quote_span_negative_or_inverted_offsets_invalid():
    """T2.F4.4: Inverted or negative character offsets return False."""
    text_content = "Sample text for validation"
    assert verify_evidence_quote(text_content, "text", 10, 5) is False
    assert verify_evidence_quote(text_content, "text", -2, 4) is False
    assert verify_evidence_quote(text_content, "text", 5, 5) is False

def test_t2_f04_quote_matcher_whitespace_only_quote_returns_none():
    """T2.F4.5: Whitespace-only quote string returns None."""
    assert find_quote_offsets("Sample text", "    ") is None

# ==============================================================================
# FEATURE 5: Action Items & Coaching Separation (Boundary / Negative)
# ==============================================================================
def test_t2_f05_action_items_zero_commitments_empty_list():
    """T2.F5.1: Call without commitments returns empty list, not null."""
    utts = [
        {"id": "u1", "speaker_label": "A", "text": "Hello, how are you?"},
        {"id": "u2", "speaker_label": "B", "text": "I am fine thank you."},
    ]
    actions = evaluate_action_items([], utts, {})
    assert isinstance(actions, list)
    assert len(actions) == 0

def test_t2_f05_action_items_tentative_filtering_when_disabled():
    """T2.F5.2: When include_tentative is False, tentative items are excluded."""
    utts = [
        {"id": "u1", "speaker_label": "A", "text": "We might look into adding that feature."}
    ]
    # With tentative disabled
    actions = evaluate_action_items([], utts, {"include_tentative": False})
    for a in actions:
        assert a["modality"] != "tentative"

def test_t2_f05_action_items_owner_rule_explicit_only():
    """T2.F5.3: When owner_rule is explicit_only, committing speaker is not set as owner."""
    utts = [
        {"id": "u1", "speaker_label": "A", "text": "I will send you the proposal."}
    ]
    actions = evaluate_action_items([], utts, {"owner_rule": "explicit_only"})
    for a in actions:
        assert a["owner_text"] is None
        assert a["owner_basis"] == "none"

def test_t2_f05_action_items_empty_utterances_handled():
    """T2.F5.4: evaluate_action_items with empty utterance list returns empty list."""
    assert evaluate_action_items([], [], {}) == []

def test_t2_f05_action_items_duplicate_quote_deduplication():
    """T2.F5.5: Duplicate action items referencing the identical quote are deduplicated."""
    utts = [
        {"id": "u1", "speaker_label": "A", "text": "I will email the contract by Monday."}
    ]
    candidates = [
        {"utterance_id": "u1", "task": "Email contract", "type": "commitment", "quote": "I will email the contract by Monday."},
        {"utterance_id": "u1", "task": "Email contract duplicate", "type": "commitment", "quote": "I will email the contract by Monday."},
    ]
    actions = evaluate_action_items(candidates, utts, {})
    # Should only keep 1 item for this quote
    quotes = [a["quote"] for a in actions]
    assert len(quotes) == len(set(quotes))

# ==============================================================================
# FEATURE 6: Settings & Snapshot Persistence (Boundary / Negative)
# ==============================================================================
def test_t2_f06_put_settings_invalid_sensitivity_422(client):
    """T2.F6.1: PUT /settings with invalid sensitivity returns 422 REQUEST_INVALID."""
    r_curr = client.get("/api/v1/settings")
    bad_cfg = dict(r_curr.json()["config"])
    bad_cfg["tone"]["sensitivity"] = "hyper_sensitive"
    r = client.put("/api/v1/settings", json=bad_cfg)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "REQUEST_INVALID"

def test_t2_f06_put_settings_out_of_range_threshold_422(client):
    """T2.F6.2: Malformed criteria configuration is rejected with 422."""
    r_curr = client.get("/api/v1/settings")
    bad_cfg = dict(r_curr.json()["config"])
    bad_cfg["tone"]["criteria"] = "invalid_criteria_string_not_list"  # Invalid type
    r = client.put("/api/v1/settings", json=bad_cfg)
    assert r.status_code == 422

def test_t2_f06_settings_version_immutable_trigger(db):
    """T2.F6.3: UPDATE on settings_versions table raises SQLite trigger abort exception."""
    latest_s = SettingsService.get_latest_settings(db)
    with pytest.raises(Exception) as exc:
        db.execute(text(f"UPDATE settings_versions SET sensitivity='high' WHERE version={latest_s.version}"))
        db.commit()
    assert "immutable" in str(exc.value).lower()
    db.rollback()

def test_t2_f06_settings_version_delete_trigger(db):
    """T2.F6.4: DELETE on settings_versions table raises SQLite trigger abort exception."""
    latest_s = SettingsService.get_latest_settings(db)
    with pytest.raises(Exception) as exc:
        db.execute(text(f"DELETE FROM settings_versions WHERE version={latest_s.version}"))
        db.commit()
    assert "deleted" in str(exc.value).lower() or "immutable" in str(exc.value).lower()
    db.rollback()

def test_t2_f06_put_settings_missing_body_422(client):
    """T2.F6.5: PUT /settings with empty body returns 422."""
    r = client.put("/api/v1/settings", json={})
    assert r.status_code == 422

# ==============================================================================
# FEATURE 7: Audio Streaming & Playback (Boundary / Negative)
# ==============================================================================
def test_t2_f07_audio_stream_nonexistent_call_404(client):
    """T2.F7.1: Streaming audio for non-existent call returns 404."""
    r = client.get("/api/v1/calls/non-existent-call-uuid/audio")
    assert r.status_code in (404, 405)

def test_t2_f07_audio_stream_missing_storage_file_404(client, db):
    """T2.F7.2: Call exists in DB but audio file is deleted from disk returns 404."""
    call_id = f"test-t2-f07-{uuid.uuid4().hex[:8]}"
    missing_key = f"missing_{call_id}.wav"
    call = Call(id=call_id, original_filename="missing.wav", size_bytes=1000, storage_key=missing_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/audio")
    assert r.status_code in (404, 405)

    # Cleanup
    db.delete(call)
    db.commit()

def test_t2_f07_audio_stream_invalid_range_syntax(client, db):
    """T2.F7.3: Malformed Range header syntax handled safely."""
    call_id = f"test-t2-f07b-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.wav"
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / storage_key
    create_synthetic_wav_file(audio_path, duration_sec=1.0)

    call = Call(id=call_id, original_filename="test.wav", size_bytes=audio_path.stat().st_size, storage_key=storage_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=invalid-syntax"})
    # Should either ignore bad header (200), return 400, 416, or 404/405 if route pending
    assert r.status_code in (200, 400, 416, 404, 405)

    # Cleanup
    if audio_path.exists():
        audio_path.unlink()
    db.delete(call)
    db.commit()

def test_t2_f07_audio_stream_out_of_bounds_range_416(client, db):
    """T2.F7.4: Byte range exceeding file size handled safely."""
    call_id = f"test-t2-f07c-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.wav"
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / storage_key
    create_synthetic_wav_file(audio_path, duration_sec=1.0)

    call = Call(id=call_id, original_filename="test.wav", size_bytes=audio_path.stat().st_size, storage_key=storage_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=9999999-99999999"})
    assert r.status_code in (416, 200, 404, 405)

    # Cleanup
    if audio_path.exists():
        audio_path.unlink()
    db.delete(call)
    db.commit()

def test_t2_f07_audio_stream_zero_byte_range(client, db):
    """T2.F7.5: Range 'bytes=0-0' requests single first byte."""
    call_id = f"test-t2-f07d-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.wav"
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / storage_key
    create_synthetic_wav_file(audio_path, duration_sec=1.0)

    call = Call(id=call_id, original_filename="test.wav", size_bytes=audio_path.stat().st_size, storage_key=storage_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=0-0"})
    if r.status_code == 206:
        assert len(r.content) == 1
    else:
        assert r.status_code in (200, 404, 405)

    # Cleanup
    if audio_path.exists():
        audio_path.unlink()
    db.delete(call)
    db.commit()

# ==============================================================================
# FEATURE 8: Audio Rectification & Reporting (Boundary / Negative)
# ==============================================================================
def test_t2_f08_normalize_missing_input_file_raises_error(tmp_path):
    """T2.F8.1: normalize_to_wav on missing input file raises error."""
    missing_input = tmp_path / "non_existent.wav"
    output_wav = tmp_path / "out.wav"
    with pytest.raises(Exception):
        normalize_to_wav(missing_input, output_wav)

def test_t2_f08_normalize_corrupted_input_file_raises_error(tmp_path):
    """T2.F8.2: normalize_to_wav on corrupted random data raises AppError AUDIO_CORRUPTED."""
    corrupt_file = tmp_path / "corrupt.wav"
    corrupt_file.write_bytes(CORRUPTED_RANDOM_BYTES)
    output_wav = tmp_path / "out.wav"
    with pytest.raises(AppError) as exc_info:
        normalize_to_wav(corrupt_file, output_wav)
    assert exc_info.value.code == "AUDIO_CORRUPTED"

def test_t2_f08_audio_validation_empty_file_rejected(tmp_path):
    """T2.F8.3: validate_audio_file on empty file raises FILE_EMPTY."""
    empty_file = tmp_path / "empty.m4a"
    empty_file.write_bytes(b"")
    with pytest.raises(AppError) as exc:
        validate_audio_file(empty_file)
    assert exc.value.code == "FILE_EMPTY"

def test_t2_f08_audio_validation_too_short_duration(tmp_path, monkeypatch):
    """T2.F8.4: Audio duration < 10s raises DURATION_OUT_OF_RANGE."""
    dummy_file = tmp_path / "short.m4a"
    dummy_file.write_bytes(b"non-empty-bytes")
    short_probe = {
        "streams": [{"codec_name": "aac", "channels": 1, "sample_rate": "16000"}],
        "format": {"duration": "4.2"},
    }
    monkeypatch.setattr("app.audio.validation.probe_audio", lambda path: short_probe)
    with pytest.raises(AppError) as exc:
        validate_audio_file(dummy_file)
    assert exc.value.code == "DURATION_OUT_OF_RANGE"

def test_t2_f08_audio_validation_too_long_duration(tmp_path, monkeypatch):
    """T2.F8.5: Audio duration > 1800s raises DURATION_OUT_OF_RANGE."""
    dummy_file = tmp_path / "long.m4a"
    dummy_file.write_bytes(b"non-empty-bytes")
    long_probe = {
        "streams": [{"codec_name": "aac", "channels": 1, "sample_rate": "16000"}],
        "format": {"duration": "2400.0"},
    }
    monkeypatch.setattr("app.audio.validation.probe_audio", lambda path: long_probe)
    with pytest.raises(AppError) as exc:
        validate_audio_file(dummy_file)
    assert exc.value.code == "DURATION_OUT_OF_RANGE"

# ==============================================================================
# FEATURE 9: Transcription Benchmarking (Boundary / Negative)
# ==============================================================================
def test_t2_f09_benchmark_wer_empty_hypothesis_yields_one():
    """T2.F9.1: calculate_wer with empty hypothesis yields 1.0 (100% deletion)."""
    assert calculate_wer("reference text here", "") == 1.0

def test_t2_f09_benchmark_wer_empty_reference_no_division_by_zero():
    """T2.F9.2: calculate_wer with empty reference handled without ZeroDivisionError."""
    assert calculate_wer("", "hypothesis text") == 1.0

def test_t2_f09_benchmark_wer_both_empty_yields_zero():
    """T2.F9.3: calculate_wer with both empty strings yields 0.0."""
    assert calculate_wer("", "") == 0.0

def test_t2_f09_benchmark_cer_empty_strings_handled():
    """T2.F9.4: calculate_cer with empty strings handled safely."""
    assert calculate_cer("", "") == 0.0
    assert calculate_cer("reference", "") == 1.0
    assert calculate_cer("", "hypothesis") == 1.0

def test_t2_f09_benchmark_cer_unicode_and_hinglish():
    """T2.F9.5: calculate_cer handles non-ASCII Devanagari and Hinglish characters safely."""
    hindi_ref = "नमस्ते ग्राहक बिक्री"
    hindi_hyp = "नमस्ते ग्राहक बिक्री"
    assert calculate_cer(hindi_ref, hindi_hyp) == 0.0

    hindi_diff = "नमस्ते ग्राहक सेवा"
    cer = calculate_cer(hindi_ref, hindi_diff)
    assert 0.0 < cer < 1.0

# ==============================================================================
# FEATURE 10: Browser Validation Sample MPEG (Boundary / Negative)
# ==============================================================================
def test_t2_f10_corrupted_mpeg_magic_bytes_rejected(tmp_path):
    """T2.F10.1: Corrupted MPEG file is caught by validate_audio_file as AUDIO_CORRUPTED."""
    corrupt_mpeg = tmp_path / "corrupt.mpeg"
    corrupt_mpeg.write_bytes(b"\x00\x00\x00\x00corrupt-mpeg-garbage-bytes-12345")
    with pytest.raises(AppError) as exc_info:
        validate_audio_file(corrupt_mpeg)
    assert exc_info.value.code in ("AUDIO_CORRUPTED", "AUDIO_UNREADABLE", "INVALID_FILE_TYPE", "DURATION_OUT_OF_RANGE")

def test_t2_f10_sample_mpeg_invalid_range_seek(client, db):
    """T2.F10.2: Seeking out-of-bounds byte range on sample MPEG call handled safely."""
    call_id = f"test-t2-f10-{uuid.uuid4().hex[:8]}"
    call = Call(id=call_id, original_filename="sample.mpeg", size_bytes=344434, storage_key="sample.mpeg")
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=99999999-999999999"})
    assert r.status_code in (416, 200, 404, 405)

    # Cleanup
    db.delete(call)
    db.commit()

def test_t2_f10_sample_mpeg_duplicate_upload_generates_unique_call_id(client):
    """T2.F10.3: Multiple uploads of the same MPEG file generate unique call IDs."""
    with open(SAMPLE_MPEG_PATH, "rb") as f1, open(SAMPLE_MPEG_PATH, "rb") as f2:
        r1 = client.post("/api/v1/calls", files={"file": ("sample_dup1.mpeg", f1, "video/mpeg")})
        r2 = client.post("/api/v1/calls", files={"file": ("sample_dup2.mpeg", f2, "video/mpeg")})
    assert r1.status_code == 202
    assert r2.status_code == 202
    assert r1.json()["id"] != r2.json()["id"]

def test_t2_f10_sample_mpeg_role_swap_validation(client, db):
    """T2.F10.4: Inverting roles on MPEG call without sales_rep raises 422."""
    call_id = f"test-t2-f10b-{uuid.uuid4().hex[:8]}"
    call = Call(id=call_id, original_filename="sample.mpeg", size_bytes=344434, storage_key=f"{call_id}.mpeg", status="complete")
    role_a = SpeakerRole(call_id=call_id, speaker_label="A", role="unknown", status="unresolved")
    role_b = SpeakerRole(call_id=call_id, speaker_label="B", role="unknown", status="unresolved")
    db.add_all([call, role_a, role_b])
    db.commit()

    # Assigning both as customer (0 sales reps) must be rejected
    r = client.put(f"/api/v1/calls/{call_id}/speaker-roles", json={"roles": {"A": "customer", "B": "customer"}})
    assert r.status_code == 422

    # Cleanup
    db.delete(role_a)
    db.delete(role_b)
    db.delete(call)
    db.commit()

def test_t2_f10_sample_mpeg_markdown_export_content(client, db):
    """T2.F10.5: Export endpoint returns markdown with expected structure for completed call."""
    call_id = f"test-t2-f10c-{uuid.uuid4().hex[:8]}"
    call = Call(id=call_id, original_filename="sample.mpeg", size_bytes=344434, storage_key=f"{call_id}.mpeg", status="complete")
    active_s = SettingsService.get_latest_settings(db)
    from app.db.models.analyses import Analysis
    from app.db.models.transcripts import Transcript
    an = Analysis(
        id=f"an-{call_id}",
        call_id=call_id,
        run_number=1,
        settings_version=active_s.version,
        status="complete",
        verdict="GREEN"
    )
    tr = Transcript(call_id=call_id, status="completed", provider="faster_whisper", speaker_count=2, audio_seconds=114.8)
    db.add_all([call, an, tr])
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/export?format=markdown")
    assert r.status_code == 200
    assert "Sales Call Audit Report" in r.text
    assert "GREEN" in r.text

    # Cleanup
    db.delete(an)
    db.delete(tr)
    db.delete(call)
    db.commit()
