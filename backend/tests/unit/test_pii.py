import pytest
from app.utils.pii import redact_pii

def test_redact_phone_numbers():
    text1 = "Call me back at 9876543210 please."
    assert redact_pii(text1) == "Call me back at [REDACTED_PHONE] please."

    text2 = "My US number is 555-123-4567 or (555) 123-4567."
    res2 = redact_pii(text2)
    assert "[REDACTED_PHONE]" in res2
    assert "555-123-4567" not in res2

def test_redact_email_addresses():
    text = "Send the proposal to john.doe@example.com by EOD."
    assert redact_pii(text) == "Send the proposal to [REDACTED_EMAIL] by EOD."

def test_redact_credit_cards():
    text = "Card number 4111 2222 3333 4444 was provided."
    assert redact_pii(text) == "Card number [REDACTED_CARD] was provided."

def test_redact_clean_text_unchanged():
    text = "Hello, we are talking about enterprise wholesale ordering platforms."
    assert redact_pii(text) == text
