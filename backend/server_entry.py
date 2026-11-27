import os
import threading
import gradio as gr

# Configure cloud defaults for Hugging Face Spaces (Gradio SDK, ZeroGPU Free)
os.environ.setdefault("LLM_PROVIDER", "gemini")
os.environ.setdefault("LLM_FALLBACK_PROVIDER", "gemini")
os.environ.setdefault("WHISPER_MODEL", "large-v3-turbo")
os.environ.setdefault("WHISPER_DEVICE", "cpu")
os.environ.setdefault("WHISPER_COMPUTE_TYPE", "int8")
os.environ.setdefault("WHISPER_BEAM_SIZE", "1")
os.environ.setdefault("CORS_ORIGINS", "*")

import create_tables  # noqa: E402, F401
from fastapi.exceptions import RequestValidationError  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402
from app.api.v1.router import api_router  # noqa: E402
from app.utils.errors import (  # noqa: E402
    AppError,
    app_error_handler,
    validation_error_handler,
    http_error_handler,
    generic_error_handler,
)

try:
    import spaces

    @spaces.GPU
    def _zerogpu_ping():
        return "TuneChecker ZeroGPU Ready"
except Exception:
    def _zerogpu_ping():
        return "TuneChecker CPU Ready"


with gr.Blocks(title="TuneChecker API") as demo:
    gr.Markdown("# TuneChecker Sales Call Quality Auditor API")
    gr.Markdown("API Base: `/api/v1` · Health: `/api/v1/health`")
    btn = gr.Button("Check Runtime")
    out = gr.Textbox(label="Status")
    btn.click(_zerogpu_ping, outputs=out)


if __name__ == "__main__":
    # Let Gradio bind the exact port expected by Hugging Face ZeroGPU
    demo.launch(server_name="0.0.0.0", prevent_thread_lock=True)

    # Attach TuneChecker FastAPI routes & handlers directly to Gradio's FastAPI app
    fastapi_app = demo.app
    fastapi_app.add_exception_handler(AppError, app_error_handler)
    fastapi_app.add_exception_handler(RequestValidationError, validation_error_handler)
    fastapi_app.add_exception_handler(StarletteHTTPException, http_error_handler)
    fastapi_app.add_exception_handler(Exception, generic_error_handler)
    fastapi_app.include_router(api_router, prefix="/api/v1")

    threading.Event().wait()
