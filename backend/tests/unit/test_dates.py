import pytest
from datetime import datetime
from app.utils.dates import normalize_relative_deadline

def test_normalize_tomorrow():
    ref = datetime(2026, 11, 26, 10, 0, 0)
    norm = normalize_relative_deadline("tomorrow", reference_date=ref)
    assert "2026-11-27" in norm

def test_normalize_today():
    ref = datetime(2026, 11, 26, 10, 0, 0)
    norm = normalize_relative_deadline("this afternoon", reference_date=ref)
    assert "2026-11-26" in norm

def test_normalize_next_week():
    ref = datetime(2026, 11, 26, 10, 0, 0)
    norm = normalize_relative_deadline("next week", reference_date=ref)
    assert "2026-12-03" in norm

def test_normalize_none_or_empty():
    assert normalize_relative_deadline(None) is None
    assert normalize_relative_deadline("") is None
