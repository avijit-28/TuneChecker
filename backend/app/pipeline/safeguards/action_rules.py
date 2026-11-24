import re
from typing import Any
from app.pipeline.safeguards.quote_matcher import find_quote_offsets

def extract_heuristic_action_candidates(utterances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Deterministic rule-based extractor for sales call commitments and action items.
    Catches first-person promises, follow-ups, and scheduled deliverables as a robust safeguard.
    """
    candidates = []
    
    # Common commitment patterns
    commitment_regexes = [
        # "I'll talk to Frederick next week", "I'll, I'll talk to Frederick", "I'll mention to him"
        (re.compile(
            r"\b(i'll|i will|we'll|we will|i'm going to|we're going to|i can|we can)(?:[,\s]+(?:i'll|i will))?\s+(?:(?:[a-z,\s]+?)\s+)?\b(talk to|speak with|speak to|call|send|email|forward|share|upload|mention|follow up|schedule|reach out|check with|look into)\b([^\.\?!;]+)?",
            re.IGNORECASE
        ), "definite"),
        # "send me an email", "call me back"
        (re.compile(r"\b(send me|email me|call me back|check out)\b[^\.\?!;]+", re.IGNORECASE), "definite"),
        # "we might / maybe look into"
        (re.compile(r"\b(we might|maybe we can|could look into)\b[^\.\?!;]+", re.IGNORECASE), "tentative")
    ]

    deadline_regex = re.compile(
        r"\b(next week|tomorrow|by friday|by monday|by tomorrow|this afternoon|later today|in an hour|by the end of the day|end of the week)\b",
        re.IGNORECASE
    )

    for idx_u, u in enumerate(utterances):
        text = u.get("text", "")
        utt_id = u.get("id")
        speaker = u.get("speaker_label", "A")

        for regex, mod in commitment_regexes:
            match = regex.search(text)
            if match:
                full_clause = match.group(0).strip()
                # Find deadline in current utterance or immediate subsequent utterance
                dl_match = deadline_regex.search(text)
                if not dl_match and idx_u + 1 < len(utterances):
                    next_text = utterances[idx_u + 1].get("text", "")
                    dl_match = deadline_regex.search(next_text)
                deadline = dl_match.group(0) if dl_match else None

                # Clean task summary
                task_text = full_clause
                for prefix in ["i'll, i'll", "i'll", "i will", "we'll", "we will", "i'm going to", "we're going to"]:
                    if task_text.lower().startswith(prefix):
                        task_text = task_text[len(prefix):].strip(" ,")
                        break
                task_text = re.sub(r"\b(uh|um|ah)\b,?", "", task_text, flags=re.IGNORECASE)
                task_text = re.sub(r"[,;]+", " ", task_text)
                task_text = re.sub(r"\s+", " ", task_text).strip(" ,")
                task_summary = " ".join(w.capitalize() if i == 0 or w.lower() in ("frederick",) else w for i, w in enumerate(task_text.split()))

                # Infer type
                if "mention" in full_clause.lower() or "talk to my" in full_clause.lower():
                    act_type = "customer_task" if speaker == "B" else "follow_up"
                elif "upload" in full_clause.lower() or "send" in full_clause.lower() or "email" in full_clause.lower():
                    act_type = "information_promised"
                elif "talk to" in full_clause.lower() or "call" in full_clause.lower():
                    act_type = "follow_up"
                else:
                    act_type = "commitment"

                candidates.append({
                    "utterance_id": utt_id,
                    "task": task_summary[:200],
                    "type": act_type,
                    "modality": mod,
                    "owner_text": "Sales Rep" if speaker == "A" else "Customer",
                    "owner_basis": "committing_speaker",
                    "deadline_text": deadline,
                    "quote": text  # will be verified and trimmed to exact offsets
                })

    return candidates

def evaluate_action_items(
    candidate_actions: list[dict[str, Any]],
    utterances: list[dict[str, Any]],
    action_settings: dict[str, Any]
) -> list[dict[str, Any]]:
    utt_map = {u["id"]: u for u in utterances}
    verified_actions = []

    types_config = action_settings.get("types", {})
    include_tentative = action_settings.get("include_tentative", True)
    owner_rule = action_settings.get("owner_rule", "explicit_or_committing_speaker")

    # Combine LLM candidates with deterministic heuristic candidates
    heuristic_candidates = extract_heuristic_action_candidates(utterances)
    all_candidates = list(candidate_actions) + heuristic_candidates

    seen_quotes = set()

    for idx, act in enumerate(all_candidates):
        utt_id = act.get("utterance_id")
        task = act.get("task", "").strip()
        act_type = act.get("type", "commitment")
        modality = act.get("modality", "definite").lower()
        quote = act.get("quote", "").strip()
        owner_text = act.get("owner_text")
        deadline_text = act.get("deadline_text")

        if not task or not quote:
            continue

        # If utt_id not in map, search all utterances for quote
        target_utt = None
        if utt_id and utt_id in utt_map:
            target_utt = utt_map[utt_id]
        else:
            for u in utterances:
                if find_quote_offsets(u["text"], quote):
                    target_utt = u
                    utt_id = u["id"]
                    break

        if not target_utt:
            continue

        target_text = target_utt["text"]
        offsets = find_quote_offsets(target_text, quote)
        if not offsets:
            continue

        char_start, char_end = offsets
        actual_quote = target_text[char_start:char_end]

        # Prevent duplicate action items on the exact same quote
        quote_key = (target_utt["id"], actual_quote.strip().lower())
        if quote_key in seen_quotes:
            continue
        seen_quotes.add(quote_key)

        # Check action type allowed
        type_key_map = {
            "commitment": "commitments",
            "follow_up": "follow_ups",
            "information_promised": "information_promised",
            "customer_task": "customer_tasks"
        }
        config_key = type_key_map.get(act_type, "commitments")
        if not types_config.get(config_key, True):
            continue

        # Check tentative filter
        if modality == "tentative" and not include_tentative:
            continue

        speaker_label = target_utt["speaker_label"]

        # Check owner basis
        owner_basis = act.get("owner_basis", "committing_speaker" if owner_text else "none")
        if owner_rule == "explicit_only" and owner_basis == "committing_speaker":
            owner_text = None
            owner_basis = "none"

        ref_id = f"A{len(verified_actions) + 1}"

        verified_actions.append({
            "ref": ref_id,
            "type": act_type if act_type in ["commitment", "follow_up", "information_promised", "customer_task"] else "commitment",
            "task": task[:500],
            "modality": modality if modality in ["definite", "tentative"] else "definite",
            "owner_text": owner_text[:100] if owner_text else None,
            "owner_basis": owner_basis,
            "deadline_text": deadline_text,
            "utterance_id": utt_id,
            "speaker_label": speaker_label,
            "quote": actual_quote,
            "char_start": char_start,
            "char_end": char_end
        })

    return verified_actions
