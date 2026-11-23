from app.utils.errors import AppError
from app.config import settings

VALID_EXTENSIONS = {".m4a"}
VALID_MIME_TYPES = {
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
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
            f"Unsupported file extension. Only .m4a files are supported.",
            415,
            details={"filename": filename}
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
    # Standard MP4 box header: 4 bytes size, 4 bytes type 'ftyp'
    return header_bytes[4:8] == b"ftyp"
