"""
Synthetic audio headers, byte streams, and in-memory audio generators for isolated testing.
"""
import io
import math
import struct
import wave
from pathlib import Path

# Authoritative Audio Container Magic Headers
M4A_VALID_HEADER = b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00"
MP4_VALID_HEADER = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00"
WAV_VALID_HEADER = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00"
MP3_ID3_HEADER = b"ID3\x03\x00\x00\x00\x00\x00#TCON"
MP3_SYNC_HEADER = b"\xff\xfb\x90d\x00\x00\x00\x00\x00\x00\x00\x00"
MPEG_PACK_HEADER = b"\x00\x00\x01\xba\x44\x00\x04\x00"

# Corrupted and Invalid Headers
CORRUPTED_TRUNCATED_HEADER = b"\x00\x00"
CORRUPTED_RANDOM_BYTES = b"\xde\xad\xbe\xef\x01\x02\x03\x04\x05\x06\x07\x08"
INVALID_PDF_HEADER = b"%PDF-1.7\r\n"
INVALID_TEXT_HEADER = b"Plain text file header not audio"

def generate_synthetic_wav_bytes(
    duration_sec: float = 1.0,
    sample_rate: int = 16000,
    num_channels: int = 1,
    frequency_hz: float = 440.0,
    amplitude: float = 0.5
) -> bytes:
    """
    Generates a valid PCM WAV byte string in-memory without external dependencies.
    If frequency_hz is 0 or amplitude is 0, generates digital silence.
    """
    total_frames = int(duration_sec * sample_rate)
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(2)  # 16-bit PCM
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(total_frames):
            if amplitude == 0.0 or frequency_hz == 0.0:
                sample_val = 0
            else:
                t = float(i) / sample_rate
                sample_val = int(amplitude * 32767.0 * math.sin(2.0 * math.pi * frequency_hz * t))
                sample_val = max(-32768, min(32767, sample_val))

            sample_bytes = struct.pack("<h", sample_val)
            for _ in range(num_channels):
                frames.extend(sample_bytes)

        wav_file.writeframes(frames)

    return buffer.getvalue()

def create_synthetic_wav_file(
    file_path: Path,
    duration_sec: float = 1.0,
    sample_rate: int = 16000,
    frequency_hz: float = 440.0
) -> Path:
    """Writes a synthetic PCM WAV file to the specified disk path."""
    data = generate_synthetic_wav_bytes(
        duration_sec=duration_sec,
        sample_rate=sample_rate,
        frequency_hz=frequency_hz
    )
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(data)
    return file_path
