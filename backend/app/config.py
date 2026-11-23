import os
import shutil
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

def resolve_binary(name: str) -> str:
    # If it's already an existing executable path, return it
    if os.path.isfile(name):
        return name
    found = shutil.which(name)
    if found:
        return found
    # Check WinGet Gyan ffmpeg default install location on Windows
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        base_winget = os.path.join(
            local_app_data,
            "Microsoft", "WinGet", "Packages",
            "Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe",
            "ffmpeg-9.0.2-essentials_build", "bin"
        )
        winget_path = os.path.join(base_winget, f"{name}.exe" if not name.endswith(".exe") else name)
        if os.path.isfile(winget_path):
            return winget_path
    return name

class Settings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    LOG_PROMPTS: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/app.db"
    
    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_LOCAL_PATH: str = "./data/audio"
    
    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 50
    MIN_DURATION_SEC: int = 10
    MAX_DURATION_SEC: int = 1800
    
    # Audio tools
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    
    @field_validator("FFMPEG_PATH", mode="after")
    @classmethod
    def validate_ffmpeg(cls, v: str) -> str:
        return resolve_binary(v)

    @field_validator("FFPROBE_PATH", mode="after")
    @classmethod
    def validate_ffprobe(cls, v: str) -> str:
        return resolve_binary(v)

    # STT Settings (Zero-Cost Local Faster-Whisper)
    STT_PROVIDER: str = "faster_whisper"
    WHISPER_MODEL: str = "large-v3-turbo"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_LANGUAGE: Optional[str] = None
    WHISPER_NO_SPEECH_THRESHOLD: float = 0.85
    WHISPER_LOG_PROB_THRESHOLD: float = -2.5
    WHISPER_CONDITION_ON_PREVIOUS_TEXT: bool = False
    WHISPER_BEAM_SIZE: int = 5
    WHISPER_INITIAL_PROMPT: Optional[str] = "Customer sales call, product orders, quantities, pricing, delivery, Hindi and English conversation."
    
    # LLM Settings (Zero-Cost Local Ollama)
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    LLM_MODEL: str = "qwen2.5:1.5b-instruct"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_OUTPUT_TOKENS: int = 4096
    LLM_TIMEOUT_SEC: int = 90
    
    # Queue / Job worker settings
    MAX_CONCURRENT_JOBS: int = 1
    JOB_MAX_ATTEMPTS: int = 3
    JOB_STALE_AFTER_SEC: int = 300
    
    # Privacy / Retention
    AUDIO_RETENTION_DAYS: int = 30
    RATE_LIMIT_UPLOADS_PER_HOUR: int = 20
    DAILY_ANALYSIS_LIMIT: int = 50
    
    # Security / CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    HUGGINGFACE_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
