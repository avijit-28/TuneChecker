# INTEGRATIONS.md — Local AI and Audio Integrations

> Cost policy: zero paid API calls. All inference runs locally. Internet is needed initially for software/model downloads and gated model access.

## 1. Integration overview

| Component | Role | Execution |
|---|---|---|
| FFmpeg / FFprobe | Inspect, decode, convert audio | Local process |
| Faster-Whisper | Speech-to-text | Local inference |
| pyannote Community-1 | Speaker diarization | Local inference |
| Ollama + Qwen2.5 1.5B | Structured transcript analysis | Local inference |
| SQLite | Persist call and analysis data | Local database |

Keep each integration behind a small backend service adapter. Frontend code must never call model runtimes directly.

## 2. FFmpeg integration

**Purpose:** Inspect audio metadata and convert supported inputs when needed.

Implementation:
- Invoke FFmpeg/FFprobe with argument arrays, not shell-concatenated strings.
- Set timeouts and capture exit codes.
- Preserve the original recording.
- Store converted temporary audio in a controlled directory.
- Validate output before passing it to AI services.

Failure behavior:
- Mark preprocessing failed.
- Store a sanitized error category.
- Do not proceed with empty or invalid audio.

## 3. Faster-Whisper integration

**Purpose:** Produce transcript text and timestamps.

Initial model: `base`.

GPU configuration may use CUDA and a supported compute type only after compatibility testing. CPU fallback should use `device="cpu"` and `compute_type="int8"`.

Responsibilities:
- Load model from configuration.
- Transcribe approved audio.
- Preserve segment start/end times.
- Store language and model metadata where available.
- Return structured segments to the application.

Reliability rules:
- Do not invent words to fill gaps.
- Preserve empty/low-quality transcription status.
- Validate timestamps and text.
- Record the model configuration used.
- Do not report confidence as calibrated probability unless the model output actually supports that interpretation.

## 4. pyannote.audio Community-1 integration

**Purpose:** Detect speaker turns and diarization labels.

Model access:
- Use the official model page: https://huggingface.co/pyannote/speaker-diarization-community-1
- Accept its access conditions.
- Use a minimum-scope Hugging Face token in backend environment only.
- Review current model card and license before redistribution.

Responsibilities:
- Run diarization on the same audio timeline as transcription.
- Persist speaker turn intervals.
- Map transcript segments to diarization turns by temporal overlap.
- Use neutral labels (`SPEAKER_00`, etc.).
- Do not infer business role from diarization label or speaker order.

Failure behavior:
- Preserve transcript.
- Mark diarization unavailable or partial.
- Keep role as `UNKNOWN`.
- Do not run representative-only tone analysis unless the representative is confirmed.

## 5. Ollama integration

**Purpose:** Analyze representative transcript segments and extract structured evidence/action items.

Initial model:

```powershell
ollama pull qwen2.5:1.5b-instruct
```

Local endpoint:

```text
http://localhost:11434
```

Responsibilities:
- Confirm local model availability before a job.
- Send only required transcript segments and active settings.
- Use a fixed server-side instruction template.
- Request JSON output matching a Pydantic schema.
- Validate classification, evidence references, and action items.
- Persist model name and analysis settings version.

Do not:
- Use Ollama Cloud.
- Call hosted inference.
- Execute model-generated code or SQL.
- Trust unsupported owners, deadlines, or evidence.
- treat malformed JSON as success.

For long transcripts, split into bounded chunks and preserve segment IDs/timestamps. Aggregate only validated outputs and deduplicate action items using evidence-aware logic.

## 6. Tone analysis contract

Allowed overall outcomes:
- `RED`: negative representative tone is supported by evidence.
- `GREEN`: no configured negative tone is identified after sufficient representative speech was evaluated.
- `INSUFFICIENT_EVIDENCE`: role, transcript, or evidence is insufficient.

The ScaleWorks UI may emphasize RED/GREEN, but the implementation must preserve the insufficient-evidence state rather than falsely displaying GREEN.

Every RED finding must include:
- A real transcript segment ID.
- Exact or faithfully quoted segment text.
- Timestamp where available.
- Configured criterion/category.
- Concise explanation.

Evidence text must be checked against stored transcript segments. Customer speech must never be used as evidence of representative tone.

## 7. Action-item extraction contract

Every stored action item must be grounded in one or more actual transcript segments.

Fields:
- Description.
- Owner: nullable; only set when explicitly supported.
- Deadline: nullable; only set when explicitly stated.
- Evidence segment IDs.
- Timestamp(s), where available.

Do not infer a calendar date from a relative deadline unless a reliable call date/timezone and explicit conversion policy exist. Do not turn a request into a representative commitment unless the transcript supports that commitment.

## 8. Sequential orchestration and memory

Target hardware includes 8 GB RAM. Use one active analysis job at a time initially.

Suggested stages:
1. Validate/convert audio.
2. Load Whisper, transcribe, persist, release resources.
3. Load pyannote, diarize, persist, release resources.
4. Call local Ollama, validate and persist output.
5. Return results.

Measure actual RAM/VRAM use. Python object deletion does not guarantee immediate release of all GPU memory. Add explicit cleanup supported by the chosen runtime and process isolation if needed.

## 9. Configuration variables

Use `.env.example` placeholders, aligned with actual implementation:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b-instruct
WHISPER_MODEL=base
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=int8_float16
HUGGINGFACE_TOKEN=replace_with_read_token
AUDIO_STORAGE_PATH=./storage/audio
MAX_UPLOAD_SIZE=52428800
```

Never expose `HUGGINGFACE_TOKEN` or local filesystem paths unnecessarily to the frontend.

## 10. Retry, timeout, and fallback strategy

| Integration | Retry policy | Fallback |
|---|---|---|
| FFmpeg | Retry only transient process failure | Mark invalid/failed; do not bypass validation |
| Faster-Whisper | Avoid blind retries for deterministic errors | CPU mode or smaller model |
| pyannote | Retry download/network errors cautiously | Unknown speaker role; retain transcript |
| Ollama | Retry transient local connection once/twice | Mark analysis failed/partial; never fabricate result |
| SQLite | Retry only safe transient lock errors | Return clear failure; do not lose job state |

Use bounded timeouts and avoid retry loops.

## 11. Integration tests

- [ ] FFmpeg reads valid `.m4a`.
- [ ] Faster-Whisper produces timestamped transcript segments.
- [ ] pyannote returns diarization turns or a handled failure.
- [ ] Unknown speaker role is preserved.
- [ ] Ollama is reachable locally.
- [ ] Invalid JSON is rejected.
- [ ] RED evidence maps to an actual representative segment.
- [ ] Customer-only negative language does not cause RED.
- [ ] Action-item owner/deadline remain null when unsupported.
- [ ] No paid endpoint is called.
