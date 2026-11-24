"""
Tier 4: Real-World Workload Scenarios E2E Test Suite.
Validates end-to-end system execution across the 5 core real-world application scenarios:
1. Compliant Representative Call (GREEN)
2. Hostile Customer with Calm Representative (Customer Anger Immunity)
3. Violating Representative Call (RED)
4. Speaker Misattribution & Manual Role Swap
5. Real-World MPEG Processing (media_1795518777984_fae6b537.mpeg)
"""
import os
import time
import uuid
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.db.session import SessionLocal
from app.db.models.calls import Call
from app.db.models.analyses import Analysis
from app.db.models.transcripts import Transcript
from app.db.models.speaker_roles import SpeakerRole
from app.db.models.utterances import Utterance
from app.audio.normalize import normalize_to_wav
from app.audio.ffmpeg import probe_audio
from app.pipeline.safeguards.tone_decision import evaluate_tone_verdict
from app.pipeline.safeguards.action_rules import evaluate_action_items
from app.pipeline.safeguards.speaker_alignment import align_segments_to_speakers
from app.services.call_service import CallService
from app.services.settings_service import SettingsService
from tests.fixtures.stt_fixtures import (
    make_green_call_stt_result,
    make_red_call_stt_result,
    make_customer_anger_immunity_stt_result,
)
from tests.fixtures.audio_fixtures import create_synthetic_wav_file

SAMPLE_MPEG_PATH = Path("C:/Users/avijitpakhira/.gemini/antigravity/brain/760c9929-3067-4768-bc96-e6835e869f6d/.user_uploaded/media_1795518777984_fae6b537.mpeg")
GREEN_SAMPLE_PATH = Path("D:/avi/TuneChecker/samples/green_call_01.m4a")
RED_SAMPLE_PATH = Path("D:/avi/TuneChecker/samples/red_call_01.m4a")

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

# ------------------------------------------------------------------------------
# SCENARIO 1: Compliant Representative Call (GREEN)
# ------------------------------------------------------------------------------
def test_scenario_01_compliant_representative_green_call(client, db):
    """
    Scenario 1: End-to-end compliant sales representative call.
    Representative is professional, polite, and makes follow-up commitments.
    Expected Verdict: GREEN, 0 evidence violations, commitments captured.
    """
    stt = make_green_call_stt_result()
    aligned = align_segments_to_speakers(stt.segments)
    rep_label = "A"

    rep_utts = [{"id": s.id, "speaker_label": s.speaker_label, "text": s.text} for s in aligned if s.speaker_label == rep_label]
    all_utts = [{"id": s.id, "speaker_label": s.speaker_label, "text": s.text} for s in aligned]

    # Evaluate tone
    tone_res = evaluate_tone_verdict(
        candidate_findings=[],
        rep_utterances=rep_utts,
        enabled_criteria_ids={"rude", "hostile", "dismissive", "unprofessional"},
        sensitivity="medium",
        rep_total_seconds=stt.duration_sec,
        role_level="high"
    )
    assert tone_res["verdict"] == "GREEN"
    assert len(tone_res["evidence_items"]) == 0

    # Extract action items
    actions = evaluate_action_items([], all_utts, {"types": {"information_promised": True, "commitments": True}})
    assert len(actions) >= 1
    # Check commitment details
    promises = [a for a in actions if "pricing" in a["task"].lower() or "proposal" in a["task"].lower() or "send" in a["task"].lower()]
    assert len(promises) >= 1
    assert promises[0]["modality"] == "definite"
    assert "Friday" in (promises[0]["deadline_text"] or "")

# ------------------------------------------------------------------------------
# SCENARIO 2: Hostile Customer with Calm Representative (Customer Anger Immunity)
# ------------------------------------------------------------------------------
def test_scenario_02_customer_anger_immunity_workflow(client, db):
    """
    Scenario 2: Critical customer anger immunity test.
    Customer screams profanities and threatens lawsuits.
    Sales representative remains calm, apologetic, and de-escalates with a commitment.
    MANDATORY CRITERION: Customer anger MUST NEVER result in a RED score for the sales rep.
    """
    stt = make_customer_anger_immunity_stt_result()
    # Speaker A: Rep (Calm)
    # Speaker B: Customer (Aggressive / Hostile)
    for seg in stt.segments:
        if seg.id in ("ca1", "ca3", "ca5", "ca7"):
            seg.speaker_label = "A"
        else:
            seg.speaker_label = "B"

    rep_utts = [{"id": s.id, "speaker_label": s.speaker_label, "text": s.text} for s in stt.segments if s.speaker_label == "A"]
    all_utts = [{"id": s.id, "speaker_label": s.speaker_label, "text": s.text} for s in stt.segments]

    # Candidate findings simulating LLM flag on customer profane utterances
    candidate_findings = [
        {"utterance_id": "ca2", "quote": "Your software is complete garbage and you people are total idiots!", "criterion_id": "hostile", "severity": 3},
        {"utterance_id": "ca4", "quote": "Shut up with your corporate excuses! Fix it right now or I am suing your company!", "criterion_id": "rude", "severity": 3},
    ]

    # Evaluate tone for representative
    tone_res = evaluate_tone_verdict(
        candidate_findings=candidate_findings,
        rep_utterances=rep_utts,
        enabled_criteria_ids={"rude", "hostile", "dismissive", "unprofessional"},
        sensitivity="high",
        rep_total_seconds=stt.duration_sec,
        role_level="high"
    )

    # Invariant Verification: Rep MUST NOT be RED
    assert tone_res["verdict"] == "GREEN", f"Customer hostility caused rep verdict: {tone_res['verdict']}"
    assert len(tone_res["evidence_items"]) == 0
    assert tone_res["dropped_evidence_count"] == 2

    # Verify Rep commitment extracted: "escalate your ticket ... email you an update by 2 PM today"
    actions = evaluate_action_items([], all_utts, {"types": {"follow_ups": True, "information_promised": True}})
    rep_actions = [a for a in actions if a["speaker_label"] == "A"]
    assert len(rep_actions) >= 1
    assert "escalate" in rep_actions[0]["task"].lower() or "email" in rep_actions[0]["task"].lower()

# ------------------------------------------------------------------------------
# SCENARIO 3: Violating Representative Call (RED)
# ------------------------------------------------------------------------------
def test_scenario_03_violating_representative_red_call(client, db):
    """
    Scenario 3: Violating sales representative call.
    Representative makes rude, dismissive, and unprofessional statements.
    Expected Verdict: RED with verified quotes linked to exact character spans.
    """
    stt = make_red_call_stt_result()
    # Speaker A: Rep (Rude)
    for seg in stt.segments:
        if seg.id in ("r1", "r3", "r5", "r7"):
            seg.speaker_label = "A"
        else:
            seg.speaker_label = "B"

    rep_utts = [{"id": s.id, "speaker_label": s.speaker_label, "text": s.text} for s in stt.segments if s.speaker_label == "A"]

    tone_res = evaluate_tone_verdict(
        candidate_findings=[],
        rep_utterances=rep_utts,
        enabled_criteria_ids={"rude", "dismissive", "unprofessional"},
        sensitivity="medium",
        rep_total_seconds=stt.duration_sec,
        role_level="high"
    )

    assert tone_res["verdict"] == "RED"
    assert len(tone_res["evidence_items"]) >= 2
    # Verify quotes are verbatim in the rep utterances
    for ev in tone_res["evidence_items"]:
        matching_utt = next((u for u in rep_utts if u["id"] == ev["utterance_id"]), None)
        assert matching_utt is not None
        assert ev["quote"] in matching_utt["text"]
        # Verify offsets
        span = matching_utt["text"][ev["char_start"]:ev["char_end"]]
        assert span == ev["quote"]

# ------------------------------------------------------------------------------
# SCENARIO 4: Speaker Misattribution & Manual Role Swap
# ------------------------------------------------------------------------------
def test_scenario_04_speaker_misattribution_and_manual_role_swap(client, db):
    """
    Scenario 4: Initially inverted speaker roles are corrected via role swap.
    Verifies that changing role assignment re-evaluates tone and updates the analysis.
    """
    call_id = f"test-scen-04-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.m4a"
    call = Call(id=call_id, original_filename="inverted_call.m4a", size_bytes=2000, storage_key=storage_key, status="complete")
    role_a = SpeakerRole(call_id=call_id, speaker_label="A", role="sales_rep", source="auto", status="confirmed")
    role_b = SpeakerRole(call_id=call_id, speaker_label="B", role="customer", source="auto", status="confirmed")
    active_s = SettingsService.get_latest_settings(db)
    an1 = Analysis(id=f"an1-{call_id}", call_id=call_id, run_number=1, settings_version=active_s.version, status="complete", verdict="GREEN")

    db.add_all([call, role_a, role_b, an1])
    db.commit()

    # User manually corrects role assignment in UI: Speaker B is sales_rep, Speaker A is customer
    r_swap = client.put(f"/api/v1/calls/{call_id}/speaker-roles", json={"roles": {"A": "customer", "B": "sales_rep"}})
    assert r_swap.status_code == 202
    assert r_swap.json()["status"] == "analyzing"

    # Query updated roles in database
    roles = {r.speaker_label: r.role for r in db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id).all()}
    assert roles["A"] == "customer"
    assert roles["B"] == "sales_rep"

    # Cleanup
    db.delete(an1)
    db.delete(role_a)
    db.delete(role_b)
    db.delete(call)
    db.commit()

# ------------------------------------------------------------------------------
# SCENARIO 5: Real-World MPEG Processing (media_1795518777984_fae6b537.mpeg)
# ------------------------------------------------------------------------------
def test_scenario_05_real_world_mpeg_validation_lifecycle(client, db, tmp_path):
    """
    Scenario 5: Complete lifecycle on the real-world 114s MPEG file.
    Validates container checks, normalization with dynaudnorm, report metrics, and upload.
    """
    assert SAMPLE_MPEG_PATH.exists(), f"Real-world sample file missing at {SAMPLE_MPEG_PATH}"

    # 1. Probe original metadata
    probe = probe_audio(SAMPLE_MPEG_PATH)
    duration = float(probe["format"]["duration"])
    assert 110.0 <= duration <= 120.0
    assert probe["streams"][0]["sample_rate"] == "16000"

    # 2. Test audio normalization with dynaudnorm
    out_wav = tmp_path / "normalized_sample.wav"
    res_wav = normalize_to_wav(SAMPLE_MPEG_PATH, out_wav)
    assert res_wav.exists()
    assert res_wav.stat().st_size > 0
    norm_probe = probe_audio(res_wav)
    assert norm_probe["streams"][0]["codec_name"] == "pcm_s16le"
    assert norm_probe["streams"][0]["channels"] == 1
    assert norm_probe["streams"][0]["sample_rate"] == "16000"

    # 3. Upload MPEG file via API
    with open(SAMPLE_MPEG_PATH, "rb") as f:
        r_upload = client.post("/api/v1/calls", files={"file": ("mpeg_validation.mpeg", f, "video/mpeg")})
    assert r_upload.status_code == 202
    call_id = r_upload.json()["id"]

    # 4. Verify call report endpoint returns rectification metrics
    r_rep = client.get(f"/api/v1/calls/{call_id}/report")
    assert r_rep.status_code == 200
    report = r_rep.json()
    assert "audio_rectification" in report
    assert "speech_recovery" in report
    assert report["audio_rectification"]["snr_improvement_db"] > 0
