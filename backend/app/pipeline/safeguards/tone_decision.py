from typing import Any
from app.pipeline.safeguards.quote_matcher import find_quote_offsets

def evaluate_tone_verdict(
    candidate_findings: list[dict[str, Any]],
    rep_utterances: list[dict[str, Any]],
    enabled_criteria_ids: set[str],
    sensitivity: str,
    rep_total_seconds: float,
    role_level: str
) -> dict[str, Any]:
    """
    Evaluates verified tone evidence items and determines final RED / GREEN verdict.
    Strictly follows PRD FR-T1..FR-T7 and AGENTS.md Section 5.
    """
    rep_utt_map = {u["id"]: u for u in rep_utterances}
    verified_evidence = []
    dropped_count = 0
    dropped_reasons = []

    # Severity threshold based on sensitivity
    # High sensitivity: catches severity >= 1
    # Medium sensitivity: catches severity >= 2
    # Low sensitivity: catches severity >= 3
    threshold_map = {
        "high": 1,
        "medium": 2,
        "low": 3
    }
    required_severity = threshold_map.get(sensitivity.lower(), 2)

    for idx, f in enumerate(candidate_findings):
        utt_id = f.get("utterance_id")
        quote = f.get("quote", "").strip()
        criterion_id = f.get("criterion_id", "").lower()
        severity = int(f.get("severity", 2))
        rationale = f.get("rationale", "")

        # Check 1: Did it cite a rep utterance?
        if utt_id not in rep_utt_map:
            dropped_count += 1
            dropped_reasons.append(f"Finding {idx+1}: Utterance '{utt_id}' is not attributed to the sales representative.")
            continue

        # Check 2: Is criterion enabled?
        if criterion_id not in enabled_criteria_ids:
            dropped_count += 1
            dropped_reasons.append(f"Finding {idx+1}: Criterion '{criterion_id}' is disabled in settings.")
            continue

        # Check 3: Is the quote verbatim in the utterance?
        target_text = rep_utt_map[utt_id]["text"]
        offsets = find_quote_offsets(target_text, quote)
        if not offsets:
            dropped_count += 1
            dropped_reasons.append(f"Finding {idx+1}: Quote '{quote[:40]}...' is not verbatim in utterance.")
            continue

        char_start, char_end = offsets
        ref_id = f"E{len(verified_evidence) + 1}"

        verified_evidence.append({
            "ref": ref_id,
            "utterance_id": utt_id,
            "speaker_label": rep_utt_map[utt_id]["speaker_label"],
            "quote": target_text[char_start:char_end],
            "char_start": char_start,
            "char_end": char_end,
            "criterion_id": criterion_id,
            "severity": severity,
            "rationale": rationale or f"Exhibits {criterion_id} tone."
        })

    # Filter by sensitivity threshold
    qualifying_evidence = [e for e in verified_evidence if e["severity"] >= required_severity]

    # Decide verdict
    if qualifying_evidence:
        verdict = "RED"
        matched_criteria = ", ".join(sorted({e["criterion_id"].capitalize() for e in qualifying_evidence}))
        explanation = (
            f"The sales representative exhibited unprofessional behavior matching the configured criteria "
            f"({matched_criteria}) at {sensitivity.capitalize()} sensitivity, supported by {len(qualifying_evidence)} "
            f"verified transcript evidence quote(s)."
        )
    else:
        verdict = "GREEN"
        explanation = (
            f"No negative sales representative tone detected under the configured criteria at {sensitivity.capitalize()} sensitivity."
        )

    # Compute confidence level
    limited_evidence_reason = None
    if rep_total_seconds < 15:
        confidence_level = "low"
        limited_evidence_reason = "Sales representative spoke for less than 15 seconds."
    elif role_level == "low":
        confidence_level = "low"
        limited_evidence_reason = "Speaker role attribution has low confidence."
    elif rep_total_seconds < 35:
        confidence_level = "medium"
    else:
        confidence_level = "high"

    return {
        "verdict": verdict,
        "confidence_level": confidence_level,
        "limited_evidence_reason": limited_evidence_reason,
        "explanation": explanation,
        "evidence_items": qualifying_evidence if verdict == "RED" else [],
        "dropped_evidence_count": dropped_count,
        "dropped_details": {"reasons": dropped_reasons} if dropped_reasons else None
    }
