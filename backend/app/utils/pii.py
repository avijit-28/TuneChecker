import re
from typing import Optional

# Regex patterns for sensitive PII in call transcripts
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
PHONE_PATTERN = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b(?:\+91[-.\s]?)?[6-9]\d{9}\b')
CARD_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')

def redact_pii(text: str, mask_phone: bool = True, mask_email: bool = True, mask_card: bool = True) -> str:
    """
    Sanitizes transcript text by masking emails, phone numbers, and credit cards.
    """
    if not text:
        return text

    sanitized = text
    if mask_card:
        sanitized = CARD_PATTERN.sub("[REDACTED_CARD]", sanitized)
    if mask_email:
        sanitized = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", sanitized)
    if mask_phone:
        sanitized = PHONE_PATTERN.sub("[REDACTED_PHONE]", sanitized)

    return sanitized
