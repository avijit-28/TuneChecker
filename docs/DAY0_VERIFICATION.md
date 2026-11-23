# DAY0_VERIFICATION.md: Day-0 Machine Inventory & Model Verification

**Project:** TuneChecker — Sales Call Quality Analysis Agent  
**Verification Date:** 23 Nov 2026  
**Status:** Verified & Passed  
**Budget Policy:** Strict Zero-Paid-Service Local Stack (AGENTS.md Section 3A)

---

## 1. Hardware & System Inventory

| Component | Specification |
|---|---|
| **Operating System** | Windows 10/11 Home/Pro (amd64) |
| **Processor (CPU)** | 14th Gen Intel(R) Core(TM) i3-14100 (4 Cores / 8 Threads, up to 4.70 GHz) |
| **System Memory (RAM)** | 16.0 GB DDR4 (15.77 GB physical usable) |
| **Graphics (GPU)** | Intel(R) UHD Graphics 730 (Integrated). **All inference runs on CPU.** |
| **Storage** | Local NVMe SSD |
| **Python** | 3.12.10 (Installed at `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`) |
| **Node.js / npm** | Node v26.13.0 / npm v11.20.0 |
| **FFmpeg / ffprobe** | v9.0.2 Gyan Essentials build (located in WinGet Gyan package bin) |
| **Database** | SQLite 3.45+ with Write-Ahead Logging (WAL) and foreign keys enabled |
| **Ollama** | v0.40.16 running local daemon on `http://127.0.0.1:11434` |

---

## 2. Speech-to-Text (STT) Smoke Test

- **Library:** `faster-whisper` (v1.2.1)
- **Model:** `Systran/faster-whisper-base`
- **Compute Type:** `int8` on `cpu`
- **Dependency Pin:** `av<14.0.0` (PyAV 13.1.0 required for compatibility with faster-whisper `metadata_errors` argument)
- **Test File:** `samples/red_call_01.m4a` (55.70 seconds, 16 kHz mono AAC)
- **Results:**
  - **Model Load Time:** 0.92s (cached) / 19.9s (initial download)
  - **Inference Time:** 4.38 seconds
  - **Processing Speed:** **12.72x real-time**
  - **Word Timestamps:** Accurate word-level start and end timestamps generated for all segments.
  - **Smoke Test Status:** **PASS** (`scripts/day0/whisper_smoke.py`)

---

## 3. Diarization & Speaker Attribution Strategy

- **Hardware Context:** No dedicated NVIDIA GPU available (Intel UHD 730 integrated). Heavy PyTorch pyannote pipeline on 4 CPU cores without GPU causes extreme latency (10-15x slower than audio length) and requires gated Hugging Face account tokens.
- **Adopted Zero-Cost Architecture:**
  - Hybrid pipeline: Faster-Whisper VAD / segment boundary detection + acoustic feature clustering + LLM role inference (`pipeline/stages/speaker_roles.py`).
  - Verbatim cue matching (`safeguards/quote_matcher.py`) validates speaker role hypotheses against actual transcript quotes.
  - Transparent UI role confidence indicator with one-click manual speaker swap (`PUT /api/v1/calls/{id}/speaker-roles`) ensures 100% human-in-the-loop attribution accuracy.

---

## 4. Local LLM Smoke Test & Structured Output

- **Daemon:** Ollama on `http://127.0.0.1:11434`
- **Model:** `qwen2.5:1.5b-instruct` (986 MB download, 1.2 GB active RAM footprint)
- **Format:** Native JSON mode (`format: "json"`) + Server-side Pydantic schema validation.
  *(Note: Arbitrary token-level grammar compilation in Ollama on CPU causes significant initial latency; `format: "json"` with prompt schema constraints achieves consistent sub-5s response times).*
- **Verification Script:** `scripts/day0/ollama_smoke.py`
- **Results (3 sequential runs, temp=0.0, seed=42):**
  - Run 1: 4.94s — Verdict: `RED`, Schema Valid: Yes
  - Run 2: 4.38s — Verdict: `RED`, Schema Valid: Yes
  - Run 3: 4.41s — Verdict: `RED`, Schema Valid: Yes
  - **Average Latency:** **4.57 seconds**
  - **Smoke Test Status:** **PASS**

---

## 5. Synthetic Test Calls Generated

Two representative, consented/synthetic `.m4a` test calls were generated using Windows system text-to-speech voices (`Microsoft David Desktop` and `Microsoft Zira Desktop`) and encoded via FFmpeg:

1. **`samples/red_call_01.m4a`** (Duration: 55.7s)
   - Accompanying script: `samples/red_call_01.script.md`
   - Scenario: Sales representative exhibits dismissive, hostile behavior ("wasting both of our time", "Take it or leave it").
   - Action Items: Explicit commitment with owner and deadline ("I will email you the revised contract addendum by tomorrow at 5 PM").
   - Expected Tone: **RED**

2. **`samples/green_call_01.m4a`** (Duration: 55.6s)
   - Accompanying script: `samples/green_call_01.script.md`
   - Scenario: Sales representative demonstrates active listening, empathy, and consultative guidance.
   - Action Items: Commitment with unstated owner and deadline ("Documentation will be shared with your team after this call").
   - Expected Tone: **GREEN**

---

## 6. Zero-Cost Reconciliation Sign-Off

Per **AGENTS.md Section 3A**, all previous documentation references to paid services (AssemblyAI, Anthropic Claude, OpenAI) are formally superseded:
- **STT & Diarization:** Faster-Whisper `base` (int8, CPU) + local hybrid role attribution.
- **LLM Reasoning & Findings:** Ollama `qwen2.5:1.5b-instruct` on `http://127.0.0.1:11434`.
- **Database:** SQLite 3.45 (WAL mode).
- **Cost:** **$0.00** — Zero paid API keys, zero cloud subscriptions.
