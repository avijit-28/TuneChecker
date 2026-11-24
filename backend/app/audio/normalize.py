import tempfile
from pathlib import Path
from app.audio.ffmpeg import run_ffmpeg
from app.utils.errors import AppError

def normalize_to_wav(input_path: Path, output_wav_path: Path) -> Path:
    """
    Normalizes input audio to 16 kHz mono 16-bit PCM WAV.
    Applies FFmpeg Dynamic Audio Normalizer (dynaudnorm) to dynamically amplify
    soft/muffled telephone respondent speech while keeping loud speaker clear.
    """
    args = [
        "-y",
        "-i", str(input_path),
        "-af", "dynaudnorm=p=0.9:m=10:s=12:g=15",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(output_wav_path)
    ]
    proc = run_ffmpeg(args, timeout=60)
    if proc.returncode != 0:
        raise AppError("AUDIO_CORRUPTED", "Failed to normalize audio to 16kHz mono WAV.", details={"stderr": proc.stderr[:200]})
    return output_wav_path
