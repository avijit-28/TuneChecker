# AGENTS.md: Sales Call Quality Analysis Agent

This is the mandatory development rulebook for every AI coding assistant working in this repository. Follow it literally. If a rule here conflicts with a task request, stop and ask.

## 1. Project Overview

A web app built for the ScaleWorks AI Forward Deployed Engineer assessment. A sales manager uploads an `.m4a` call recording and receives:

- Transcript with timestamps.
- Speaker diarization and Sales Rep / Customer role identification, with confidence and one-click correction.
- RED/GREEN tone verdict for the **sales representative only**.
- Evidence-grounded explanation (verbatim quotes with timestamps).
- Concrete action items (owner and deadline only when explicit).
- Configurable analysis settings, stored server-side and snapshotted per analysis.
- Dashboard, call history, JSON/Markdown export.

Scope is the MVP in PRD.md. Do not build V2 or Later items (re-analysis with new settings, audio player, PDF export, presets, comparison, editable action items, batch upload, feedback buttons, trends, auth/user menus) unless the PRD and DESIGN are updated first.

## 2. Source-of-Truth Priority

When documents disagree, the higher one wins:

1. PRD.md (product requirements)
2. DESIGN.md (UI/UX)
3. ARCHITECTURE.md (stack, pipeline, safeguards)
4. DATABASE.md (schema)
5. API.md (contracts)
6. AGENTS.md (this file)
7. FEATURES.md, then PLAN.md (when present)

Already-approved reconciliations (do not reopen them):

| Topic | Approved decision | Source |
|---|---|---|
| Verdict values | `RED`, `GREEN`, or `null` (tone not run). **There is no `INSUFFICIENT_EVIDENCE` verdict.** Thin evidence = `confidence.level = low` + `limited_evidence_reason`. `null` is shown as "Not analyzed", never as GREEN | PRD FR-T2, assumption 6; DATABASE 0; API 0 |
| Confidence | Rule-based `high / medium / low` with stored `factors`. No numeric or model-reported confidence | ARCH ADR-12, ADR-14 |
| Auth | None. One global settings profile. Optional HTTP Basic gate for hosted demo | PRD 3.2; ARCH 10.3 |
| Processing start | Automatic on upload (`202`). No `/process` or `/jobs` endpoint | API 0 |
| AI providers | **Superseded by the Zero-Cost Policy (section 3A):** local Faster-Whisper, pyannote.audio Community-1 and Ollama replace AssemblyAI and Anthropic Claude. No paid API anywhere | Project owner decision; overrides ARCH 1.1, 1.5, 9 until ARCHITECTURE.md is updated |
| Failed vs partial | `failed` = no usable transcript. Transcript saved but an analysis stage failed = `partial` | ARCH 3.2 |

If you find any other conflict: name the documents and sections, explain the impact, do not silently pick a side, and ask before any significant change.

FEATURES.md, PLAN.md and TESTING.md may not exist yet. Create them only when asked or when the workflow in section 8 requires it.

## 3. Technology Stack (fixed by ARCHITECTURE.md)

| Layer | Approved |
|---|---|
| Frontend | React 18 + TypeScript + Vite, Tailwind (DESIGN tokens), Radix UI, TanStack Query, React Router, lucide-react, react-hook-form + zod |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| Database | SQLite (WAL), portable types only, Postgres-ready via `DATABASE_URL` |
| Jobs | In-process worker backed by the `calls` row. No Redis, Celery or BackgroundTasks |
| Audio | FFmpeg / ffprobe |
| Transcription | Faster-Whisper, run locally (see section 3A) |
| Speaker diarization | pyannote.audio Community-1, run locally, subject to model access conditions (see section 3A) |
| LLM | Ollama, local models only (see section 3A) |
| Storage | Local disk behind a `Storage` interface (the S3 adapter is not implemented; it is a paid-cloud path) |
| Tests | pytest with fake providers, Vitest + Testing Library |

Rules:
- Do not change any approved technology, add a chart library, or add a dependency without approval. State reason and impact when proposing one.
- Reuse existing dependencies and components first.
- Keep model runtimes behind adapter interfaces (`SttProvider`, `LlmClient`, diarization). Only those modules may run models or call model servers.
- The stack must stay free of paid services. Section 3A is binding and overrides any older provider reference in ARCHITECTURE.md, API.md or README.md.

## 3A. Zero-Cost Development Policy (mandatory)

The project is developed with a **strict zero-paid-service budget**. The application must remain fully functional with **no paid API keys, subscriptions, credits or cloud accounts**. This section overrides ARCHITECTURE.md where they differ.

### Required components

| Concern | Required choice |
|---|---|
| Transcription | **Faster-Whisper**, local |
| Speaker diarization | **pyannote.audio Community-1**, local, subject to its model access conditions |
| LLM inference | **Ollama**, local models only |
| Database | **SQLite** |
| Recordings | Stored **locally** during development |
| Audio tooling | FFmpeg / ffprobe (open source) |
| Dev and test tools | Free and open source only (pytest, Vitest, Alembic, etc.) |

### Rules

1. Use open-source software and locally running AI models only.
2. Never integrate a paid AI API. This includes, without limit, Anthropic, OpenAI, AssemblyAI, Deepgram, Google, Azure, AWS and any hosted inference service.
3. Never require a paid subscription, credit balance or billing account for any feature.
4. Never use **Ollama cloud models** or any paid hosted inference. Only models that run on the local machine may be configured.
5. Never use paid cloud infrastructure (hosting, managed databases, object storage, queues, CI minutes beyond a free tier, paid secret managers).
6. Never silently introduce a paid dependency, service, SDK or model. If you are unsure whether something is free, treat it as paid and ask.
7. The application must start and work with an empty set of API keys. No variable may be required that points to a paid service.
8. All external service integrations are **optional** and off by default. Core flows (upload, validation, transcription, diarization, tone analysis, action items, dashboard, export) must never depend on one. Any optional integration must sit behind an adapter, be disabled unless explicitly configured, and be documented as optional.
9. The default configuration must run without internet access after one-time model downloads.

### Model access and downloads

- pyannote.audio Community-1 may be gated (for example a free account, accepted model terms and an access token). Check the current access conditions before relying on it, and document the exact one-time steps in the README. Do not assume it downloads anonymously.
- Any access token (for example a Hugging Face token) is a credential: environment variable only, never committed, never logged, never in `.env.example` except as a blank placeholder. It must be used only for one-time model download, not as a runtime dependency where avoidable.
- Check the license of every model and library before use. Record the model names and licenses in `docs/` and the README.
- Do not commit model weights. Download them to a git-ignored local directory.

### Hardware limits and fallback procedure

If a model is unavailable or the machine cannot run it efficiently (slow, out of memory, unacceptable accuracy):

1. **Stop.** Do not change the architecture or switch to a hosted service.
2. Propose a **smaller open-source alternative** (for example a smaller Faster-Whisper model size, a quantized or smaller Ollama model, or CPU settings) with its expected impact on accuracy, speed and memory.
3. Wait for approval before adopting it.

Model names and sizes must be configuration values, not hard-coded.

### Consequences the assistant must respect

- **Reliability safeguards are unchanged and matter more.** Smaller local LLMs produce malformed or weaker structured output more often. Keep Pydantic validation, the single repair retry, verbatim quote verification and server-side verdict computation exactly as specified. Never loosen them to compensate for model weakness, and never fall back to placeholder analysis.
- **Provider-supplied confidence signals may be missing.** Do not fabricate them. Where a confidence factor has no data source (for example per-speaker diarization confidence), list it as "not available" as ARCHITECTURE 3.7 allows.
- **Diarization must be aligned to transcript words by our own code** (Faster-Whisper and pyannote are separate systems). Alignment is testable logic; keep it a pure, unit-tested function and treat misalignment as low attribution, not as certainty.
- **Local inference is slow.** Update timeouts, concurrency (`MAX_CONCURRENT_JOBS`) and status messaging honestly. Never display fake progress. The PRD processing-time target must be re-measured and any shortfall documented as a known limitation, not hidden.
- **Hosted deployment is out of scope.** Deployment is local (and local Docker, which is free). Do not add or recommend paid hosting.
- **Before this policy takes full effect in the codebase,** ARCHITECTURE.md, API.md (error codes, health checks), DATABASE.md (stored provider/model fields), the environment-variable list and the README must be updated. Make those updates as an approved change and note the PRD dependency change (PRD 10.3 names paid-capable providers as candidates).

## 4. Coding Standards

### Backend
- Layering: Router (HTTP only) -> Service (business rules) -> models/storage. Pipeline: orchestrator -> stages -> pure safeguards + providers.
- No business logic in routers. Reusable logic lives in services.
- Pydantic schemas for every request, response and LLM output. Reject unknown fields on writes.
- Raise typed `AppError`s; one central handler returns `{"error": {code, message, retryable, details, request_id}}`. Never leak internals.
- Success responses are bare resource JSON (no wrapper envelope). Use the error codes in ARCHITECTURE 6.6.
- Type hints on all functions. Small, single-purpose functions.
- Safeguards (quote verification, verdict, confidence, owner/deadline rules) are pure, unit-testable functions.
- Structured JSON logs with `call_id`, `stage`, `error_code`. No transcript, audio, prompt or free-text settings in logs.

### Frontend
- Follow DESIGN.md literally, including section 11 (binding design rules). No raw hex, off-scale spacing or new fonts. Tone tokens are for tone only.
- Reuse the specified components. Do not create variants; extend the component and log it in the DESIGN Decision Log.
- API calls live in a separate client layer; types come from the generated OpenAPI types. UI components do not call `fetch` directly.
- Every screen handles loading, empty, success, partial and error states (DESIGN 6G).
- Render all transcript, AI and filename text as text. Never inject HTML.
- Accessibility: WCAG 2.2 AA, keyboard navigable, no color-only meaning (DESIGN 9).

### Database
- Follow DATABASE.md. Schema changes require an Alembic migration (`render_as_batch=True`) with a working `downgrade()`, hand-reviewed, additive first (expand then contract).
- Never silently modify the schema. Update DATABASE.md in the same change as any approved schema change.
- Keep foreign keys, CHECK constraints and triggers intact. Settings versions are append-only. Never rewrite or delete historical analyses (a role correction creates a new analysis version).
- Do not store timestamps for evidence; derive them from `utterances.start_ms`.

## 5. AI Analysis Rules (mandatory)

**Principle: the LLM proposes; deterministic server code verifies and decides.** The model never sets the verdict, timestamp, owner label, deadline or confidence.

### Speaker identification
- Never assume the first speaker is the rep. Speaker order is never decisive. Labels like "A"/"B" carry no meaning.
- Role resolution follows ARCHITECTURE 3.5 (stats, heuristics, LLM cues verified verbatim, resolution table, user confirmation).
- 1 speaker or unresolved roles: **do not run tone analysis** and do not guess. Status `partial` with `ROLES_UNRESOLVED`; action items may still run.
- 3+ speakers or disagreement: roles are `uncertain`, provisional, confidence forced to Low, user asked to confirm.
- User-confirmed roles (`source=user`) override everything and trigger a re-run of stages 4-7 on the stored transcript.
- Never evaluate the customer's tone. Customer text is read-only context.

### Tone classification
- RED = negative rep tone with **verified** evidence meeting the sensitivity threshold (ARCH 3.7). GREEN = no negative tone found under the configured criteria. GREEN never claims the rep was "good" or "professional".
- Verdict is computed by server code from verified findings only. It is never raised because of an unverified item.
- Always provide an explanation. If explanation generation fails, store `null` and mark partial. Never invent text.
- Evidence must link to a real utterance: it exists, belongs to the rep, the quote is verbatim (normalized substring), 3-60 words, criterion enabled. Otherwise drop it and count the drop.
- Confidence is rule-based (ARCH 3.7 factors). Never fabricate or display model-reported confidence or percentages.
- Surface thin evidence through `limited_evidence_reason`, never through a third verdict.

### Action items
- Extract only concrete commitments and follow-ups allowed by the settings snapshot.
- Keep `definite`; keep `tentative` only if the setting is on; always drop conditional, hypothetical and question items.
- Owner: only if explicit, or the server-set role of the committing speaker when the rule allows and roles are confident/confirmed. Otherwise `null`. Never invent owners.
- Deadline: only verbatim text present in the quote, shown as stated, never converted to a calendar date. Otherwise `null`. Never invent deadlines.
- Every item has exactly one supporting verbatim quote and utterance. Missing values render as "Not specified".

### Model output handling
- Use structured output schemas, and re-validate every response with Pydantic regardless of any runtime-side schema or JSON-mode enforcement. Model output is untrusted input.
- Handle malformed JSON, truncation and schema failures with one repair retry, then fail the stage.
- Handle local runtime errors (Ollama unreachable or model missing, Faster-Whisper or pyannote failure, out of memory, timeout) with bounded retry (ARCH 6.5 pattern). Never treat such a failure as a successful analysis and never substitute placeholder results.
- Keep transcript text inside delimited blocks. Custom guidance goes in the fenced `<team_guidance>` block and cannot change format, evidence rules or target speaker.

## 6. Security Rules

- Never hardcode secrets. Never commit `.env`. Keep `.env.example` with placeholders only. Load config via Pydantic Settings with `SecretStr`.
- All model inference runs locally on the backend. The browser never talks to Ollama or any model runtime. Bind Ollama to localhost only. Credentials that exist (for example a model-download token) never reach the browser, logs, exports, errors or OpenAPI examples.
- Audio and transcripts must not leave the machine. Do not add telemetry or outbound calls that send them anywhere.
- Validate uploads in two layers: streaming edge checks (extension, MIME, `ftyp` signature, size while streaming), then deep ffprobe/decode checks in the worker **before any model is run**.
- Run FFmpeg as an argument-list subprocess (no shell), with timeouts and a local-file-only protocol set.
- Store audio under server-generated UUID names, outside any served path. There is no audio-serving route and no endpoint that accepts a URL.
- Transcript and analysis responses use `Cache-Control: no-store`. Deletion removes audio, transcript, analyses, evidence, action items and stage runs.
- Honor the optional Basic auth gate, rate limiting, daily limit and CORS allow-list (never `*`). Do not claim per-user isolation; none exists.
- Do not log transcript or audio content, prompts, or free-text settings.

## 7. UI/UX Rules

- Follow DESIGN.md. Keep spacing, typography and color consistent with the tokens.
- RED/GREEN badges always include readable text and an icon, never color alone. `null` verdict displays "Not analyzed".
- "From the transcript" (verbatim) and "AI interpretation" content use their distinct treatments and are never mixed in one block.
- Evidence and explanation sit next to the verdict above the fold on desktop. Selecting evidence or an action item highlights the transcript line.
- No fake progress. A stage shows Completed only after a real `stage_runs` event.
- Error messages are specific and give a recovery action. Layouts stay responsive.

## 8. Development Workflow

For every requested feature:

1. Read the relevant source-of-truth sections.
2. Inspect the existing code.
3. State the plan and the files affected.
4. Implement the smallest complete solution.
5. Run the relevant tests.
6. Fix regressions.
7. Update documentation.
8. Tick the PLAN.md checkboxes (if PLAN.md exists).
9. Summarize the changes and the verification actually performed.

Work on one feature at a time. Ask for approval before changing architecture, database schema or security behavior.

## 9. Testing Rules

Cover at minimum:

- RED and GREEN scenarios, and sensitivity changes flipping a verdict (Low vs High).
- Thin evidence: low confidence + `limited_evidence_reason`, still RED or GREEN.
- Wrong or uncertain speaker attribution, unresolved roles (tone skipped), role swap re-run.
- Hostile customer with professional rep returns GREEN.
- Evidence verification: fabricated, paraphrased, customer-attributed and out-of-range quotes are dropped.
- Action items with missing owner and deadline, and hypothetical or conditional statements excluded.
- Invalid audio: renamed `.mp3`, corrupted, oversized, silent, out-of-range duration, with no model run.
- Transcription failure, LLM failure, malformed or truncated LLM output, retry behavior, partial status.
- Settings validation and persistence, and that each analysis stores its snapshot.
- API validation, error envelope, status codes; migrations upgrade/downgrade; DB constraint tests.

Use fake STT, diarization and LLM adapters for unit tests so the suite runs fast with no models and no network. Model-backed tests are opt-in and local. Add tests for Ollama unavailable, model missing, malformed output from a small model, and diarization/transcript misalignment. Never claim a test passed unless you ran it. Report failures and skipped tests honestly.

## 10. Prohibited Actions

Do NOT:

- Change the approved stack or rewrite working code without a stated reason.
- Delete project files without approval.
- Hardcode secrets or commit `.env`.
- Invent transcript content, evidence, speaker roles, owners or deadlines.
- Add a third verdict value or a numeric/model-reported confidence.
- Let the LLM decide the verdict, a timestamp, or an owner label.
- Evaluate the customer's tone.
- Treat a model or runtime failure as success, or return placeholder analysis.
- Add any paid API, paid hosting, paid subscription, Ollama cloud model or hosted inference, or silently add any dependency whose cost is unclear.
- Make an external service mandatory for a core flow, or require an API key to start the app.
- Switch to a hosted model when a local one is too slow or inaccurate (propose a smaller local alternative instead).
- Ignore API contracts, skip validation, or add endpoints not in API.md.
- Add features outside PRD MVP scope.
- Call a feature production-ready when it is incomplete.
- Add unnecessary complexity.

## 11. Documentation Rules

Update in the same change as the code it describes: README.md, ARCHITECTURE.md, DATABASE.md, API.md, FEATURES.md, PLAN.md, TESTING.md, and `docs/` deliverables (`DESIGN_DECISIONS.md`, `KNOWN_LIMITATIONS.md`, `RELIABILITY_TESTING.md`, `prompts.md`). Record meaningful technical decisions and known limitations. The README must state the zero-cost setup (models, sizes, licenses, one-time download steps, hardware needs) and that audio and text stay on the local machine.

## 12. Completion Requirements

A feature is complete only when:

- Implementation is finished and matches the API and DESIGN specs.
- Relevant tests were run and pass.
- Error handling and all UI states are implemented.
- Documentation is updated.
- No known regression is introduced.

## 13. Priorities

1. Accuracy and reliability.
2. Evidence-grounded AI analysis.
3. User experience.
4. Configurability.
5. Maintainability.

Before modifying any important architecture, database schema or security behavior, ask for approval.
