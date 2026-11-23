from typing import Any
from app.pipeline.safeguards.quote_matcher import find_quote_offsets

def evaluate_action_items(
    candidate_actions: list[dict[str, Any]],
    utterances: list[dict[str, Any]],
    action_settings: dict[str, Any]
) -> list[dict[str, Any]]:
    utt_map = {u["id"]: u for u in utterances}
    verified_actions = []

    types_config = action_settings.get("types", {})
    include_tentative = action_settings.get("include_tentative", False)
    owner_rule = action_settings.get("owner_rule", "explicit_or_committing_speaker")

    for idx, act in enumerate(candidate_actions):
        utt_id = act.get("utterance_id")
        task = act.get("task", "").strip()
        act_type = act.get("type", "commitment")
        modality = act.get("modality", "definite").lower()
        quote = act.get("quote", "").strip()
        owner_text = act.get("owner_text")
        deadline_text = act.get("deadline_text")

        if not utt_id or utt_id not in utt_map:
            continue
        if not task or not quote:
            continue

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

        # Verify quote verbatim in utterance
        target_text = utt_map[utt_id]["text"]
        offsets = find_quote_offsets(target_text, quote)
        if not offsets:
            continue

        char_start, char_end = offsets
        speaker_label = utt_map[utt_id]["speaker_label"]

        # Check owner basis
        owner_basis = act.get("owner_basis", "none")
        if owner_basis not in ["explicit_name", "explicit_role", "committing_speaker", "none"]:
            owner_basis = "committing_speaker" if owner_text else "none"

        # Apply owner_rule: explicit_only strips non-explicit owners
        if owner_rule == "explicit_only" and owner_basis == "committing_speaker":
            owner_text = None
            owner_basis = "none"

        if not owner_text:
            owner_basis = "none"

        # Deadline verification: clean up or leave None
        if deadline_text:
            deadline_text = deadline_text.strip()
            if not deadline_text or len(deadline_text) > 120:
                deadline_text = None

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
            "quote": target_text[char_start:char_end],
            "char_start": char_start,
            "char_end": char_end
        })

    return verified_actions
