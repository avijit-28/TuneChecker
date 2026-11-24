import re
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
    Combines LLM findings with deterministic tone safeguard patterns.
    """
    rep_utt_map = {u["id"]: u for u in rep_utterances}
    verified_evidence = []
    dropped_count = 0
    dropped_reasons = []

    # Severity threshold based on sensitivity
    threshold_map = {
        "high": 1,
        "medium": 2,
        "low": 3
    }
    required_severity = threshold_map.get(sensitivity.lower(), 2)

    # 1. Deterministic Safeguard Heuristics for Rep Utterances
    heuristic_patterns = [
        (re.compile(r"\b(are you kidding|shut up|nonsense|ridiculous|not my problem|don't care)\b", re.IGNORECASE), "rude", 3, "Blatantly disrespectful or hostile statement."),
        (re.compile(r"\b(whatever you know|whatever, you know|like whatever)\b", re.IGNORECASE), "dismissive", 2, "Dismissive phrasing regarding accounts/client requirements."),
        (re.compile(r"\b(bro|baby)\b", re.IGNORECASE), "unprofessional", 2, "Overly casual slang or pet name inappropriate for professional sales."),
    ]

    combined_findings = list(candidate_findings)
    for u in rep_utterances:
        text = u.get("text", "")
        for pattern, crit, sev, rat in heuristic_patterns:
            m = pattern.search(text)
            if m:
                combined_findings.append({
                    "utterance_id": u["id"],
                    "quote": text,
                    "criterion_id": crit,
                    "severity": sev,
                    "rationale": rat
                })

    seen_evidence = set()

    for idx, f in enumerate(combined_findings):
        utt_id = f.get("utterance_id")
        quote = f.get("quote", "").strip()
        criterion_id = f.get("criterion_id", "").lower()
        severity = int(f.get("severity", 2))
        rationale = f.get("rationale", "")

        if not quote:
            continue

        # Check 1: Find matching rep utterance
        target_utt = None
        if utt_id and utt_id in rep_utt_map:
            target_utt = rep_utt_map[utt_id]
        else:
            for u in rep_utterances:
                if find_quote_offsets(u["text"], quote):
                    target_utt = u
                    utt_id = u["id"]
                    break

        if not target_utt:
            dropped_count += 1
            dropped_reasons.append(f"Finding {idx+1}: Quote '{quote[:40]}' not found in representative utterances.")
            continue

        # Check 2: Is criterion enabled?
        if criterion_id not in enabled_criteria_ids:
            dropped_count += 1
            dropped_reasons.append(f"Finding {idx+1}: Criterion '{criterion_id}' is disabled in settings.")
            continue

        # Check 3: Is the quote in the utterance?
        target_text = target_utt["text"]
        offsets = find_quote_offsets(target_text, quote)
        if not offsets:
            dropped_count += 1
            dropped_reasons.append(f"Finding {idx+1}: Quote '{quote[:40]}...' is not verbatim in utterance.")
            continue

        char_start, char_end = offsets
        actual_quote = target_text[char_start:char_end]

        ev_key = (target_utt["id"], criterion_id, actual_quote.lower().strip())
        if ev_key in seen_evidence:
            continue
        seen_evidence.add(ev_key)

        ref_id = f"E{len(verified_evidence) + 1}"

        verified_evidence.append({
            "ref": ref_id,
            "utterance_id": utt_id,
            "speaker_label": target_utt["speaker_label"],
            "quote": actual_quote,
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
