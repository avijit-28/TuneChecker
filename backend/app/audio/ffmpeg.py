import json
import subprocess
from pathlib import Path
from typing import Any
from app.config import settings
from app.utils.errors import AppError

def run_ffprobe(args: list[str], timeout: int = 15) -> subprocess.CompletedProcess:
    cmd = [settings.FFPROBE_PATH] + args
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout
    )

def run_ffmpeg(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    cmd = [settings.FFMPEG_PATH] + args
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout
    )

def probe_audio(file_path: Path) -> dict[str, Any]:
    args = [
        "-v", "error",
        "-show_entries", "format=duration,format_name,size,bit_rate:stream=codec_name,channels,sample_rate",
        "-of", "json",
        str(file_path)
    ]
    try:
        proc = run_ffprobe(args, timeout=15)
        if proc.returncode != 0:
            raise AppError("AUDIO_UNREADABLE", "Could not probe audio file headers.", 422, details={"stderr": proc.stderr[:200]})
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        raise AppError("AUDIO_UNREADABLE", "Timeout while probing audio file.", 422)
    except json.JSONDecodeError:
        raise AppError("AUDIO_UNREADABLE", "Failed to parse audio probe output.", 422)

def test_decode(file_path: Path) -> bool:
    """Decodes the entire file into null to catch bitstream corruption."""
    args = [
        "-v", "error",
        "-i", str(file_path),
        "-f", "null",
        "-"
    ]
    try:
        proc = run_ffmpeg(args, timeout=30)
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        return False

def check_silence(file_path: Path) -> bool:
    """Checks if audio is purely silent using volumedetect filter."""
    args = [
        "-i", str(file_path),
        "-af", "volumedetect",
        "-f", "null",
        "-"
    ]
    try:
        proc = run_ffmpeg(args, timeout=30)
        output = proc.stderr
        # Check max_volume
        for line in output.splitlines():
            if "max_volume:" in line:
                val = line.split("max_volume:")[1].strip().split()[0]
                try:
                    vol_db = float(val)
                    if vol_db <= -70.0:  # practically complete digital silence
                        return True
                except ValueError:
                    pass
        return False
    except Exception:
        return False
