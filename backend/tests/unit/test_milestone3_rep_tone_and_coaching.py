import uuid
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.models.calls import Call
from app.db.models.transcripts import Transcript
from app.db.models.utterances import Utterance
from app.db.models.speaker_roles import SpeakerRole
from app.db.models.analyses import Analysis, EvidenceItem, ActionItem, CoachingRecommendation
from app.pipeline.stages.tone_analysis import run_tone_stage
from app.pipeline.stages.action_items import run_action_items_stage
from app.pipeline.safeguards.tone_decision import evaluate_tone_verdict
from app.pipeline.safeguards.quote_matcher import verify_evidence_quote, find_quote_offsets
from app.schemas.analyses import (
    CoachingRecommendationResponse,
    ActionItemResponse,
    EvidenceItemResponse,
    AnalysisResponse
)

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def client():
    return TestClient(app)

# ==============================================================================
# a) Customer Anger Immunity with SQLite DB Stage Execution
# ==============================================================================
def test_customer_anger_immunity_db_stage_execution(client, db, monkeypatch):
    """
    Customer is screaming profanities and insults while sales rep is calm.
    Verify customer speech immunity through full DB-backed run_tone_stage and GET /analysis.
    The sales representative MUST remain GREEN with 0 evidence violations.
    """
    call_id = f"test-anger-{uuid.uuid4().hex[:8]}"
    call = Call(
        id=call_id,
        original_filename="hostile_customer_call.wav",
        size_bytes=10240,
        storage_key=f"{call_id}.wav",
        status="complete"
    )
    db.add(call)

    transcript = Transcript(call_id=call_id, status="completed", provider="whisper")
    db.add(transcript)

    # Speaker roles: A is calm rep, B is hostile customer
    role_rep = SpeakerRole(call_id=call_id, speaker_label="A", role="sales_rep", source="auto", status="confirmed", level="high")
    role_cust = SpeakerRole(call_id=call_id, speaker_label="B", role="customer", source="auto", status="confirmed", level="high")
    db.add_all([role_rep, role_cust])

    # Utterances (Rep speaks for > 25 seconds total)
    utts = [
        Utterance(id=f"u-{call_id}-1", call_id=call_id, idx=1, speaker_label="A", start_ms=0, end_ms=8000,
                  text="Good morning, thank you for contacting Brightwave support. How can I help you today?"),
        Utterance(id=f"u-{call_id}-2", call_id=call_id, idx=2, speaker_label="B", start_ms=8500, end_ms=20000,
                  text="You are all complete incompetent idiots and your garbage software destroyed my data! Shut up and refund my money right now!"),
        Utterance(id=f"u-{call_id}-3", call_id=call_id, idx=3, speaker_label="A", start_ms=20500, end_ms=38000,
                  text="I understand how frustrating this is, and I sincerely apologize for the inconvenience. I will review the system logs and email you an update by 4 PM."),
        Utterance(id=f"u-{call_id}-4", call_id=call_id, idx=4, speaker_label="B", start_ms=38500, end_ms=48000,
                  text="You better do it or I am getting your entire team fired, you morons!"),
        Utterance(id=f"u-{call_id}-5", call_id=call_id, idx=5, speaker_label="A", start_ms=48500, end_ms=58000,
                  text="Thank you for your patience, we take this seriously and will have this resolved today.")
    ]
    db.add_all(utts)
    db.commit()

    # Simulate LLM returning a candidate finding on the customer utterance
    def mock_generate_json(self, system_prompt, user_prompt):
        return {
            "has_negative_tone": True,
            "candidate_findings": [
                {
                    "utterance_id": f"u-{call_id}-2",
                    "quote": "Shut up and refund my money right now!",
                    "criterion_id": "rude",
                    "severity": 3,
                    "rationale": "Customer was extremely rude."
                }
            ]
        }
    monkeypatch.setattr("app.pipeline.providers.llm.ollama.OllamaLlmProvider.generate_json", mock_generate_json)

    try:
        # Run DB-backed tone stage
        res = run_tone_stage(db, call_id)
        assert res["verdict"] == "GREEN"
        assert res["evidence_count"] == 0

        # Verify DB analysis record
        analysis = db.query(Analysis).filter(Analysis.call_id == call_id).first()
        assert analysis is not None
        assert analysis.verdict == "GREEN"
        assert analysis.rep_speaker_label == "A"
        assert analysis.status == "complete"
        assert len(analysis.evidence_items) == 0

        # Verify API response
        r = client.get(f"/api/v1/calls/{call_id}/analysis")
        assert r.status_code == 200
        data = r.json()
        assert data["verdict"] == "GREEN"
        assert len(data["evidence"]) == 0
        assert data["sales_rep"]["label"] == "A"

    finally:
        db.query(EvidenceItem).filter(EvidenceItem.call_id == call_id).delete()
        db.query(Analysis).filter(Analysis.call_id == call_id).delete()
        db.query(Utterance).filter(Utterance.call_id == call_id).delete()
        db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id).delete()
        db.query(Transcript).filter(Transcript.call_id == call_id).delete()
        db.query(Call).filter(Call.id == call_id).delete()
        db.commit()

# ==============================================================================
# b) NEEDS_REVIEW Verdict Trigger and DB Persistence
# ==============================================================================
def test_needs_review_verdict_low_duration_and_db_persistence(client, db, monkeypatch):
    """
    Sales rep speaks for less than 15 seconds.
    Tone analysis must assign NEEDS_REVIEW with low confidence and limited_evidence_reason.
    Must persist to SQLite and filter via /calls?tone=needs_review.
    """
    call_id = f"test-nr-{uuid.uuid4().hex[:8]}"
    call = Call(
        id=call_id,
        original_filename="short_pleasantry_call.wav",
        size_bytes=4096,
        storage_key=f"{call_id}.wav",
        status="complete"
    )
    db.add(call)
    db.add(Transcript(call_id=call_id, status="completed", provider="whisper"))

    role_rep = SpeakerRole(call_id=call_id, speaker_label="A", role="sales_rep", source="auto", status="confirmed", level="high")
    role_cust = SpeakerRole(call_id=call_id, speaker_label="B", role="customer", source="auto", status="confirmed", level="high")
    db.add_all([role_rep, role_cust])

    # Rep speaks for only 7 seconds total
    utts = [
        Utterance(id=f"u-{call_id}-1", call_id=call_id, idx=1, speaker_label="A", start_ms=0, end_ms=4000,
                  text="Brightwave support, how can I help?"),
        Utterance(id=f"u-{call_id}-2", call_id=call_id, idx=2, speaker_label="B", start_ms=4500, end_ms=10000,
                  text="I'm just checking if my account is active."),
        Utterance(id=f"u-{call_id}-3", call_id=call_id, idx=3, speaker_label="A", start_ms=10500, end_ms=13500,
                  text="Yes it is, have a great day!")
    ]
    db.add_all(utts)
    db.commit()

    def mock_empty_generate_json(self, system_prompt, user_prompt):
        return {"has_negative_tone": False, "candidate_findings": []}
    monkeypatch.setattr("app.pipeline.providers.llm.ollama.OllamaLlmProvider.generate_json", mock_empty_generate_json)

    try:
        res = run_tone_stage(db, call_id)
        assert res["verdict"] == "NEEDS_REVIEW"

        # Verify DB analysis record
        analysis = db.query(Analysis).filter(Analysis.call_id == call_id).first()
        assert analysis is not None
        assert analysis.verdict == "NEEDS_REVIEW"
        assert analysis.confidence_level == "low"
        assert analysis.limited_evidence_reason == "Sales representative spoke for less than 15 seconds."

        # Filter calls by NEEDS_REVIEW
        r_list = client.get("/api/v1/calls?tone=needs_review")
        assert r_list.status_code == 200
        items = r_list.json()["items"]
        assert any(item["id"] == call_id and item["tone"] == "NEEDS_REVIEW" for item in items)

        # GET analysis endpoint returns NEEDS_REVIEW
        r_analysis = client.get(f"/api/v1/calls/{call_id}/analysis")
        assert r_analysis.status_code == 200
        data = r_analysis.json()
        assert data["verdict"] == "NEEDS_REVIEW"
        assert data["confidence"]["level"] == "low"
        assert data["limited_evidence_reason"] == "Sales representative spoke for less than 15 seconds."

    finally:
        db.query(Analysis).filter(Analysis.call_id == call_id).delete()
        db.query(Utterance).filter(Utterance.call_id == call_id).delete()
        db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id).delete()
        db.query(Transcript).filter(Transcript.call_id == call_id).delete()
        db.query(Call).filter(Call.id == call_id).delete()
        db.commit()

def test_needs_review_verdict_triggers():
    """
    Unit test all safeguard branches for NEEDS_REVIEW classification:
    1. Low speaker role confidence
    2. Numerical confidence < 0.70
    3. Low confidence violation (potential RED converted to NEEDS_REVIEW)
    4. Mixed/borderline indicators
    5. Partial non-compliance
    """
    rep_utts = [{"id": "u1", "speaker_label": "A", "text": "Hello, thank you for reaching out today."}]

    # 1. Low speaker role confidence
    r_role = evaluate_tone_verdict([], rep_utts, {"rude"}, "medium", 35.0, role_level="low")
    assert r_role["verdict"] == "NEEDS_REVIEW"
    assert r_role["confidence_level"] == "low"

    # 2. Explicit confidence < 0.70
    r_conf = evaluate_tone_verdict([], rep_utts, {"rude"}, "medium", 35.0, role_level="high", confidence=0.62)
    assert r_conf["verdict"] == "NEEDS_REVIEW"
    assert r_conf["confidence_level"] == "low"

    # 3. Violation with low role confidence converts potential RED to NEEDS_REVIEW
    violating_utts = [{"id": "u1", "speaker_label": "A", "text": "Shut up and listen to me!"}]
    r_viol_low = evaluate_tone_verdict([], violating_utts, {"rude"}, "medium", 35.0, role_level="low")
    assert r_viol_low["verdict"] == "NEEDS_REVIEW"

    # 4. Mixed / borderline indicators
    r_borderline = evaluate_tone_verdict(
        [{"utterance_id": "u1", "quote": "something", "severity": 2, "borderline": True}],
        rep_utts, {"rude"}, "medium", 35.0, role_level="high"
    )
    assert r_borderline["verdict"] == "NEEDS_REVIEW"

    # 5. Partial non-compliance
    r_partial = evaluate_tone_verdict([], rep_utts, {"rude"}, "medium", 35.0, role_level="high", partial_non_compliance=True)
    assert r_partial["verdict"] == "NEEDS_REVIEW"

# ==============================================================================
# c) CoachingRecommendation DB Model, Migration, Schema & API Serialization
# ==============================================================================
def test_coaching_recommendation_db_model_and_constraints(db):
    """
    Verify CoachingRecommendation model in SQLite:
    - Primary key, foreign keys, unique constraint on (analysis_id, ref).
    - Check constraint on severity IN ('suggestion', 'important', 'critical').
    """
    call_id = f"test-coach-{uuid.uuid4().hex[:8]}"
    call = Call(id=call_id, original_filename="coaching_test.wav", size_bytes=1000, storage_key=f"{call_id}.wav", status="complete")
    db.add(call)
    db.add(Transcript(call_id=call_id, status="completed", provider="whisper"))

    role = SpeakerRole(call_id=call_id, speaker_label="A", role="sales_rep", status="confirmed")
    db.add(role)

    utt = Utterance(id=f"u-{call_id}-1", call_id=call_id, idx=1, speaker_label="A", start_ms=0, end_ms=5000, text="Let me talk about features.")
    db.add(utt)

    analysis = Analysis(
        id=f"a-{call_id}-1",
        call_id=call_id,
        run_number=1,
        settings_version=1,
        status="complete",
        verdict="GREEN"
    )
    db.add(analysis)
    db.commit()

    try:
        # Create valid coaching recommendation
        coach1 = CoachingRecommendation(
            id=str(uuid.uuid4()),
            analysis_id=analysis.id,
            call_id=call_id,
            ref="C1",
            category="objection_handling",
            recommendation="Acknowledge budget constraint before pricing pitch.",
            context_quote="too expensive",
            severity="important",
            utterance_id=utt.id
        )
        db.add(coach1)
        db.commit()

        loaded = db.query(CoachingRecommendation).filter(CoachingRecommendation.id == coach1.id).first()
        assert loaded is not None
        assert loaded.ref == "C1"
        assert loaded.category == "objection_handling"
        assert loaded.severity == "important"
        assert loaded.context_quote == "too expensive"
        assert loaded.utterance_id == utt.id

        # Unique constraint on (analysis_id, ref)
        coach_dup = CoachingRecommendation(
            id=str(uuid.uuid4()),
            analysis_id=analysis.id,
            call_id=call_id,
            ref="C1",  # duplicate ref
            category="pacing",
            recommendation="Slow down speech.",
            severity="suggestion"
        )
        db.add(coach_dup)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()

        # Check constraint on severity
        coach_bad_sev = CoachingRecommendation(
            id=str(uuid.uuid4()),
            analysis_id=analysis.id,
            call_id=call_id,
            ref="C2",
            category="pacing",
            recommendation="Slow down speech.",
            severity="invalid_severity"
        )
        db.add(coach_bad_sev)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()

    finally:
        db.query(CoachingRecommendation).filter(CoachingRecommendation.call_id == call_id).delete()
        db.query(Analysis).filter(Analysis.call_id == call_id).delete()
        db.query(Utterance).filter(Utterance.call_id == call_id).delete()
        db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id).delete()
        db.query(Transcript).filter(Transcript.call_id == call_id).delete()
        db.query(Call).filter(Call.id == call_id).delete()
        db.commit()

def test_pydantic_schema_serialization():
    """Verify CoachingRecommendationResponse and AnalysisResponse schemas."""
    coach_data = {
        "id": "c-1",
        "analysis_id": "a-1",
        "call_id": "call-1",
        "ref": "C1",
        "category": "objection_handling",
        "recommendation": "Ask clarifying questions before proposing solutions.",
        "context_quote": "We already have a solution.",
        "severity": "important",
        "utterance_id": "u-1",
        "start_ms": 1200
    }
    schema = CoachingRecommendationResponse(**coach_data)
    assert schema.ref == "C1"
    assert schema.category == "objection_handling"
    assert schema.severity == "important"

# ==============================================================================
# d) Action Items vs Coaching Separation
# ==============================================================================
def test_action_items_vs_coaching_separation(client, db, monkeypatch):
    """
    Ensure clear separation between concrete commitments (ActionItem)
    and constructive behavioral advice (CoachingRecommendation).
    Verify GET /analysis returns both distinct categories.
    """
    call_id = f"test-sep-{uuid.uuid4().hex[:8]}"
    call = Call(id=call_id, original_filename="action_coaching.wav", size_bytes=2048, storage_key=f"{call_id}.wav", status="complete")
    db.add(call)
    db.add(Transcript(call_id=call_id, status="completed", provider="whisper"))

    role_rep = SpeakerRole(call_id=call_id, speaker_label="A", role="sales_rep", source="auto", status="confirmed", level="high")
    role_cust = SpeakerRole(call_id=call_id, speaker_label="B", role="customer", source="auto", status="confirmed", level="high")
    db.add_all([role_rep, role_cust])

    u1 = Utterance(id=f"u-{call_id}-1", call_id=call_id, idx=1, speaker_label="A", start_ms=0, end_ms=8000,
                   text="I will email the pricing proposal to your team by Friday afternoon.")
    u2 = Utterance(id=f"u-{call_id}-2", call_id=call_id, idx=2, speaker_label="B", start_ms=8500, end_ms=16000,
                   text="That sounds fine, but your pricing is really expensive for our budget.")
    db.add_all([u1, u2])

    analysis = Analysis(
        id=f"a-{call_id}-1",
        call_id=call_id,
        run_number=1,
        settings_version=1,
        status="complete",
        verdict="GREEN"
    )
    db.add(analysis)
    db.commit()

    def mock_action_generate_json(self, system_prompt, user_prompt):
        return {
            "candidate_actions": [
                {
                    "utterance_id": f"u-{call_id}-1",
                    "task": "Email pricing proposal by Friday",
                    "type": "information_promised",
                    "modality": "definite",
                    "owner_text": "Sales Rep",
                    "owner_basis": "committing_speaker",
                    "deadline_text": "by Friday afternoon",
                    "quote": "I will email the pricing proposal to your team by Friday afternoon."
                }
            ],
            "candidate_coaching": [
                {
                    "utterance_id": f"u-{call_id}-2",
                    "category": "objection_handling",
                    "recommendation": "Address budget objection before committing to discounts.",
                    "context_quote": "pricing is really expensive",
                    "severity": "important"
                }
            ]
        }
    monkeypatch.setattr("app.pipeline.providers.llm.ollama.OllamaLlmProvider.generate_json", mock_action_generate_json)

    try:
        # Run action items stage
        res = run_action_items_stage(db, call_id)
        assert res["action_count"] >= 1
        assert res["coaching_count"] >= 1

        # Check ActionItem records: concrete deliverable with owner & deadline
        actions = db.query(ActionItem).filter(ActionItem.call_id == call_id).all()
        assert len(actions) >= 1
        act = actions[0]
        assert act.type in ("commitment", "information_promised", "follow_up")
        assert act.deadline_text is not None
        assert act.char_start >= 0 and act.char_end > act.char_start

        # Check CoachingRecommendation records: behavioral feedback with category & severity
        coaching = db.query(CoachingRecommendation).filter(CoachingRecommendation.call_id == call_id).all()
        assert len(coaching) >= 1
        coach = coaching[0]
        assert coach.category in ("objection_handling", "pacing", "active_listening", "professionalism", "product_knowledge")
        assert coach.severity in ("suggestion", "important", "critical")

        # Query GET /analysis
        r = client.get(f"/api/v1/calls/{call_id}/analysis")
        assert r.status_code == 200
        data = r.json()
        assert "action_items" in data
        assert "coaching_recommendations" in data
        assert len(data["action_items"]) >= 1
        assert len(data["coaching_recommendations"]) >= 1

        # Action item contains char_start and char_end
        api_act = data["action_items"][0]
        assert "char_start" in api_act
        assert "char_end" in api_act
        assert api_act["char_end"] > api_act["char_start"]

        # Coaching recommendation contains category and severity
        api_coach = data["coaching_recommendations"][0]
        assert "category" in api_coach
        assert "severity" in api_coach
        assert "recommendation" in api_coach

    finally:
        db.query(CoachingRecommendation).filter(CoachingRecommendation.call_id == call_id).delete()
        db.query(ActionItem).filter(ActionItem.call_id == call_id).delete()
        db.query(Analysis).filter(Analysis.call_id == call_id).delete()
        db.query(Utterance).filter(Utterance.call_id == call_id).delete()
        db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id).delete()
        db.query(Transcript).filter(Transcript.call_id == call_id).delete()
        db.query(Call).filter(Call.id == call_id).delete()
        db.commit()

# ==============================================================================
# e) Quote Substring Span Boundaries and SQLite Triggers
# ==============================================================================
def test_quote_substring_span_boundaries_and_sqlite_triggers(db):
    """
    Test quote matching logic and SQLite database triggers:
    1. verify_evidence_quote strictly checks that utterance_text[start:end] == quote.
    2. SQLite trigger trg_evidence_quote_is_transcript_span aborts mismatched quote insertion.
    3. SQLite trigger trg_action_quote_is_transcript_span aborts mismatched quote insertion.
    """
    text = "Please check the attached contract terms before signing."
    quote = "attached contract terms"
    offsets = find_quote_offsets(text, quote)
    assert offsets is not None
    start, end = offsets

    # Exact match verifies True
    assert verify_evidence_quote(text, quote, start, end) is True

    # Mismatched quote content returns False
    assert verify_evidence_quote(text, "different quote", start, end) is False

    # Out of bounds returns False
    assert verify_evidence_quote(text, quote, -1, end) is False
    assert verify_evidence_quote(text, quote, start, len(text) + 10) is False
    assert verify_evidence_quote(text, quote, end, start) is False

    # Test SQLite triggers
    call_id = f"test-trg-{uuid.uuid4().hex[:8]}"
    call = Call(id=call_id, original_filename="trigger_test.wav", size_bytes=1000, storage_key=f"{call_id}.wav", status="complete")
    db.add(call)
    db.add(Transcript(call_id=call_id, status="completed", provider="whisper"))

    role = SpeakerRole(call_id=call_id, speaker_label="A", role="sales_rep", status="confirmed")
    db.add(role)

    utt = Utterance(id=f"u-{call_id}-1", call_id=call_id, idx=1, speaker_label="A", start_ms=0, end_ms=5000, text=text)
    db.add(utt)

    analysis = Analysis(id=f"a-{call_id}-1", call_id=call_id, run_number=1, settings_version=1, status="complete", verdict="RED")
    db.add(analysis)
    db.commit()

    try:
        # Valid EvidenceItem insertion succeeds
        ev_valid = EvidenceItem(
            id=str(uuid.uuid4()),
            analysis_id=analysis.id,
            call_id=call_id,
            ref="E1",
            utterance_id=utt.id,
            speaker_label="A",
            quote=quote,
            char_start=start,
            char_end=end,
            criterion_id="rude",
            severity=2,
            rationale="Quote matches exactly"
        )
        db.add(ev_valid)
        db.commit()

        # Mismatched EvidenceItem insertion is aborted by SQLite trigger
        ev_invalid = EvidenceItem(
            id=str(uuid.uuid4()),
            analysis_id=analysis.id,
            call_id=call_id,
            ref="E2",
            utterance_id=utt.id,
            speaker_label="A",
            quote="hallucinated quote not in transcript",
            char_start=start,
            char_end=end,
            criterion_id="rude",
            severity=2,
            rationale="Trigger should abort"
        )
        db.add(ev_invalid)
        with pytest.raises(Exception) as exc:
            db.commit()
        assert "evidence quote is not the transcript span" in str(exc.value)
        db.rollback()

        # Valid ActionItem insertion succeeds
        act_valid = ActionItem(
            id=str(uuid.uuid4()),
            analysis_id=analysis.id,
            call_id=call_id,
            ref="A1",
            type="commitment",
            task="Check contract terms",
            modality="definite",
            utterance_id=utt.id,
            speaker_label="A",
            quote=quote,
            char_start=start,
            char_end=end
        )
        db.add(act_valid)
        db.commit()

        # Mismatched ActionItem insertion is aborted by SQLite trigger
        act_invalid = ActionItem(
            id=str(uuid.uuid4()),
            analysis_id=analysis.id,
            call_id=call_id,
            ref="A2",
            type="commitment",
            task="Check contract terms",
            modality="definite",
            utterance_id=utt.id,
            speaker_label="A",
            quote="hallucinated action quote",
            char_start=start,
            char_end=end
        )
        db.add(act_invalid)
        with pytest.raises(Exception) as exc_act:
            db.commit()
        assert "action-item quote is not the transcript span" in str(exc_act.value)
        db.rollback()

    finally:
        db.query(ActionItem).filter(ActionItem.call_id == call_id).delete()
        db.query(EvidenceItem).filter(EvidenceItem.call_id == call_id).delete()
        db.query(Analysis).filter(Analysis.call_id == call_id).delete()
        db.query(Utterance).filter(Utterance.call_id == call_id).delete()
        db.query(SpeakerRole).filter(SpeakerRole.call_id == call_id).delete()
        db.query(Transcript).filter(Transcript.call_id == call_id).delete()
        db.query(Call).filter(Call.id == call_id).delete()
        db.commit()
