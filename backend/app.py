import os
import uvicorn

# Configure cloud defaults for Hugging Face Spaces (Gradio SDK, Free CPU Basic)
os.environ.setdefault("LLM_PROVIDER", "gemini")
os.environ.setdefault("LLM_FALLBACK_PROVIDER", "gemini")
os.environ.setdefault("WHISPER_MODEL", "large-v3-turbo")
os.environ.setdefault("WHISPER_DEVICE", "cpu")
os.environ.setdefault("WHISPER_COMPUTE_TYPE", "int8")
os.environ.setdefault("WHISPER_BEAM_SIZE", "1")
os.environ.setdefault("CORS_ORIGINS", "*")

import create_tables  # noqa: E402, F401
from app.main import app  # noqa: E402


@app.get("/")
def root_health():
    """Root health endpoint for Hugging Face Spaces readiness probe."""
    return {"status": "ok", "service": "TuneChecker API"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port)
