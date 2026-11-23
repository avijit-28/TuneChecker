from typing import Optional

def find_quote_offsets(utterance_text: str, quote: str) -> Optional[tuple[int, int]]:
    """
    Finds the exact verbatim character start and end offsets of a quote within an utterance.
    Matches with whitespace stripping; returns (char_start, char_end) where
    utterance_text[char_start:char_end] == quote.
    Returns None if quote is not found verbatim in utterance_text.
    """
    if not quote or not utterance_text:
        return None

    clean_quote = quote.strip()
    idx = utterance_text.find(clean_quote)
    if idx != -1:
        return (idx, idx + len(clean_quote))

    # Case where quotation marks or slight punctuation around the quote exist
    unquoted = clean_quote.strip('"\'')
    if unquoted and unquoted != clean_quote:
        idx = utterance_text.find(unquoted)
        if idx != -1:
            return (idx, idx + len(unquoted))

    return None

def verify_evidence_quote(utterance_text: str, quote: str, char_start: int, char_end: int) -> bool:
    """Verifies that utterance_text[char_start:char_end] == quote."""
    if char_start < 0 or char_end > len(utterance_text) or char_start >= char_end:
        return False
    return utterance_text[char_start:char_end] == quote
