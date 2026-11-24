from pathlib import Path
from unittest.mock import patch
import pytest

from app.audio.upload_checks import (
    validate_filename_and_mime,
    validate_ftyp_box,
    validate_audio_container,
)
from app.audio.validation import validate_audio_file
from app.utils.errors import AppError


def test_filename_and_mime_validation_valid():
    assert validate_filename_and_mime("test_call.m4a", "audio/mp4") == "test_call.m4a"
    assert validate_filename_and_mime("call.mp4", "video/mp4") == "call.mp4"
    assert validate_filename_and_mime("call.mp3", "audio/mpeg") == "call.mp3"
    assert validate_filename_and_mime("recording.wav", "audio/wav") == "recording.wav"
    assert validate_filename_and_mime("meeting.mpeg", "video/mpeg") == "meeting.mpeg"
    assert validate_filename_and_mime("voice.mpg", "audio/mpeg") == "voice.mpg"
    assert validate_filename_and_mime("path/to/nested\\call.M4A", "audio/x-m4a") == "call.M4A"


def test_filename_validation_invalid_extension():
    with pytest.raises(AppError) as exc_info:
        validate_filename_and_mime("document.pdf", "application/pdf")
    assert exc_info.value.code == "INVALID_FILE_TYPE"
    assert exc_info.value.status_code == 415

    with pytest.raises(AppError) as exc_info:
        validate_filename_and_mime("audio.flac", "audio/flac")
    assert exc_info.value.code == "INVALID_FILE_TYPE"


def test_filename_validation_empty():
    with pytest.raises(AppError) as exc_info:
        validate_filename_and_mime("", "audio/mp4")
    assert exc_info.value.code == "FILE_EMPTY"


def test_audio_container_verification():
    # Valid M4A & MP4
    m4a_header = b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00"
    mp4_header = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00"
    assert validate_audio_container(m4a_header, "call.m4a") is True
    assert validate_audio_container(mp4_header, "call.mp4") is True
    assert validate_audio_container(b"RIFF\x24\x08\x00\x00WAVEfmt ", "call.m4a") is False
    assert validate_audio_container(b"RIFF\x24\x08\x00\x00WAVEfmt ", "call.mp4") is False

    # Valid WAV
    wav_header = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00"
    assert validate_audio_container(wav_header, "call.wav") is True
    assert validate_audio_container(m4a_header, "call.wav") is False

    # Valid MP3 / MPEG
    mp3_id3 = b"ID3\x03\x00\x00\x00\x00\x00#"
    assert validate_audio_container(mp3_id3, "call.mp3") is True
    assert validate_audio_container(mp3_id3, "call.mpeg") is True
    mpeg_ps = b"\x00\x00\x01\xba\x44\x00\x04\x00"
    assert validate_audio_container(mpeg_ps, "video.mpg") is True
    mp3_sync = b"\xff\xfb\x90d\x00\x00\x00\x00"
    assert validate_audio_container(mp3_sync, "call.mp3") is True

    # Truncated header
    assert validate_audio_container(b"\x00", "call.m4a") is False


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
    candidates = [
        Path(__file__).resolve().parents[3] / "samples" / "red_call_01.m4a",
        Path("../samples/red_call_01.m4a"),
        Path("samples/red_call_01.m4a"),
    ]
    sample_path = next((p for p in candidates if p.exists()), None)
    if not sample_path:
        pytest.skip("Sample red_call_01.m4a not found")

    result = validate_audio_file(sample_path)
    assert result["duration_sec"] > 50.0
    assert result["duration_ms"] > 50000
    assert result["channels"] == 1
    assert result["codec"] == "aac"
