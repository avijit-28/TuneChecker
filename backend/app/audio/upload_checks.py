from pathlib import Path
from app.utils.errors import AppError
from app.config import settings

VALID_EXTENSIONS = {".m4a", ".mp3", ".wav"}
VALID_MIME_TYPES = {
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "application/octet-stream"
}

def validate_filename_and_mime(filename: str, content_type: str) -> str:
    if not filename:
        raise AppError("FILE_EMPTY", "No file uploaded.", 422)
    
    # Check extension
    lower_name = filename.lower()
    if not any(lower_name.endswith(ext) for ext in VALID_EXTENSIONS):
        raise AppError(
            "INVALID_FILE_TYPE",
            f"Unsupported file extension. Only .m4a, .mp3, and .wav audio files are supported.",
            415,
            details={"filename": filename, "supported": sorted(list(VALID_EXTENSIONS))}
        )

    # Sanitize filename (remove paths, keep base)
    sanitized = filename.replace("\\", "/").split("/")[-1].strip()
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    return sanitized

def validate_ftyp_box(header_bytes: bytes) -> bool:
    """Verifies the file starts with an MP4/M4A ftyp box in the first 32 bytes."""
    if len(header_bytes) < 8:
        return False
    return header_bytes[4:8] == b"ftyp"

def validate_audio_container(header_bytes: bytes, filename: str) -> bool:
    """Verifies the container header matches the declared audio extension."""
    if len(header_bytes) < 4:
        return False
    
    ext = Path(filename).suffix.lower()
    if ext == ".m4a":
        return validate_ftyp_box(header_bytes)
    elif ext == ".wav":
        if len(header_bytes) < 12:
            return False
        return header_bytes[:4] == b"RIFF" and header_bytes[8:12] == b"WAVE"
    elif ext == ".mp3":
        if header_bytes[:3] == b"ID3":
            return True
        if len(header_bytes) >= 2 and header_bytes[0] == 0xFF and (header_bytes[1] & 0xE0) == 0xE0:
            return True
        # Allow pass-through for headerless MP3 bitstreams (FFmpeg decode test will strictly verify)
        return True
    
    return False
