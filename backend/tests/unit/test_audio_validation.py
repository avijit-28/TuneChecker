from pathlib import Path
from unittest.mock import patch
import pytest

from app.audio.upload_checks import (
    validate_filename_and_mime,
    validate_ftyp_box,
)
from app.audio.validation import validate_audio_file
from app.utils.errors import AppError


def test_filename_and_mime_validation_valid():
    sanitized = validate_filename_and_mime("test_call.m4a", "audio/mp4")
    assert sanitized == "test_call.m4a"

    sanitized = validate_filename_and_mime("path/to/nested\\call.M4A", "audio/x-m4a")
    assert sanitized == "call.M4A"


def test_filename_validation_invalid_extension():
    with pytest.raises(AppError) as exc_info:
        validate_filename_and_mime("audio.mp3", "audio/mpeg")
    assert exc_info.value.code == "INVALID_FILE_TYPE"
    assert exc_info.value.status_code == 415

    with pytest.raises(AppError) as exc_info:
        validate_filename_and_mime("recording.wav", "audio/wav")
    assert exc_info.value.code == "INVALID_FILE_TYPE"


def test_filename_validation_empty():
    with pytest.raises(AppError) as exc_info:
        validate_filename_and_mime("", "audio/mp4")
    assert exc_info.value.code == "FILE_EMPTY"


def test_ftyp_box_verification():
    # Valid MP4 header: 4-byte size followed by 'ftyp'
    valid_header = b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00"
    assert validate_ftyp_box(valid_header) is True

    # Invalid header (WAV/RIFF)
    wav_header = b"RIFF\x24\x08\x00\x00WAVEfmt "
    assert validate_ftyp_box(wav_header) is False

    # Short/truncated header
    assert validate_ftyp_box(b"\x00\x00\x00") is False
    assert validate_ftyp_box(b"") is False


def test_validate_audio_file_empty_or_missing(tmp_path: Path):
    missing_file = tmp_path / "missing.m4a"
    with pytest.raises(AppError) as exc_info:
        validate_audio_file(missing_file)
    assert exc_info.value.code == "FILE_EMPTY"

    empty_file = tmp_path / "empty.m4a"
    empty_file.write_bytes(b"")
    with pytest.raises(AppError) as exc_info:
        validate_audio_file(empty_file)
    assert exc_info.value.code == "FILE_EMPTY"


def test_validate_audio_file_duration_bounds(tmp_path: Path):
    dummy_file = tmp_path / "dummy.m4a"
    dummy_file.write_bytes(b"non-empty")

    # Duration too short (< 10s)
    short_probe = {
        "streams": [{"codec_name": "aac", "channels": 1, "sample_rate": "16000"}],
        "format": {"duration": "5.4"},
    }
    with patch("app.audio.validation.probe_audio", return_value=short_probe):
        with pytest.raises(AppError) as exc_info:
            validate_audio_file(dummy_file)
        assert exc_info.value.code == "DURATION_OUT_OF_RANGE"
        assert exc_info.value.details["duration_sec"] == 5.4

    # Duration too long (> 1800s)
    long_probe = {
        "streams": [{"codec_name": "aac", "channels": 1, "sample_rate": "16000"}],
        "format": {"duration": "1801.0"},
    }
    with patch("app.audio.validation.probe_audio", return_value=long_probe):
        with pytest.raises(AppError) as exc_info:
            validate_audio_file(dummy_file)
        assert exc_info.value.code == "DURATION_OUT_OF_RANGE"


def test_validate_audio_file_corrupted(tmp_path: Path):
    dummy_file = tmp_path / "corrupt.m4a"
    dummy_file.write_bytes(b"corrupt-data")

    probe_ok = {
        "streams": [{"codec_name": "aac", "channels": 1, "sample_rate": "16000"}],
        "format": {"duration": "60.0"},
    }
    with patch("app.audio.validation.probe_audio", return_value=probe_ok):
        with patch("app.audio.validation.test_decode", return_value=False):
            with pytest.raises(AppError) as exc_info:
                validate_audio_file(dummy_file)
            assert exc_info.value.code == "AUDIO_CORRUPTED"


def test_validate_audio_file_silent(tmp_path: Path):
    dummy_file = tmp_path / "silent.m4a"
    dummy_file.write_bytes(b"silent-data")

    probe_ok = {
        "streams": [{"codec_name": "aac", "channels": 1, "sample_rate": "16000"}],
        "format": {"duration": "60.0"},
    }
    with patch("app.audio.validation.probe_audio", return_value=probe_ok):
        with patch("app.audio.validation.test_decode", return_value=True):
            with patch("app.audio.validation.check_silence", return_value=True):
                with pytest.raises(AppError) as exc_info:
                    validate_audio_file(dummy_file)
                assert exc_info.value.code == "AUDIO_SILENT"


def test_validate_audio_file_real_sample():
    sample_path = Path("../samples/red_call_01.m4a")
    if not sample_path.exists():
        sample_path = Path("samples/red_call_01.m4a")
    if not sample_path.exists():
        pytest.skip("Sample red_call_01.m4a not found")

    result = validate_audio_file(sample_path)
    assert result["duration_sec"] > 50.0
    assert result["duration_ms"] > 50000
    assert result["channels"] == 1
    assert result["codec"] == "aac"
