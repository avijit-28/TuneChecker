from pathlib import Path
from typing import Any
from app.audio.ffmpeg import probe_audio, test_decode, check_silence
from app.config import settings
from app.utils.errors import AppError

def validate_audio_file(file_path: Path) -> dict[str, Any]:
    if not file_path.is_file() or file_path.stat().st_size == 0:
        raise AppError("FILE_EMPTY", "Audio file is empty or missing on disk.", 422)

    # 1. Probe audio
    probe_data = probe_audio(file_path)
    streams = probe_data.get("streams", [])
    audio_streams = [s for s in streams if s.get("codec_name")]
    if not audio_streams:
        raise AppError("AUDIO_UNREADABLE", "File contains no valid audio streams.", 422)

    # 2. Extract duration
    format_info = probe_data.get("format", {})
    raw_duration = format_info.get("duration")
    if not raw_duration:
        raise AppError("AUDIO_UNREADABLE", "Could not determine audio duration.", 422)

    try:
        duration_sec = float(raw_duration)
    except ValueError:
        raise AppError("AUDIO_UNREADABLE", f"Invalid duration value '{raw_duration}'.", 422)

    duration_ms = int(duration_sec * 1000)

    # 3. Check duration limits (10s to 1800s)
    if duration_sec < settings.MIN_DURATION_SEC:
        raise AppError(
            "DURATION_OUT_OF_RANGE",
            f"Audio duration ({duration_sec:.1f}s) is shorter than minimum allowed ({settings.MIN_DURATION_SEC}s).",
            422,
            details={"duration_sec": duration_sec, "min_sec": settings.MIN_DURATION_SEC}
        )
    if duration_sec > settings.MAX_DURATION_SEC:
        raise AppError(
            "DURATION_OUT_OF_RANGE",
            f"Audio duration ({duration_sec:.1f}s) exceeds maximum allowed ({settings.MAX_DURATION_SEC}s).",
            422,
            details={"duration_sec": duration_sec, "max_sec": settings.MAX_DURATION_SEC}
        )

    # 4. Decode test
    if not test_decode(file_path):
        raise AppError("AUDIO_CORRUPTED", "Audio stream contains corrupt bitstream data.", 422)

    # 5. Silence check
    if check_silence(file_path):
        raise AppError("AUDIO_SILENT", "Audio recording is completely silent.", 422)

    stream = audio_streams[0]
    return {
        "duration_ms": duration_ms,
        "duration_sec": duration_sec,
        "codec": stream.get("codec_name"),
        "channels": stream.get("channels"),
        "sample_rate": stream.get("sample_rate"),
    }
