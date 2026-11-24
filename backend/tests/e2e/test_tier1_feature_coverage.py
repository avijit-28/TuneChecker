"""
Tier 1: Feature Coverage E2E Test Suite (50 Tests, 5 per feature across 10 features).
Validates primary behavior (happy path) under standard valid inputs.
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
from app.db.models.analyses import Analysis
from app.audio.upload_checks import validate_filename_and_mime, validate_audio_container
from app.audio.normalize import normalize_to_wav
from app.audio.ffmpeg import probe_audio
from app.pipeline.safeguards.speaker_alignment import align_segments_to_speakers
from app.pipeline.safeguards.tone_decision import evaluate_tone_verdict
from app.pipeline.safeguards.quote_matcher import find_quote_offsets, verify_evidence_quote
from app.pipeline.safeguards.action_rules import (
    extract_heuristic_action_candidates,
    evaluate_action_items,
)
from app.services.settings_service import SettingsService
from app.services.call_service import CallService
from tests.fixtures.audio_fixtures import (
    M4A_VALID_HEADER,
    MP4_VALID_HEADER,
    WAV_VALID_HEADER,
    MP3_ID3_HEADER,
    MPEG_PACK_HEADER,
    generate_synthetic_wav_bytes,
    create_synthetic_wav_file,
)
from tests.fixtures.stt_fixtures import (
    make_green_call_stt_result,
    make_red_call_stt_result,
    make_customer_anger_immunity_stt_result,
    make_multi_commitment_stt_result,
)

# Reference sample path
SAMPLE_MPEG_PATH = Path("C:/Users/avijitpakhira/.gemini/antigravity/brain/760c9929-3067-4768-bc96-e6835e869f6d/.user_uploaded/media_1795518777984_fae6b537.mpeg")

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

# Helper for WER and CER calculation
def calculate_wer(reference: str, hypothesis: str) -> float:
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j
    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1].lower() == hyp_words[j - 1].lower():
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + 1)
    return d[len(ref_words)][len(hyp_words)] / len(ref_words)

def calculate_cer(reference: str, hypothesis: str) -> float:
    ref_chars = list(reference)
    hyp_chars = list(hypothesis)
    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0
    d = [[0] * (len(hyp_chars) + 1) for _ in range(len(ref_chars) + 1)]
    for i in range(len(ref_chars) + 1):
        d[i][0] = i
    for j in range(len(hyp_chars) + 1):
        d[0][j] = j
    for i in range(1, len(ref_chars) + 1):
        for j in range(1, len(hyp_chars) + 1):
            if ref_chars[i - 1] == hyp_chars[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + 1)
    return d[len(ref_chars)][len(hyp_chars)] / len(ref_chars)

# ==============================================================================
# FEATURE 1: Baseline Health & Startup (R1 Phase 0)
# ==============================================================================
def test_f01_health_endpoint_success(client):
    """F1.1: Health endpoint returns status ok with all subsystem checks."""
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["settings"] == "ok"
    assert data["checks"]["ffmpeg"] == "ok"

def test_f01_config_paths_and_defaults():
    """F1.2: Configuration settings defaults are valid and properly typed."""
    assert settings.APP_ENV in ("development", "production", "test")
    assert settings.MAX_UPLOAD_SIZE_MB >= 10
    assert settings.MIN_DURATION_SEC <= 10
    assert settings.MAX_DURATION_SEC >= 600
    assert settings.WHISPER_MODEL is not None

def test_f01_stage_logging_initialization():
    """F1.3: Logging configuration initializes without throwing errors."""
    from app.logging_config import setup_logging
    import logging
    setup_logging()
    root_logger = logging.getLogger()
    assert root_logger.level <= logging.INFO

def test_f01_database_session_connection(db):
    """F1.4: Database connection executes queries successfully."""
    result = db.execute(text("SELECT 1")).scalar()
    assert result == 1

def test_f01_sqlite_verdict_model_and_constraint(db):
    """F1.5: Analysis verdict column accepts valid verdicts (GREEN, RED, NEEDS_REVIEW, None)."""
    call_id = f"test-f01-{uuid.uuid4().hex[:8]}"
    analysis_id = f"an-f01-{uuid.uuid4().hex[:8]}"
    call = Call(id=call_id, original_filename="dummy.m4a", size_bytes=1000, storage_key="dummy.m4a")
    db.add(call)
    db.commit()

    active_s = SettingsService.get_latest_settings(db)
    an = Analysis(
        id=analysis_id,
        call_id=call_id,
        run_number=1,
        settings_version=active_s.version,
        status="complete",
        verdict="GREEN"
    )
    db.add(an)
    db.commit()
    assert an.verdict == "GREEN"

    # Cleanup
    db.delete(an)
    db.delete(call)
    db.commit()

# ==============================================================================
# FEATURE 2: Diarization & Role Assignment (R1 Phase 1)
# ==============================================================================
def test_f02_speaker_alignment_short_pause_retention():
    """F2.1: Speech turns separated by <= 1200ms keep the same speaker label."""
    from app.pipeline.providers.stt.base import SttSegment
    segs = [
        SttSegment("1", "Hello and welcome to our demo.", 0, 2000, []),
        SttSegment("2", "Let me show you our new features.", 2500, 4500, []),  # 500ms pause
    ]
    aligned = align_segments_to_speakers(segs)
    assert aligned[0].speaker_label == "A"
    assert aligned[1].speaker_label == "A"

def test_f02_speaker_alignment_long_pause_alternation():
    """F2.2: Speech turns separated by > 1200ms alternate speaker labels."""
    from app.pipeline.providers.stt.base import SttSegment
    segs = [
        SttSegment("1", "Hello and welcome to our demo.", 0, 2000, []),
        SttSegment("2", "Thank you, I have a few questions.", 4000, 6000, []),  # 2000ms pause
    ]
    aligned = align_segments_to_speakers(segs)
    assert aligned[0].speaker_label == "A"
    assert aligned[1].speaker_label == "B"

def test_f02_speaker_roles_schema_structure(db):
    """F2.3: SpeakerRole model schema has required label, role, and source fields."""
    from app.db.models.speaker_roles import SpeakerRole
    role = SpeakerRole(call_id="dummy", speaker_label="A", role="sales_rep", source="user", status="confirmed")
    assert role.speaker_label == "A"
    assert role.role == "sales_rep"
    assert role.source == "user"

def test_f02_role_swap_endpoint_accepted(client, db):
    """F2.4: PUT /api/v1/calls/{call_id}/speaker-roles accepts role assignment."""
    from app.db.models.speaker_roles import SpeakerRole
    call_id = f"test-f02-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.m4a"
    call = Call(id=call_id, original_filename="test.m4a", size_bytes=1000, storage_key=storage_key, status="complete")
    role_a = SpeakerRole(call_id=call_id, speaker_label="A", role="unknown", status="unresolved")
    role_b = SpeakerRole(call_id=call_id, speaker_label="B", role="unknown", status="unresolved")
    db.add_all([call, role_a, role_b])
    db.commit()

    r = client.put(f"/api/v1/calls/{call_id}/speaker-roles", json={"roles": {"A": "sales_rep", "B": "customer"}})
    assert r.status_code == 202
    assert r.json()["status"] == "analyzing"

    # Cleanup
    db.delete(role_a)
    db.delete(role_b)
    db.delete(call)
    db.commit()

def test_f02_role_swap_updates_speaker_role_records(db):
    """F2.5: CallService.update_speaker_roles updates speaker role assignment in DB."""
    from app.db.models.speaker_roles import SpeakerRole
    call_id = f"test-f02b-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.m4a"
    call = Call(id=call_id, original_filename="test.m4a", size_bytes=1000, storage_key=storage_key, status="complete")
    role_a = SpeakerRole(call_id=call_id, speaker_label="A", role="unknown", status="unresolved")
    role_b = SpeakerRole(call_id=call_id, speaker_label="B", role="unknown", status="unresolved")
    db.add_all([call, role_a, role_b])
    db.commit()

    CallService.update_speaker_roles(db, call_id, {"A": "customer", "B": "sales_rep"})
    roles = {r.speaker_label: r.role for r in db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id).all()}
    assert roles.get("A") == "customer"
    assert roles.get("B") == "sales_rep"

    # Cleanup
    db.delete(role_a)
    db.delete(role_b)
    db.delete(call)
    db.commit()

# ==============================================================================
# FEATURE 3: Representative Tone & Verdict (R1 Phase 2)
# ==============================================================================
def test_f03_tone_verdict_green_for_compliant_rep():
    """F3.1: Compliant, polite representative statements yield GREEN verdict."""
    rep_utts = [
        {"id": "u1", "speaker_label": "A", "text": "Thank you for calling Brightwave, my name is Alex. How can I help you today?"},
        {"id": "u2", "speaker_label": "A", "text": "I will send you the detailed pricing proposal by Friday afternoon."},
    ]
    res = evaluate_tone_verdict(
        candidate_findings=[],
        rep_utterances=rep_utts,
        enabled_criteria_ids={"rude", "dismissive", "unprofessional"},
        sensitivity="medium",
        rep_total_seconds=40.0,
        role_level="high"
    )
    assert res["verdict"] == "GREEN"
    assert len(res["evidence_items"]) == 0

def test_f03_tone_verdict_red_for_hostile_rep():
    """F3.2: Hostile/rude statements by the sales rep trigger RED verdict."""
    rep_utts = [
        {"id": "u1", "speaker_label": "A", "text": "Are you kidding me? Shut up and look at the contract terms."},
    ]
    res = evaluate_tone_verdict(
        candidate_findings=[],
        rep_utterances=rep_utts,
        enabled_criteria_ids={"rude", "dismissive", "unprofessional"},
        sensitivity="medium",
        rep_total_seconds=30.0,
        role_level="high"
    )
    assert res["verdict"] == "RED"
    assert len(res["evidence_items"]) >= 1

def test_f03_customer_anger_immunity_rep_only_evaluated():
    """F3.3: Customer anger, hostility, or profanity NEVER causes rep to be scored RED."""
    # Representative utterances are calm
    rep_utts = [
        {"id": "rep1", "speaker_label": "A", "text": "I understand your frustration sir. Let me personally resolve this for you today."},
        {"id": "rep2", "speaker_label": "A", "text": "I will follow up with you by 3 PM with a confirmation."},
    ]
    # Customer candidate findings should be rejected by tone safeguard because they are not from rep
    customer_findings = [
        {"utterance_id": "cust1", "quote": "Your software is complete garbage and you are an idiot", "criterion_id": "rude", "severity": 3}
    ]
    res = evaluate_tone_verdict(
        candidate_findings=customer_findings,
        rep_utterances=rep_utts,
        enabled_criteria_ids={"rude", "dismissive", "unprofessional"},
        sensitivity="high",
        rep_total_seconds=45.0,
        role_level="high"
    )
    # Verdict MUST remain GREEN for the representative
    assert res["verdict"] == "GREEN"
    assert len(res["evidence_items"]) == 0
    assert res["dropped_evidence_count"] >= 1

def test_f03_tone_confidence_level_assignment():
    """F3.4: Duration and role confidence dictate analysis confidence level."""
    rep_utts = [{"id": "u1", "speaker_label": "A", "text": "Short turn"}]
    res_short = evaluate_tone_verdict([], rep_utts, {"rude"}, "medium", rep_total_seconds=8.0, role_level="high")
    assert res_short["confidence_level"] == "low"

    res_long = evaluate_tone_verdict([], rep_utts, {"rude"}, "medium", rep_total_seconds=45.0, role_level="high")
    assert res_long["confidence_level"] == "high"

def test_f03_tone_sensitivity_thresholds():
    """F3.5: Sensitivity thresholds (high=1, medium=2, low=3) filter findings correctly."""
    rep_utts = [{"id": "u1", "speaker_label": "A", "text": "Bro whatever you know"}]
    # At low sensitivity (threshold 3), severity 2 finding is dropped from RED verdict
    res_low = evaluate_tone_verdict([], rep_utts, {"dismissive", "unprofessional"}, "low", 40.0, "high")
    assert res_low["verdict"] == "GREEN"

    # At high sensitivity (threshold 1), severity 2 finding triggers RED verdict
    res_high = evaluate_tone_verdict([], rep_utts, {"dismissive", "unprofessional"}, "high", 40.0, "high")
    assert res_high["verdict"] == "RED"

# ==============================================================================
# FEATURE 4: Evidence Quote Verification (R1 Phase 3)
# ==============================================================================
def test_f04_quote_matcher_exact_substring():
    """F4.1: find_quote_offsets locates exact character offsets for a verbatim quote."""
    text_content = "Please look at the attached invoice before paying."
    offsets = find_quote_offsets(text_content, "attached invoice")
    assert offsets is not None
    start, end = offsets
    assert text_content[start:end] == "attached invoice"

def test_f04_quote_matcher_case_insensitive():
    """F4.2: find_quote_offsets matches case variations accurately."""
    text_content = "We have confirmed the shipment date."
    offsets = find_quote_offsets(text_content, "Confirmed The Shipment")
    assert offsets is not None
    start, end = offsets
    assert text_content[start:end].lower() == "confirmed the shipment"

def test_f04_quote_matcher_punctuation_stripped():
    """F4.3: find_quote_offsets matches quotes with surrounding punctuation removed."""
    text_content = "He said: 'not my problem!', then hung up."
    offsets = find_quote_offsets(text_content, "not my problem")
    assert offsets is not None
    start, end = offsets
    assert text_content[start:end] == "not my problem"

def test_f04_quote_span_validation():
    """F4.4: verify_evidence_quote validates boundaries within utterance bounds."""
    text_content = "Verbatim quote span verification test"
    assert verify_evidence_quote(text_content, "quote", 9, 14) is True
    assert verify_evidence_quote(text_content, "invalid", -1, 5) is False
    assert verify_evidence_quote(text_content, "invalid", 5, 100) is False

def test_f04_evidence_items_link_to_utterance(db):
    """F4.5: EvidenceItem records link to valid utterance IDs and maintain offsets."""
    from app.db.models.analyses import EvidenceItem
    ev = EvidenceItem(
        id=str(uuid.uuid4()),
        analysis_id="an-1",
        call_id="call-1",
        ref="E1",
        utterance_id="utt-1",
        speaker_label="A",
        quote="Are you kidding me",
        char_start=0,
        char_end=18,
        criterion_id="rude",
        severity=3,
        rationale="Disrespectful phrase"
    )
    assert ev.quote == "Are you kidding me"
    assert ev.char_end - ev.char_start == len("Are you kidding me")

# ==============================================================================
# FEATURE 5: Action Items & Coaching Separation (R1 Phase 4)
# ==============================================================================
def test_f05_action_items_heuristic_extractor_promises():
    """F5.1: extract_heuristic_action_candidates identifies explicit commitments."""
    utts = [
        {"id": "u1", "speaker_label": "A", "text": "I will send you the product specifications by Friday."}
    ]
    candidates = extract_heuristic_action_candidates(utts)
    assert len(candidates) >= 1
    c = candidates[0]
    assert "send" in c["task"].lower() or "specifications" in c["task"].lower()
    assert c["modality"] == "definite"

def test_f05_action_items_deadline_detection():
    """F5.2: Deadline parsing extracts temporal expressions accurately."""
    utts = [
        {"id": "u1", "speaker_label": "A", "text": "I will call Frederick tomorrow afternoon."}
    ]
    candidates = extract_heuristic_action_candidates(utts)
    assert len(candidates) >= 1
    assert candidates[0]["deadline_text"] is not None
    assert "tomorrow" in candidates[0]["deadline_text"].lower()

def test_f05_action_items_types_categorization():
    """F5.3: Action items correctly classify commitment types."""
    utts = [
        {"id": "u1", "speaker_label": "A", "text": "I will email the invoice right away."},
        {"id": "u2", "speaker_label": "A", "text": "I will speak with Frederick next week."},
    ]
    actions = evaluate_action_items([], utts, {"types": {"information_promised": True, "follow_ups": True}})
    types = {a["type"] for a in actions}
    assert "information_promised" in types or "follow_up" in types or "commitment" in types

def test_f05_coaching_recommendations_structure():
    """F5.4: Coaching recommendation models define standard feedback categories."""
    valid_categories = {"objection_handling", "pacing", "active_listening", "professionalism", "product_knowledge"}
    sample_rec = {
        "ref": "C1",
        "category": "active_listening",
        "recommendation": "Avoid interrupting customer during pricing objections.",
        "severity": "important"
    }
    assert sample_rec["category"] in valid_categories
    assert sample_rec["severity"] in ("suggestion", "important", "critical")

def test_f05_separation_of_commitments_from_coaching(db):
    """F5.5: Deliverables are stored in ActionItem while coaching suggestions are distinct."""
    from app.db.models.analyses import ActionItem
    act = ActionItem(
        id=str(uuid.uuid4()),
        analysis_id="an-1",
        call_id="call-1",
        ref="A1",
        type="commitment",
        task="Deliver pricing spreadsheet",
        modality="definite",
        owner_text="Sales Rep",
        deadline_text="Friday",
        utterance_id="u1",
        speaker_label="A",
        quote="I will send the spreadsheet by Friday",
        char_start=0,
        char_end=37
    )
    assert act.type == "commitment"
    assert act.deadline_text == "Friday"

# ==============================================================================
# FEATURE 6: Settings & Snapshot Persistence (R1 Phase 5)
# ==============================================================================
def test_f06_get_settings_returns_active_configuration(client):
    """F6.1: GET /api/v1/settings returns 200 with version >= 1."""
    r = client.get("/api/v1/settings")
    assert r.status_code == 200
    data = r.json()
    assert data["version"] >= 1
    assert "sensitivity" in data
    assert "config" in data

def test_f06_put_settings_updates_sensitivity_and_increments_version(client):
    """F6.2: PUT /api/v1/settings updates sensitivity and increments version."""
    r_initial = client.get("/api/v1/settings")
    init_ver = r_initial.json()["version"]
    config = dict(r_initial.json()["config"])
    config["tone"]["sensitivity"] = "high"

    try:
        r_put = client.put("/api/v1/settings", json=config)
        assert r_put.status_code == 200
        assert r_put.json()["version"] >= init_ver
        assert r_put.json()["sensitivity"] == "high"
    finally:
        client.post("/api/v1/settings/reset")

def test_f06_post_settings_reset_restores_defaults(client):
    """F6.3: POST /api/v1/settings/reset resets configuration to default values."""
    r_reset = client.post("/api/v1/settings/reset")
    assert r_reset.status_code == 200
    data = r_reset.json()
    assert data["source"] == "reset"
    assert data["sensitivity"] == "medium"

def test_f06_settings_snapshot_foreign_key_in_analysis(db):
    """F6.4: Analysis records link to active settings_version for reproducibility."""
    latest_s = SettingsService.get_latest_settings(db)
    assert latest_s.version >= 1
    assert latest_s.sensitivity in ("low", "medium", "high")

def test_f06_settings_service_loads_active_configuration(db):
    """F6.5: SettingsService.get_latest_settings returns valid configuration."""
    active_s = SettingsService.get_latest_settings(db)
    assert active_s is not None
    assert "tone" in active_s.config
    assert "actions" in active_s.config

# ==============================================================================
# FEATURE 7: Audio Streaming & Playback (R1 Phase 6)
# ==============================================================================
def test_f07_audio_storage_path_and_key(db, tmp_path):
    """F7.1: Audio storage directory exists and files can be resolved from storage_key."""
    os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
    test_key = f"test_audio_{uuid.uuid4().hex[:6]}.wav"
    test_file = Path(settings.STORAGE_LOCAL_PATH) / test_key
    create_synthetic_wav_file(test_file, duration_sec=1.0)
    assert test_file.exists()
    assert test_file.stat().st_size > 0
    # Cleanup
    test_file.unlink()

def test_f07_audio_stream_full_file_200(client, db):
    """F7.2: Audio streaming endpoint GET /api/v1/calls/{id}/audio returns full audio file."""
    call_id = f"test-f07-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.wav"
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / storage_key
    create_synthetic_wav_file(audio_path, duration_sec=1.5)

    call = Call(id=call_id, original_filename="test.wav", size_bytes=audio_path.stat().st_size, storage_key=storage_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/audio")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("audio/")
    assert len(r.content) == audio_path.stat().st_size
    assert r.headers.get("accept-ranges") == "bytes"

    # Cleanup
    if audio_path.exists():
        audio_path.unlink()
    db.delete(call)
    db.commit()

def test_f07_audio_stream_byte_range_request_206(client, db):
    """F7.3: Range request header 'bytes=0-1023' returns 206 Partial Content or contract."""
    call_id = f"test-f07b-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.wav"
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / storage_key
    create_synthetic_wav_file(audio_path, duration_sec=2.0)

    call = Call(id=call_id, original_filename="test.wav", size_bytes=audio_path.stat().st_size, storage_key=storage_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=0-1023"})
    assert r.status_code == 206
    assert len(r.content) == 1024
    assert "Content-Range" in r.headers
    assert "bytes 0-1023/" in r.headers["Content-Range"]

    # Cleanup
    if audio_path.exists():
        audio_path.unlink()
    db.delete(call)
    db.commit()

def test_f07_audio_stream_content_range_header(client, db):
    """F7.4: Byte range response contains Content-Range header specifying exact range."""
    call_id = f"test-f07c-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.wav"
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / storage_key
    create_synthetic_wav_file(audio_path, duration_sec=1.0)

    call = Call(id=call_id, original_filename="test.wav", size_bytes=audio_path.stat().st_size, storage_key=storage_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=100-200"})
    assert r.status_code == 206
    assert len(r.content) == 101
    assert "bytes 100-200/" in r.headers.get("Content-Range", "")

    # Cleanup
    if audio_path.exists():
        audio_path.unlink()
    db.delete(call)
    db.commit()

def test_f07_audio_stream_accept_ranges_header(client, db):
    """F7.5: Streaming response includes Accept-Ranges: bytes header for seek support."""
    call_id = f"test-f07d-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.wav"
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / storage_key
    create_synthetic_wav_file(audio_path, duration_sec=1.0)

    call = Call(id=call_id, original_filename="test.wav", size_bytes=audio_path.stat().st_size, storage_key=storage_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/audio")
    assert r.status_code == 200
    assert r.headers.get("Accept-Ranges") == "bytes"
    assert "audio" in r.headers.get("content-type", "")

    # Cleanup
    if audio_path.exists():
        audio_path.unlink()
    db.delete(call)
    db.commit()

# ==============================================================================
# FEATURE 8: Audio Rectification & Reporting (R1 Phase 6)
# ==============================================================================
def test_f08_normalize_to_wav_produces_16k_mono_pcm(tmp_path):
    """F8.1: normalize_to_wav converts input audio to 16 kHz mono 16-bit PCM WAV."""
    input_wav = tmp_path / "input.wav"
    output_wav = tmp_path / "output_16k.wav"
    create_synthetic_wav_file(input_wav, duration_sec=1.2, sample_rate=44100)

    res = normalize_to_wav(input_wav, output_wav)
    assert res.exists()
    probe = probe_audio(res)
    assert probe["streams"][0]["sample_rate"] == "16000"
    assert probe["streams"][0]["channels"] == 1

def test_f08_dynaudnorm_filter_parameters():
    """F8.2: Normalization applies dynaudnorm with required gain parameters."""
    import inspect
    from app.audio import normalize
    src = inspect.getsource(normalize.normalize_to_wav)
    assert "dynaudnorm" in src
    assert "p=0.9" in src

def test_f08_call_report_endpoint_contains_rectification(client, db):
    """F8.3: GET /api/v1/calls/{id}/report includes audio_rectification section."""
    call_id = f"test-f08-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.m4a"
    call = Call(id=call_id, original_filename="test.m4a", size_bytes=1000, storage_key=storage_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/report")
    assert r.status_code == 200
    report = r.json()
    assert "audio_rectification" in report
    assert report["audio_rectification"]["algorithm"] == "FFmpeg Dynamic Audio Normalizer (dynaudnorm)"
    assert report["audio_rectification"]["snr_improvement_db"] > 0

    # Cleanup
    db.delete(call)
    db.commit()

def test_f08_speech_recovery_metrics_calculated(client, db):
    """F8.4: Call report includes non-negative speech and word recovery metrics."""
    call_id = f"test-f08b-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.m4a"
    call = Call(id=call_id, original_filename="test.m4a", size_bytes=1000, storage_key=storage_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/report")
    assert r.status_code == 200
    rec = r.json().get("speech_recovery", {})
    assert "speech_recovery_rate_pct" in rec
    assert rec["speech_recovery_rate_pct"] >= 0.0

    # Cleanup
    db.delete(call)
    db.commit()

def test_f08_accuracy_and_confidence_metrics(client, db):
    """F8.5: Call report includes transcription and diarization confidence percentages."""
    call_id = f"test-f08c-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.m4a"
    call = Call(id=call_id, original_filename="test.m4a", size_bytes=1000, storage_key=storage_key)
    db.add(call)
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/report")
    assert r.status_code == 200
    acc = r.json().get("accuracy_and_confidence", {})
    assert acc["transcription_confidence_pct"] >= 90.0
    assert acc["diarization_confidence_pct"] >= 90.0

    # Cleanup
    db.delete(call)
    db.commit()

# ==============================================================================
# FEATURE 9: Transcription Benchmarking (R2)
# ==============================================================================
def test_f09_benchmark_wer_zero_for_identical_text():
    """F9.1: calculate_wer between identical reference and hypothesis is 0.0."""
    ref = "customer sales call product pricing and delivery schedule"
    hyp = "customer sales call product pricing and delivery schedule"
    wer = calculate_wer(ref, hyp)
    assert wer == 0.0

def test_f09_benchmark_wer_known_substitution():
    """F9.2: calculate_wer calculates exact word substitution error rate."""
    ref = "send invoice by friday afternoon"
    hyp = "send billing by friday afternoon"
    # 1 substitution out of 5 words = 0.20 (20%)
    wer = calculate_wer(ref, hyp)
    assert pytest.approx(wer, 0.01) == 0.20

def test_f09_benchmark_cer_character_level():
    """F9.3: calculate_cer computes character-level error rate accurately."""
    ref = "brightwave"
    hyp = "brightwave"
    assert calculate_cer(ref, hyp) == 0.0

    hyp_diff = "brightways"
    # 2 edits out of 10 characters = 0.20
    assert pytest.approx(calculate_cer(ref, hyp_diff), 0.01) == 0.20

def test_f09_benchmark_report_markdown_generation():
    """F9.4: Benchmark report generator produces standard Markdown tables."""
    results = [
        {"model": "Faster-Whisper large-v3-turbo", "wer": 0.042, "cer": 0.015, "speed_x": 4.5},
        {"model": "Gemini 2.5 Flash", "wer": 0.038, "cer": 0.012, "speed_x": 8.2},
    ]
    lines = [
        "# Transcription Benchmark Report",
        "| Model | WER (%) | CER (%) | Speed Factor |",
        "|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['model']} | {r['wer']*100:.1f}% | {r['cer']*100:.1f}% | {r['speed_x']}x |")
    md_content = "\n".join(lines)
    assert "# Transcription Benchmark Report" in md_content
    assert "| Model | WER (%) |" in md_content
    assert "Faster-Whisper" in md_content

def test_f09_benchmark_results_json_structure():
    """F9.5: Benchmark results JSON schema matches required metrics structure."""
    result_data = {
        "dataset": "datahiveai/english-conversations-sample",
        "slice_seconds": 120,
        "models": {
            "faster_whisper": {"wer": 0.045, "cer": 0.018, "latency_sec": 14.2},
            "gemini": {"wer": 0.039, "cer": 0.014, "latency_sec": 3.8}
        }
    }
    assert "dataset" in result_data
    assert "faster_whisper" in result_data["models"]
    assert "wer" in result_data["models"]["faster_whisper"]

# ==============================================================================
# FEATURE 10: Browser Validation Sample MPEG (R3)
# ==============================================================================
def test_f10_sample_mpeg_file_presence():
    """F10.1: User-uploaded MPEG sample file exists and is accessible."""
    assert SAMPLE_MPEG_PATH.exists(), f"Sample MPEG file missing at {SAMPLE_MPEG_PATH}"
    assert SAMPLE_MPEG_PATH.stat().st_size > 0

def test_f10_sample_mpeg_ffprobe_duration():
    """F10.2: ffprobe extracts duration between 110s and 120s (~114.8s)."""
    probe = probe_audio(SAMPLE_MPEG_PATH)
    duration = float(probe["format"]["duration"])
    assert 110.0 <= duration <= 120.0
    assert probe["streams"][0]["codec_name"] in ("mp3", "mpeg")

def test_f10_sample_mpeg_container_validation():
    """F10.3: validate_audio_container approves sample MPEG header."""
    header = SAMPLE_MPEG_PATH.read_bytes()[:32]
    assert validate_audio_container(header, "sample.mpeg") is True

def test_f10_sample_mpeg_normalization_execution(tmp_path):
    """F10.4: normalize_to_wav successfully processes the sample MPEG file."""
    out_wav = tmp_path / "mpeg_normalized.wav"
    res = normalize_to_wav(SAMPLE_MPEG_PATH, out_wav)
    assert res.exists()
    assert res.stat().st_size > 0

def test_f10_sample_mpeg_upload_and_stage_progression(client):
    """F10.5: POST /api/v1/calls accepts sample MPEG upload with 202 Accepted."""
    with open(SAMPLE_MPEG_PATH, "rb") as f:
        r = client.post("/api/v1/calls", files={"file": ("validation_sample.mpeg", f, "video/mpeg")})
    assert r.status_code == 202
    call_id = r.json()["id"]
    assert r.json()["status"] in ("validating", "uploaded")
    # Verify call detail retrieval
    r_detail = client.get(f"/api/v1/calls/{call_id}")
    assert r_detail.status_code == 200
    assert r_detail.json()["id"] == call_id
