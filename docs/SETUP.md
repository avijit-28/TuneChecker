# SETUP.md — Local Development Setup

> Project: **Sales Call Quality Analysis Agent**  
> Assessment: ScaleWorks AI — Forward Deployed Engineer  
> Target: Windows 10/11, AMD Ryzen 7/9, 8 GB RAM, NVIDIA GPU (exact model/VRAM to be detected)  
> Cost policy: **No paid APIs, subscriptions, or hosted inference.** Models run locally. Initial model downloads require internet access.

## 1. Selected local stack

| Layer | Selection |
|---|---|
| Frontend | React + Vite |
| UI | Bootstrap 5 |
| Backend | Python + FastAPI |
| Database | SQLite + SQLAlchemy |
| Audio conversion | FFmpeg |
| Speech-to-text | Faster-Whisper |
| Speaker diarization | pyannote.audio Community-1 |
| Local LLM | Ollama + `qwen2.5:1.5b-instruct` |
| Tests | Pytest |

This is the approved starting configuration. Confirm package and CUDA compatibility on the target machine before pinning versions. Do not install arbitrary CUDA/cuDNN packages to solve a version mismatch.

## 2. Detect hardware and software

Open PowerShell:

```powershell
python --version
py --version
node --version
npm --version
git --version
nvidia-smi
```

Record the NVIDIA GPU name, driver version, and total VRAM shown by `nvidia-smi`. Do not assume a GPU model or VRAM size. Check Windows RAM in Task Manager → Performance → Memory.

Recommended operating approach for 8 GB system RAM:
- Run one audio-analysis job at a time.
- Start with Whisper `base`.
- Use the small Qwen 1.5B model.
- Process models sequentially rather than keeping every model resident.
- Close memory-heavy applications during inference.
- Keep CPU fallback available.

## 3. Install prerequisites

Install from official sources:
- Python 3.11 (or the version selected and tested by the project).
- Node.js LTS.
- Git for Windows.
- FFmpeg.
- Ollama for Windows.
- Current NVIDIA driver appropriate for the installed GPU.

After installation, open a new PowerShell window and verify:

```powershell
python --version
node --version
npm --version
git --version
ffmpeg -version
nvidia-smi
ollama --version
```

If `ffmpeg` is not recognized, add the directory containing `ffmpeg.exe` to the Windows PATH, reopen PowerShell, and retry.

## 4. Project structure

Use the actual repository structure defined in `ARCHITECTURE.md`. A reasonable starting layout is:

```text
sales-call-quality-agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── storage/
│   └── audio/
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

Do not duplicate or move existing files simply to match this example. The architecture document takes precedence.

## 5. Backend environment

From the repository root:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
```

If PowerShell blocks activation for the current user, use:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate the environment again.

Install the project's pinned dependencies from `requirements.txt`:

```powershell
pip install -r requirements.txt
```

If `requirements.txt` does not exist yet, create it from the approved architecture and test a compatible dependency set before pinning it. Do not install PyTorch, CUDA, or cuDNN versions by guesswork.

### GPU and PyTorch verification

Install the PyTorch build recommended by the official PyTorch installation selector for the installed Windows/NVIDIA driver combination. Then verify:

```powershell
python -c "import torch; print('Torch:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU fallback')"
```

Faster-Whisper uses CTranslate2 and has its own CUDA/cuDNN compatibility requirements. A working PyTorch CUDA check does **not** prove Faster-Whisper or pyannote GPU compatibility. Verify each library independently and retain CPU fallback.

## 6. Install and verify FFmpeg

Verify:

```powershell
ffmpeg -version
ffprobe -version
```

Inspect an uploaded recording:

```powershell
ffprobe -v error -show_format -show_streams ".\sample.m4a"
```

Convert a sample recording to mono 16 kHz WAV for a compatibility test:

```powershell
ffmpeg -i ".\sample.m4a" -ac 1 -ar 16000 ".\sample.wav"
```

Keep the original recording unchanged. Store converted audio as a derived temporary asset and delete it according to the retention policy.

## 7. Faster-Whisper

Install through the project's pinned requirements. Start with model `base`.

GPU example, only after verifying the installed CTranslate2/CUDA/cuDNN compatibility:

```python
from faster_whisper import WhisperModel

model = WhisperModel(
    "base",
    device="cuda",
    compute_type="int8_float16"
)

segments, info = model.transcribe(
    "sample.wav",
    beam_size=3,
    vad_filter=True,
    word_timestamps=True
)

for segment in segments:
    print(segment.start, segment.end, segment.text)
```

CPU fallback:

```python
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)
```

Use `base` as the first test configuration. Only test `small` after measuring RAM/VRAM use. Model size requirements vary by hardware, audio duration, batch settings, and library versions.

## 8. pyannote.audio Community-1

The model requires a Hugging Face account, acceptance of the model's access conditions, and an access token. This is a model-hosting authentication requirement, not a paid inference API.

1. Open the model page: https://huggingface.co/pyannote/speaker-diarization-community-1
2. Sign in and accept the conditions shown on the model page.
3. Create a token with the minimum read permissions required.
4. Put the token in the local `.env` file as `HUGGINGFACE_TOKEN`.
5. Never commit `.env` or print the token in logs.
6. Install the compatible `pyannote.audio` version and follow the model page's current usage instructions.
7. Run a short synthetic or consented audio test.

If access, download, CUDA, or memory errors occur, preserve the transcript and mark speaker attribution as unavailable/uncertain. Do not silently assign the first speaker as the sales representative.

## 9. Ollama and local LLM

Install Ollama for Windows, then:

```powershell
ollama pull qwen2.5:1.5b-instruct
ollama list
ollama run qwen2.5:1.5b-instruct
```

Ollama's local API normally listens at:

```text
http://localhost:11434
```

Verify from PowerShell:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
```

Use the model locally only. Do not configure Ollama Cloud or a hosted inference provider. A 1.5B model is a lightweight starting point, not a guarantee of perfect classification. Validate structured output and ground every result in transcript segments.

## 10. Environment variables

Create `.env` from `.env.example` in the backend directory (or the location specified by the implementation). Example placeholders:

```env
APP_ENV=development
SECRET_KEY=replace_with_a_random_local_secret
DATABASE_URL=sqlite:///./sales_calls.db
HUGGINGFACE_TOKEN=your_read_token
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b-instruct
WHISPER_MODEL=base
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=int8_float16
AUDIO_STORAGE_PATH=../storage/audio
MAX_UPLOAD_SIZE=52428800
```

Adjust names to match the actual settings module. `WHISPER_DEVICE=auto` should only be used if the application implements a tested device-selection routine. Otherwise configure `cuda` or `cpu` explicitly.

Generate a local secret rather than reusing an example value. Do not commit `.env`.

## 11. Database initialization

Use the project's migration tool if configured. If Alembic is present:

```powershell
alembic upgrade head
```

If the project uses SQLAlchemy metadata initialization for the MVP, use the documented application command. Do not run both migration and metadata-creation paths unless the implementation explicitly requires it.

Verify that the SQLite database is created at the configured location and that tables match `DATABASE.md`.

## 12. Frontend setup

Open a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Install only dependencies listed in the committed `package.json`. Configure the frontend API base URL using the project's documented Vite environment variable (for example, `VITE_API_BASE_URL=http://localhost:8000`).

## 13. Start the application

Use separate terminals.

**Terminal 1 — Ollama**  
Start Ollama using the Windows application/service. Confirm `/api/tags` responds.

**Terminal 2 — Backend**

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Adjust `app.main:app` if the actual FastAPI entry point differs.

**Terminal 3 — Frontend**

```powershell
cd frontend
npm run dev
```

Open the URL printed by Vite. FastAPI's Swagger UI is commonly available at `http://127.0.0.1:8000/docs` when enabled.

## 14. Sequential processing policy for 8 GB RAM

Do not keep Whisper, pyannote, and Ollama loaded simultaneously unless memory tests prove this is safe.

Recommended orchestration:
1. Validate and prepare audio.
2. Load Faster-Whisper; transcribe; persist segments.
3. Release transcription resources where possible.
4. Load pyannote; diarize; persist speaker turns.
5. Release diarization resources where possible.
6. Call local Ollama; validate output; persist analysis.
7. Return results to the UI.

Limit concurrency to one analysis job initially. Model unloading and GPU memory release are framework-dependent; verify actual process memory rather than assuming that deleting a Python variable releases all GPU memory.

## 15. Verification checklist

- [ ] Python virtual environment activates.
- [ ] Frontend dependencies install.
- [ ] FastAPI starts.
- [ ] SQLite database initializes.
- [ ] FFmpeg reads an `.m4a` file.
- [ ] Faster-Whisper transcribes a short test file.
- [ ] pyannote model access and diarization work, or uncertainty fallback is verified.
- [ ] Ollama responds locally.
- [ ] Ollama returns valid structured output.
- [ ] End-to-end test completes without paid API credentials.
- [ ] `.env` and audio recordings are excluded from Git.

## 16. Troubleshooting

| Problem | Checks / remedy |
|---|---|
| `ffmpeg` not recognized | Check PATH; reopen terminal; verify `ffmpeg.exe` location. |
| CUDA unavailable in PyTorch | Check `nvidia-smi`, driver, and official PyTorch install selector. |
| Faster-Whisper CUDA error | Check CTranslate2 CUDA/cuDNN compatibility; test CPU `int8`. |
| pyannote access denied | Accept model conditions and verify token permissions. |
| Ollama connection refused | Start Ollama; test `http://localhost:11434/api/tags`. |
| Out-of-memory | Run one job; use smaller models; switch Whisper to CPU; reduce context. |
| Invalid `.m4a` | Inspect with `ffprobe`; try conversion with FFmpeg; reject corrupt input. |
| SQLite locked | Ensure only one writer transaction at a time; keep transactions short. |
| Vite cannot reach backend | Check backend host/port, frontend API URL, and CORS settings. |
| FastAPI import error | Activate correct venv; install requirements; verify module path. |
| Model download fails | Check internet, disk space, Hugging Face access, and retry. |
| Slow processing | Check CPU/GPU utilization, model size, audio duration, and concurrent jobs. |

## 17. Cost and privacy notes

- Local inference does not incur per-request AI API charges.
- Initial model downloads use internet bandwidth and disk space.
- The Hugging Face token is used to access gated model files; do not expose it.
- Audio recordings and transcripts may contain sensitive information. Use consented or synthetic recordings, restrict local access, and implement deletion.
- Free/open-source software may have different licenses. Review each dependency and model license before redistribution or commercial use.

## 18. Final acceptance

The setup is complete only after a consented or synthetic `.m4a` file is processed end-to-end using local services, results are saved in SQLite, and the UI displays transcript, speaker attribution status, tone result, evidence, and action items. Record any unavailable component as a known limitation; never fabricate successful processing.
