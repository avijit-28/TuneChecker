import re
from typing import Any, Optional

VALID_CATEGORIES = {
    "objection_handling",
    "pacing",
    "active_listening",
    "professionalism",
    "product_knowledge"
}

VALID_SEVERITIES = {"suggestion", "important", "critical"}

def evaluate_coaching_recommendations(
    candidate_coaching: list[dict[str, Any]],
    utterances: list[dict[str, Any]],
    rep_speaker_label: Optional[str] = "A"
) -> list[dict[str, Any]]:
    """
    Evaluates, normalizes, and verifies sales coaching recommendations.
    Combines LLM-generated recommendations with deterministic conversational heuristics.
    """
    utt_map = {u["id"]: u for u in utterances}
    verified_coaching = []
    seen_recommendations = set()

    # 1. Deterministic Heuristic Safeguards
    heuristic_recommendations = []
    for u in utterances:
        text = u.get("text", "")
        spk = u.get("speaker_label")
        u_id = u.get("id")

        if spk != rep_speaker_label:
            # Customer mentions pricing / budget
            if re.search(r"\b(expensive|budget|pricing|cost|afford|discount|out of.*price)\b", text, re.IGNORECASE):
                heuristic_recommendations.append({
                    "utterance_id": u_id,
                    "category": "objection_handling",
                    "recommendation": "Acknowledge customer pricing sensitivity and quantify ROI/value metrics before proposing concessions.",
                    "context_quote": text[:200],
                    "severity": "important"
                })
            # Customer mentions competitor
            if re.search(r"\b(competitor|alternative|another vendor|evaluating others)\b", text, re.IGNORECASE):
                heuristic_recommendations.append({
                    "utterance_id": u_id,
                    "category": "objection_handling",
                    "recommendation": "Highlight unique product capabilities and competitive differentiators rather than general feature lists.",
                    "context_quote": text[:200],
                    "severity": "suggestion"
                })
        else:
            # Rep pacing: long monologue (> 45 words)
            words = text.split()
            if len(words) > 45:
                heuristic_recommendations.append({
                    "utterance_id": u_id,
                    "category": "pacing",
                    "recommendation": "Pause during lengthy explanations to ask open-ended check-in questions and verify customer alignment.",
                    "context_quote": " ".join(words[:15]) + "...",
                    "severity": "suggestion"
                })
            # Rep professionalism
            if re.search(r"\b(bro|baby|dude|whatever)\b", text, re.IGNORECASE):
                heuristic_recommendations.append({
                    "utterance_id": u_id,
                    "category": "professionalism",
                    "recommendation": "Maintain formal business vocabulary and eliminate casual slang during sales discussions.",
                    "context_quote": text[:200],
                    "severity": "important"
                })

    all_candidates = list(candidate_coaching) + heuristic_recommendations

    for item in all_candidates:
        category = item.get("category", "active_listening").lower().strip()
        if category not in VALID_CATEGORIES:
            category = "professionalism" if "profess" in category else "objection_handling"
        severity = item.get("severity", "suggestion").lower().strip()
        if severity not in VALID_SEVERITIES:
            severity = "suggestion"
        recommendation = item.get("recommendation", "").strip()
        if not recommendation:
            continue

        rec_key = (category, recommendation[:80].lower())
        if rec_key in seen_recommendations:
            continue
        seen_recommendations.add(rec_key)

        utt_id = item.get("utterance_id")
        context_quote = item.get("context_quote")
        if utt_id and utt_id in utt_map:
            u_text = utt_map[utt_id]["text"]
            if not context_quote:
                context_quote = u_text[:200]
        else:
            utt_id = None

        ref_id = f"C{len(verified_coaching) + 1}"
        verified_coaching.append({
            "ref": ref_id,
            "category": category,
            "recommendation": recommendation[:1000],
            "context_quote": context_quote[:500] if context_quote else None,
            "severity": severity,
            "utterance_id": utt_id
        })

    return verified_coaching
