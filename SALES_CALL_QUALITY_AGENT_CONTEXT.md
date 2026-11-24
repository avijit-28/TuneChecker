# 🎙️ TuneChecker - Sales Call Quality & Tone Checker AI Platform
## Master Handoff & Context Document for Claude Code / External AI Agents

> **Generated From Conversation:** `Sales Call Quality Agent` (ID: `760c9929-3067-4768-bc96-e6835e869f6d`)  
> **Project Root Directory:** `D:\avi\TuneChecker`  
> **Target Audience:** Claude Code / Cursor / Codex / AI Coding Assistants  
> **Primary Purpose:** Provide complete, unabridged architectural, historical, and implementation context so an AI agent can immediately resume work without asking the user repetitive questions.

---

## 1. Project Overview & Core Mission

**TuneChecker** is an enterprise AI-powered **Sales Call Quality & Tone Auditor** built for sales teams, quality auditors, and contact centers.

### What it does:
1. **Audio Ingestion & Preprocessing:** Ingests call recordings across multiple formats (`.mp3`, `.m4a`, `.mpeg`, `.mp4`, `.wav`, `.webm`) or captures live microphone audio in the browser.
2. **Multilingual Transcription (English / Hindi / Hinglish):** Transcribes conversations using Faster-Whisper (`large-v3-turbo`) with domain-specific vocabulary and prompt biasing for accented Indian English and code-mixed Hindi-English.
3. **Speaker Diarization & Role Assignment:** Automatically segments speech and classifies **who is the Sales Representative** and **who is the Customer / Client** using acoustic spectral clustering and LLM conversational heuristics.
4. **Tone & Quality Auditing:** Evaluates the conversation using LLMs (Ollama `qwen2.5:1.5b-instruct` or Google Gemini API) to assess empathy, aggressiveness, pushiness, active listening, and professionalism. Assigns an automated **Verdict (GREEN / AMBER / RED)** with a numerical Quality Score (0–100).
5. **Evidence Extraction & Action Items:** Quotes exact timestamps and speaker phrases for compliance checks and generates constructive coaching points for the sales agent.
6. **Auditor Manual Override:** If automatic speaker identification swaps the roles, auditors can click **"Swap Speakers"** in the UI to correct the roles and trigger an automatic re-evaluation.

---

## 2. Directory Structure & Key Components

```
D:\avi\TuneChecker/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── calls.py              # Upload, processing trigger, status, and results endpoints
│   │   │   ├── health.py             # System health, Ollama status, FFmpeg check
│   │   │   ├── settings.py           # Model settings, prompts, threshold configurations
│   │   │   └── transcripts.py        # Segment updates, speaker role overrides
│   │   ├── core/
│   │   │   ├── config.py             # App settings (Pydantic), paths, audio storage
│   │   │   └── database.py           # SQLite connection via SQLAlchemy (app.db)
│   │   ├── models/                   # SQLAlchemy models (Call, Segment, Analysis, ActionItem)
│   │   ├── pipeline/
│   │   │   ├── orchestrator.py       # 7-Stage Pipeline runner with error handling & retries
│   │   │   ├── safeguards/           # Audio integrity, hallucination checkers, speaker alignment
│   │   │   └── stages/
│   │   │       ├── validation.py     # Stage 1: Audio duration, format, channel validation
│   │   │       ├── transcription.py  # Stage 2: Faster-Whisper (large-v3-turbo) + Hinglish prompt
│   │   │       ├── speaker_roles.py  # Stage 3: Spectral clustering + LLM role heuristic (Sales vs Client)
│   │   │       ├── tone_analysis.py  # Stage 4: LLM audit, empathy/aggression scoring, verdict
│   │   │       ├── evidence.py       # Stage 5: Timestamped quote extraction & verification
│   │   │       ├── action_items.py   # Stage 6: Actionable coaching recommendations
│   │   │       └── completion.py     # Stage 7: Final state persistence
│   │   └── utils/                    # Audio converter (FFmpeg), logger, errors
│   ├── data/
│   │   ├── app.db                    # SQLite primary database
│   │   └── audio/                    # Uploaded raw audio storage (UUID-named files)
│   ├── requirements.txt              # FastAPI, faster-whisper, torch, librosa, soundfile, pydantic
│   └── alembic/                      # Database migrations
│
├── frontend/
│   ├── src/
│   │   ├── api/client.ts             # Axios/fetch API client targeting http://localhost:8000
│   │   ├── components/
│   │   │   ├── upload/DropZone.tsx   # Drag-and-drop file upload + Live Mic recording
│   │   │   ├── processing/Stepper.tsx# 7-stage live visual pipeline stepper
│   │   │   ├── transcript/           # TranscriptViewer, RoleBadge, SpeakerSwapModal
│   │   │   └── analysis/             # VerdictCard (Green/Amber/Red), EvidencePanel, ActionItemsPanel
│   │   ├── pages/                    # UploadPage, ProcessingPage, ResultsPage, HistoryPage, SettingsPage
│   │   └── styles/                   # Tailwind CSS, design tokens
│   └── package.json                  # React 19, TypeScript, Vite, Tailwind CSS
│
├── samples/                          # Test audio files (.m4a, .mp3, .mpeg, .mp4) & human scripts
└── docs/                             # Original design specs (SETUP, TESTING, FEATURES, etc.)
```

---

## 3. Detailed Chronology of the Conversation

### Phase 1: Initial Ingestion & Architecture Bootstrap
* **User Request:** Initialized the project with reference documents (`AUTH_SECURITY.md`, `SETUP.md`, `FEATURES.md`, etc.) inside `D:\avi\TuneChecker`.
* **Action:** Configured FastAPI backend on port 8000 and Vite React frontend on port 5173. Set up the local SQLite database (`app.db`) and Alembic migrations.

### Phase 2: Audio Format Expansions
* **Problem:** The system initially only accepted `.m4a` files.
* **User Requests:** *"why only m4a, what about other files like mp3 etc?"*, *"what about mpeg?"*, *"make it also for mp4"*.
* **Implementation:**
  * Updated `backend/app/pipeline/stages/validation.py` and `backend/app/utils/audio.py` to support `.mp3`, `.m4a`, `.wav`, `.mpeg`, `.mp4` (video/audio extraction), and `.webm`.
  * Configured FFmpeg to extract audio tracks from MP4 video containers and convert any arbitrary sample rate to 16kHz mono PCM for Whisper.
  * Updated frontend `DropZone.tsx` `accept` attributes to permit all these media types.

### Phase 3: Hindi & Hinglish Transcription Accuracy Issues
* **Problem:** When the user uploaded a real-world WhatsApp audio recording (`WhatsApp_Audio_...mpeg`), the transcription output dropped text, hallucinated, and missed Hinglish colloquial words.
* **User Feedback:** *"model thik se trained nhi hua hai... galat text extract kar rha hai"*, *"there will be an option for hinglish transcribe"*.
* **Solution Implemented:**
  1. **Model Upgrade:** Upgraded from Whisper base/small to **Faster-Whisper `large-v3-turbo`** (running via PyTorch CUDA or CPU with INT8 quantization).
  2. **Prompt Biasing (`initial_prompt`):** Injected phonetic Hinglish/Hindi domain prompts:
     `"This is a business conversation in Hindi and English (Hinglish). Common terms: sir, client, project, payment, budget, features, developer, delivery, meeting, theek hai, achha, samajh gaya."`
  3. **Language Selection:** Added explicit language configuration in the settings and pipeline (`auto`, `hi`, `en`, with Hinglish phonetic support).

### Phase 4: Integration from Reference Project (`SpeechGuard AI V2`)
* **User Request:** Provided reference project at `C:\Users\avijitpakhira\Downloads\SpeechGuard_AI_V2_VSCode_Project`.
* **Analysis & Integration:**
  1. **Live Microphone Recording:** Ported the in-browser live recording component (`MediaRecorder` API) into `DropZone.tsx` so users can speak directly into the browser.
  2. **Speaker Identification Logic:** Studied SpeechGuard's heuristics for identifying who is speaking.

### Phase 5: The Speaker Diarization / Role Assignment Problem
* **User Problem:** *"yeah, it fully transcribe the audio to text, but it couldn't identify who is client and who is sales"*.
* **Root Cause & Technical Fix:**
  * Traditional Whisper outputs timestamps and text, but on mono recordings (like WhatsApp voice notes or phone calls), both speakers are in one channel.
  * We implemented a dual-stage speaker diarization & classification pipeline:
    1. **Acoustic Diarization:** Librosa MFCC feature extraction + Spectral Clustering to cluster timestamps into `SPEAKER_00` and `SPEAKER_01`.
    2. **LLM Conversational Role Classifier:** Analyzes conversational turn patterns:
       * **Sales Rep Markers:** Professional greetings, presenting pricing, asking qualifying questions (*"How can I help you?", "Our package costs...", "Let me share the demo"*).
       * **Customer / Client Markers:** Describing pain points, asking for discounts, stating requirements (*"I need an app", "What is the cost?", "Can you reduce the price?"*).
    3. **Speaker Swap Safety Valve:** Added `SpeakerSwapModal.tsx` in the frontend allowing auditors to manually swap roles with a single click.

### Phase 6: Bug Fixes in Latest Steps
* **Bug Encountered:** User saw `"Failed to Load Analysis"` in the frontend.
* **Cause:** A Python `NameError: name 'heuristic_cues' is not defined` in `speaker_roles.py` halted the pipeline before tone analysis could execute.
* **Fix Applied:** Fixed variable references in `backend/app/pipeline/stages/speaker_roles.py` and committed to master (`git commit 8e05d89`).
* **Latest Test:** User uploaded `WhatsApp_Audio_2026-11-24_at_11.09.45.mp4` (Duration: 313.4s). The pipeline processed through validation, transcription, speaker identification, and tone analysis.

---

## 4. How to Run the Environment

### Prerequisites:
* Python 3.10+ (Current venv is at `D:\avi\TuneChecker\backend\.venv`)
* Node.js 18+ & npm
* Local Ollama running on `http://127.0.0.1:11434` with model `qwen2.5:1.5b-instruct` OR Google Gemini API Key configured in `backend/.env`.
* FFmpeg installed and accessible on PATH (System has FFmpeg at `C:\Users\avijitpakhira\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe`).

### Starting the Backend:
```powershell
cd D:\avi\TuneChecker\backend
.\.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*API Docs available at:* `http://localhost:8000/docs`

### Starting the Frontend:
```powershell
cd D:\avi\TuneChecker\frontend
npm run dev
```
*UI available at:* `http://localhost:5173`

---

## 5. Current Active State & Next Tasks for Claude Code

When you pick up this task in Claude Code, here is the exact status and what needs attention:

### 1. Verify Call ID `6ca36639-f508-41c0-a65b-f03fa3c116f9`
* The latest audio uploaded by the user (`WhatsApp_Audio_2026-11-24_at_11.09.45.mp4`) was processed under Call ID `6ca36639-f508-41c0-a65b-f03fa3c116f9`.
* Check its final analysis status via:
  ```powershell
  curl http://localhost:8000/api/v1/calls/6ca36639-f508-41c0-a65b-f03fa3c116f9/results
  ```
* Ensure the transcript shows the correct speaker labels (`Sales Rep` vs. `Customer`) for both speakers.

### 2. Refine Speaker Diarization on Mono WhatsApp Calls
* **Current Logic:** `backend/app/pipeline/stages/speaker_roles.py` and `backend/app/pipeline/safeguards/speaker_alignment.py`.
* **Area to Improve:** WhatsApp audio is typically 8kHz or 16kHz mono. If acoustic spectral clustering assigns speech turns incorrectly due to background noise:
  * Ensure the LLM conversational classifier has enough context (the first 4–6 conversational turns) to reliably detect who asked for the service (Customer) and who answered (Sales/Developer).
  * Check that `SpeakerSwapModal.tsx` in `frontend/src/components/transcript/SpeakerSwapModal.tsx` triggers the backend `POST /api/v1/transcripts/{call_id}/swap-speakers` endpoint cleanly and updates the UI instantly without page reload.

### 3. Verify Tone Verdict & Coaching Card Output
* In `backend/app/pipeline/stages/tone_analysis.py`, verify that the generated scorecard contains:
  * Overall Call Verdict (`GREEN`, `AMBER`, `RED`)
  * Empathy Score (0–100)
  * Professionalism Score (0–100)
  * Objection Handling Score (0–100)
  * Specific, cited evidence quotes with speaker attribution.
