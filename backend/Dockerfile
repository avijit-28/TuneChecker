FROM python:3.11-slim

# Install FFmpeg for audio normalization and acoustic prosody analysis
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (required by Hugging Face Spaces UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH="/home/user/.local/bin:$PATH" \
    HF_HOME="/home/user/.cache/huggingface" \
    PYTHONUNBUFFERED=1

WORKDIR /home/user/app

COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user:user . .

RUN mkdir -p /home/user/app/data/audio /home/user/.cache/huggingface

# Default cloud env overrides (override via HF Spaces Secrets/Variables)
ENV LLM_PROVIDER=gemini \
    LLM_FALLBACK_PROVIDER=gemini \
    WHISPER_MODEL=large-v3-turbo \
    WHISPER_DEVICE=cpu \
    WHISPER_COMPUTE_TYPE=int8 \
    WHISPER_BEAM_SIZE=1 \
    CORS_ORIGINS="*"

EXPOSE 7860

CMD ["sh", "-c", "python create_tables.py && uvicorn app.main:app --host 0.0.0.0 --port 7860"]
