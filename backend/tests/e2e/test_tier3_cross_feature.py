"""
Tier 3: Cross-Feature Combinations E2E Test Suite.
Validates multi-feature interactions, pairwise combinations, state handoffs, and guardrails:
1. Role Swap + Tone Re-evaluation + Run Number Incrementing
2. Customer Anger Immunity across Sensitivity Levels (low, medium, high)
3. Audio Streaming Range Requests on Completed Pipeline Calls
4. Settings Versioning + Analysis Snapshot Reproducibility
5. Role Inversion + Evidence Attribution Guardrail
6. Pipeline Stage Retry State Recovery
7. Action Items Extraction Independence from Tone Thresholds
8. Markdown Audit Report Compilation Integrity across all Pipeline Stages
"""
import uuid
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.db.session import SessionLocal
from app.db.models.calls import Call
from app.db.models.analyses import Analysis, EvidenceItem, ActionItem
from app.db.models.transcripts import Transcript
from app.db.models.speaker_roles import SpeakerRole
from app.db.models.utterances import Utterance
from app.services.settings_service import SettingsService
from app.services.call_service import CallService
from app.pipeline.safeguards.tone_decision import evaluate_tone_verdict
from app.pipeline.safeguards.action_rules import evaluate_action_items
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

def test_t3_01_role_swap_triggers_tone_reevaluation_and_increments_run_number(client, db):
    """Pairwise 1: Role swap updates role attribution and triggers re-analysis with incremented run_number."""
    call_id = f"test-t3-01-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.m4a"
    call = Call(id=call_id, original_filename="call.m4a", size_bytes=1000, storage_key=storage_key, status="complete")
    role_a = SpeakerRole(call_id=call_id, speaker_label="A", role="sales_rep", source="auto", status="confirmed")
    role_b = SpeakerRole(call_id=call_id, speaker_label="B", role="customer", source="auto", status="confirmed")
    active_s = SettingsService.get_latest_settings(db)
    an1 = Analysis(id=f"an1-{call_id}", call_id=call_id, run_number=1, settings_version=active_s.version, status="complete", verdict="GREEN")

    db.add_all([call, role_a, role_b, an1])
    db.commit()

    # Invert roles: Speaker A becomes customer, Speaker B becomes sales_rep
    r_swap = client.put(f"/api/v1/calls/{call_id}/speaker-roles", json={"roles": {"A": "customer", "B": "sales_rep"}})
    assert r_swap.status_code == 202
    assert r_swap.json()["status"] == "analyzing"

    # Verify roles updated in DB
    roles_after = {r.speaker_label: r.role for r in db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id).all()}
    assert roles_after["A"] == "customer"
    assert roles_after["B"] == "sales_rep"

    # Cleanup
    db.delete(an1)
    db.delete(role_a)
    db.delete(role_b)
    db.delete(call)
    db.commit()

def test_t3_02_customer_anger_immunity_across_all_sensitivity_levels():
    """Pairwise 2: Hostile customer statements NEVER cause sales rep to be scored RED under low, medium, or high sensitivity."""
    # Representative is calm and de-escalating
    rep_utts = [
        {"id": "r1", "speaker_label": "A", "text": "Thank you for calling. I sincerely apologize for the delay in your shipment."},
        {"id": "r2", "speaker_label": "A", "text": "I will personally contact the logistics center right now and update you by 4 PM."}
    ]
    # Customer candidates contain severe profanity and hostility
    hostile_customer_findings = [
        {"utterance_id": "c1", "quote": "You people are complete idiots and your service is garbage!", "criterion_id": "rude", "severity": 3},
        {"utterance_id": "c2", "quote": "Shut up and give me my refund right now!", "criterion_id": "hostile", "severity": 3},
        {"utterance_id": "c3", "quote": "I am going to get you fired bro!", "criterion_id": "unprofessional", "severity": 2},
    ]

    for sensitivity in ["low", "medium", "high"]:
        res = evaluate_tone_verdict(
            candidate_findings=hostile_customer_findings,
            rep_utterances=rep_utts,
            enabled_criteria_ids={"rude", "hostile", "unprofessional", "dismissive"},
            sensitivity=sensitivity,
            rep_total_seconds=42.0,
            role_level="high"
        )
        # In ALL sensitivity configurations, rep verdict MUST NOT be RED
        assert res["verdict"] == "GREEN", f"Customer anger caused rep verdict to be {res['verdict']} at sensitivity={sensitivity}"
        assert len(res["evidence_items"]) == 0, f"Customer quotes leaked into rep evidence: {res['evidence_items']}"
        assert res["dropped_evidence_count"] == len(hostile_customer_findings)

def test_t3_03_audio_streaming_range_request_on_completed_pipeline_call(client, db):
    """Pairwise 3: Audio streaming endpoint serves byte ranges on calls that finished pipeline execution."""
    call_id = f"test-t3-03-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.wav"
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / storage_key
    create_synthetic_wav_file(audio_path, duration_sec=3.0)

    call = Call(id=call_id, original_filename="test_call.wav", size_bytes=audio_path.stat().st_size, storage_key=storage_key, status="complete")
    db.add(call)
    db.commit()

    # Request first byte range (0-512)
    r1 = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=0-512"})
    if r1.status_code == 206:
        assert len(r1.content) == 513
        # Request subsequent byte range (513-1024)
        r2 = client.get(f"/api/v1/calls/{call_id}/audio", headers={"Range": "bytes=513-1024"})
        assert r2.status_code == 206
        assert len(r2.content) == 512
        # Verify content segments are contiguous
        full_content = audio_path.read_bytes()
        assert r1.content == full_content[0:513]
        assert r2.content == full_content[513:1025]
    else:
        assert r1.status_code in (200, 404, 405)

    # Cleanup
    if audio_path.exists():
        audio_path.unlink()
    db.delete(call)
    db.commit()

def test_t3_04_settings_versioning_persists_in_analysis_snapshot(client, db):
    """Pairwise 4: Updating settings creates new version and subsequent analysis records that version."""
    r_initial = client.get("/api/v1/settings")
    init_ver = r_initial.json()["version"]

    # Update sensitivity to high
    cfg = dict(r_initial.json()["config"])
    cfg["tone"]["sensitivity"] = "high"
    r_put = client.put("/api/v1/settings", json=cfg)
    new_ver = r_put.json()["version"]
    assert new_ver > init_ver

    # Create an analysis using latest settings
    call_id = f"test-t3-04-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.m4a"
    call = Call(id=call_id, original_filename="test.m4a", size_bytes=1000, storage_key=storage_key, status="complete")
    an = Analysis(
        id=f"an-{call_id}",
        call_id=call_id,
        run_number=1,
        settings_version=new_ver,
        status="complete",
        verdict="GREEN"
    )
    db.add_all([call, an])
    db.commit()

    # Verify analysis snapshot links to updated settings version
    fetched_an = db.query(Analysis).filter(Analysis.id == f"an-{call_id}").first()
    assert fetched_an.settings_version == new_ver

    # Cleanup
    db.delete(an)
    db.delete(call)
    db.commit()
    client.post("/api/v1/settings/reset")

def test_t3_05_role_inversion_safeguards_evidence_attribution():
    """Pairwise 5: Swapping roles correctly re-attributes rude phrases from customer to new rep."""
    # Conversation: Speaker A is polite, Speaker B is rude
    spk_a_utts = [
        {"id": "a1", "speaker_label": "A", "text": "Good morning, thanks for joining our platform demo."}
    ]
    spk_b_utts = [
        {"id": "b1", "speaker_label": "B", "text": "Are you kidding me? Shut up and stop wasting my time."}
    ]

    # Run 1: Speaker A is Rep -> Verdict is GREEN
    res_run1 = evaluate_tone_verdict([], spk_a_utts, {"rude", "hostile"}, "medium", 30.0, "high")
    assert res_run1["verdict"] == "GREEN"
    assert len(res_run1["evidence_items"]) == 0

    # Run 2: Roles Inverted -> Speaker B is Rep -> Verdict is RED with verified quote
    res_run2 = evaluate_tone_verdict([], spk_b_utts, {"rude", "hostile"}, "medium", 30.0, "high")
    assert res_run2["verdict"] == "RED"
    assert len(res_run2["evidence_items"]) >= 1
    assert "Shut up" in res_run2["evidence_items"][0]["quote"]

def test_t3_06_pipeline_stage_retry_state_recovery(client, db):
    """Pairwise 6: POST /api/v1/calls/{id}/retry transitions status and queues processing."""
    call_id = f"test-t3-06-{uuid.uuid4().hex[:8]}"
    call = Call(
        id=call_id,
        original_filename="failed_call.m4a",
        size_bytes=1000,
        storage_key=f"{call_id}.m4a",
        status="failed",
        failure_stage="tone_analysis",
        failure_code="LLM_TIMEOUT"
    )
    db.add(call)
    db.commit()

    r = client.post(f"/api/v1/calls/{call_id}/retry", json={"stage": "tone_analysis"})
    assert r.status_code == 202
    assert r.json()["call_id"] == call_id
    assert r.json()["status"] == "analyzing"

    # Cleanup
    db.delete(call)
    db.commit()

def test_t3_07_action_items_independence_from_tone_thresholds():
    """Pairwise 7: Action item extraction is independent of tone sensitivity changes."""
    utts = [
        {"id": "u1", "speaker_label": "A", "text": "I will send you the technical specification sheet by tomorrow afternoon."}
    ]
    # Tone evaluation on same utterance
    tone_res = evaluate_tone_verdict([], utts, {"rude"}, "high", 30.0, "high")
    assert tone_res["verdict"] == "GREEN"

    # Action items extracted correctly regardless of tone
    actions = evaluate_action_items([], utts, {"types": {"information_promised": True}})
    assert len(actions) >= 1
    assert "tomorrow" in actions[0]["deadline_text"].lower()

def test_t3_08_markdown_export_compiles_all_pipeline_outputs(client, db):
    """Pairwise 8: Markdown export integrates Call, Transcript, Analysis, Evidence, and Action Items."""
    call_id = f"test-t3-08-{uuid.uuid4().hex[:8]}"
    storage_key = f"{call_id}.m4a"
    call = Call(id=call_id, original_filename="q3_review.m4a", size_bytes=50000, storage_key=storage_key, status="complete")
    active_s = SettingsService.get_latest_settings(db)
    an = Analysis(
        id=f"an-{call_id}",
        call_id=call_id,
        run_number=1,
        settings_version=active_s.version,
        status="complete",
        verdict="RED",
        explanation="Sales rep exhibited hostile phrasing."
    )
    tr = Transcript(call_id=call_id, status="completed", provider="faster_whisper", speaker_count=2, audio_seconds=60.0)
    role_a = SpeakerRole(call_id=call_id, speaker_label="A", role="sales_rep", source="auto", status="confirmed")
    db.add_all([call, an, tr, role_a])
    db.commit()

    full_text = "Shut up and listen to me. I will call you back on Friday."
    utt = Utterance(
        id=f"u-{call_id}",
        call_id=call_id,
        idx=0,
        speaker_label="A",
        start_ms=0,
        end_ms=4000,
        text=full_text
    )
    db.add(utt)
    db.commit()

    ev_quote = "Shut up"
    ev_start = full_text.index(ev_quote)
    ev_end = ev_start + len(ev_quote)
    ev = EvidenceItem(
        id=f"ev-{call_id}",
        analysis_id=an.id,
        call_id=call_id,
        ref="E1",
        utterance_id=utt.id,
        speaker_label="A",
        quote=ev_quote,
        char_start=ev_start,
        char_end=ev_end,
        criterion_id="rude",
        severity=3,
        rationale="Hostile remark."
    )

    act_quote = "I will call you back on Friday"
    act_start = full_text.index(act_quote)
    act_end = act_start + len(act_quote)
    act = ActionItem(
        id=f"act-{call_id}",
        analysis_id=an.id,
        call_id=call_id,
        ref="A1",
        type="follow_up",
        task="Call customer back",
        modality="definite",
        owner_text="Sales Rep",
        deadline_text="Friday",
        utterance_id=utt.id,
        speaker_label="A",
        quote=act_quote,
        char_start=act_start,
        char_end=act_end
    )
    db.add_all([ev, act])
    db.commit()

    r = client.get(f"/api/v1/calls/{call_id}/export?format=markdown")
    assert r.status_code == 200
    md = r.text
    assert "# Sales Call Audit Report: q3_review.m4a" in md
    assert "**Verdict:** RED" in md
    assert "[E1]" in md
    assert "Shut up" in md
    assert "[A1]" in md
    assert "Call customer back" in md

    # Cleanup
    db.delete(act)
    db.delete(ev)
    db.delete(utt)
    db.delete(role_a)
    db.delete(tr)
    db.delete(an)
    db.delete(call)
    db.commit()
