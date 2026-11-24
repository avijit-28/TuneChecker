"""
conftest.py for E2E test suite.
Prevents background worker thread processing during API endpoint testing
from executing unmocked pipeline runs during test tear-down.
"""
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_background_pipeline_tasks():
    with patch("app.api.v1.calls.queue_call_processing") as mock_queue:
        yield mock_queue
