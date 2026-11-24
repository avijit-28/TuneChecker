import re
from typing import Optional

def find_quote_offsets(utterance_text: str, quote: str) -> Optional[tuple[int, int]]:
    """
    Finds character start and end offsets of a quote within an utterance.
    Supports:
    1. Exact verbatim match.
    2. Punctuation/whitespace-stripped match.
    3. Case-insensitive match.
    4. Subsequence word-level fuzzy match (ignores filler words like 'uh', 'um', stutter).
    """
    if not quote or not utterance_text:
        return None

    clean_quote = quote.strip()
    if not clean_quote:
        return None

    # 1. Exact match
    idx = utterance_text.find(clean_quote)
    if idx != -1:
        return (idx, idx + len(clean_quote))

    # 2. Stripped quotes/punctuation
    unquoted = clean_quote.strip('"\'.,!?;: ')
    if unquoted and unquoted != clean_quote:
        idx = utterance_text.find(unquoted)
        if idx != -1:
            return (idx, idx + len(unquoted))

    # 3. Case-insensitive match
    lower_utt = utterance_text.lower()
    lower_quote = clean_quote.lower()
    idx = lower_utt.find(lower_quote)
    if idx != -1:
        return (idx, idx + len(clean_quote))

    lower_unquoted = unquoted.lower() if unquoted else ""
    if lower_unquoted:
        idx = lower_utt.find(lower_unquoted)
        if idx != -1:
            return (idx, idx + len(lower_unquoted))

    # 4. Word-level subsequence match
    # Extract significant words (ignoring filler 'uh', 'um', punctuation)
    quote_words = [w.lower() for w in re.findall(r'\b[A-Za-z0-9\$\.\-]+\b', clean_quote) if w.lower() not in ('uh', 'um', 'ah')]
    if len(quote_words) >= 2:
        # Build regex that matches the first word, anything in between, and the last word
        first_w = re.escape(quote_words[0])
        last_w = re.escape(quote_words[-1])
        pattern = re.compile(rf'\b{first_w}\b.*?\b{last_w}\b', re.IGNORECASE | re.DOTALL)
        match = pattern.search(utterance_text)
        if match:
            return (match.start(), match.end())

    return None

def verify_evidence_quote(utterance_text: str, quote: str, char_start: int, char_end: int) -> bool:
    """Verifies that char_start and char_end form a valid non-empty span within utterance_text."""
    if char_start < 0 or char_end > len(utterance_text) or char_start >= char_end:
        return False
    return len(utterance_text[char_start:char_end].strip()) > 0
