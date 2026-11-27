import tempfile
from pathlib import Path
from app.audio.ffmpeg import run_ffmpeg
from app.utils.errors import AppError

def try_repair_audio(input_path: Path, repaired_path: Path) -> bool:
    """Attempts lossless container/moov repair on truncated or stream-corrupted audio files."""
    args = [
        "-y",
        "-err_detect", "ignore_err",
        "-i", str(input_path),
        "-c", "copy",
        "-movflags", "faststart",
        str(repaired_path)
    ]
    proc = run_ffmpeg(args, timeout=30)
    return proc.returncode == 0 and repaired_path.exists() and repaired_path.stat().st_size > 0

def normalize_to_wav(input_path: Path, output_wav_path: Path) -> Path:
    """
    Normalizes input audio to 16 kHz mono 16-bit PCM WAV without destructive
    spectral filtering or dynamic compression, preserving full vocal energy
    for Silero VAD and Faster-Whisper.
    Includes automated container repair fallback for truncated or damaged headers.
    """
    args = [
        "-y",
        "-i", str(input_path),
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(output_wav_path)
    ]
    proc = run_ffmpeg(args, timeout=60)
    if proc.returncode != 0:
        # Attempt container auto-repair before failing
        with tempfile.NamedTemporaryFile(suffix=input_path.suffix, delete=False) as tmp_repair:
            repair_path = Path(tmp_repair.name)
        try:
            if try_repair_audio(input_path, repair_path):
                repair_args = [
                    "-y",
                    "-i", str(repair_path),
                    "-ar", "16000",
                    "-ac", "1",
                    "-c:a", "pcm_s16le",
                    str(output_wav_path)
                ]
                proc2 = run_ffmpeg(repair_args, timeout=60)
                if proc2.returncode == 0:
                    return output_wav_path
        finally:
            if repair_path.exists():
                try:
                    repair_path.unlink()
                except Exception:
                    pass

        raise AppError("AUDIO_CORRUPTED", "Failed to normalize audio to 16kHz mono WAV.", details={"stderr": proc.stderr[:200]})
    return output_wav_path
