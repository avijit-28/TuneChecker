import json
from pathlib import Path
from typing import Optional
from app.audio.ffmpeg import run_ffmpeg, probe_audio
from app.utils.errors import AppError

def get_channel_count(file_path: Path) -> int:
    """Returns number of audio channels in the primary audio stream."""
    try:
        data = probe_audio(file_path)
        for s in data.get("streams", []):
            if s.get("codec_name"):
                return int(s.get("channels", 1))
    except Exception:
        pass
    return 1

def split_stereo_channels(input_path: Path, left_wav: Path, right_wav: Path) -> bool:
    """
    Splits a stereo (2-channel) audio file into two separate 16kHz mono WAV files.
    Channel 0 (Left): Sales Representative
    Channel 1 (Right): Customer
    """
    args = [
        "-y",
        "-i", str(input_path),
        "-filter_complex", "[0:a]channelsplit=channel_layout=stereo[left][right]",
        "-map", "[left]",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(left_wav),
        "-map", "[right]",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(right_wav)
    ]
    proc = run_ffmpeg(args, timeout=60)
    return proc.returncode == 0 and left_wav.exists() and right_wav.exists()
