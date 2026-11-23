# FEATURES.md — Feature Implementation Guide

> Project: Sales Call Quality Analysis Agent  
> Source of truth: `PRD.md`, `DESIGN.md`, `ARCHITECTURE.md`, `DATABASE.md`, `API.md`, `AGENTS.md`, and `PLAN.md`.

## Development rules

- Implement one feature at a time.
- Before starting, inspect the existing code and relevant source-of-truth documents.
- Preserve the selected zero-cost local stack.
- Do not introduce paid APIs or hosted inference.
- Keep the application runnable after each vertical slice.
- Update `PLAN.md` only after verification.
- Do not mark a feature complete until its acceptance criteria pass.

## Feature 1 — Application foundation

**User story:** As a sales manager, I want the application to start reliably so I can analyze calls.

**Components:** React shell, navigation, FastAPI application, configuration module, SQLite connection.

**Build order:**
1. Create the approved folder structure.
2. Configure backend settings from environment variables.
3. Configure SQLAlchemy and database session management.
4. Add `/health` endpoint.
5. Create React application shell and navigation.
6. Connect frontend health indicator to backend.
7. Add centralized frontend and backend error handling.

**Edge cases:** Missing `.env`, database unavailable, backend offline, frontend API URL incorrect.

**Acceptance criteria:**
- [ ] Backend starts using documented command.
- [ ] Frontend starts using documented command.
- [ ] Health endpoint returns a valid response.
- [ ] Missing configuration produces a clear error.
- [ ] No secrets are committed.

## Feature 2 — Audio upload and validation

**User story:** As a sales manager, I want to upload an `.m4a` call recording so it can be analyzed.

**Components:** Upload page, drag/drop area, upload API, audio validation service, local storage service, Call and Job records.

**Build order:**
1. Create upload form and file selection.
2. Accept `.m4a` only for the assessment MVP.
3. Validate extension, MIME type, file signature where practical, size, and audio integrity.
4. Use FFprobe/FFmpeg to inspect the recording.
5. Store with a generated safe filename; never trust the supplied path.
6. Create Call and AnalysisJob records.
7. Return call ID and initial status.
8. Display success, validation, and upload errors.

**Edge cases:** Empty file, oversized file, renamed non-audio file, corrupt file, duplicate filename, interrupted upload, path traversal attempt.

**Acceptance criteria:**
- [ ] Valid `.m4a` is stored safely.
- [ ] Invalid or corrupt file is rejected.
- [ ] Original filename is stored as metadata only.
- [ ] Upload path cannot escape the configured storage directory.
- [ ] Upload status is visible in the UI.

## Feature 3 — Audio preprocessing

**User story:** As the system, I need valid audio input in a supported format for transcription and diarization.

**Components:** Audio processing service, FFmpeg wrapper, temporary file manager.

**Build order:**
1. Inspect codec, duration, sample rate, and channels.
2. Convert only when required.
3. Preserve the original upload.
4. Create temporary normalized audio using documented settings.
5. Capture FFmpeg errors safely.
6. Delete temporary artifacts after processing or according to cleanup policy.

**Edge cases:** Unsupported codec, silent audio, very long audio, malformed metadata, disk full.

**Acceptance criteria:**
- [ ] Conversion is deterministic for the test fixture.
- [ ] Original recording remains unchanged.
- [ ] Invalid audio receives a useful error.
- [ ] Temporary files are cleaned up.

## Feature 4 — Speech transcription

**User story:** As a sales manager, I want a readable transcript with timestamps so I can review the call.

**Components:** Faster-Whisper service, transcript schema, transcript segment model, transcript viewer.

**Build order:**
1. Load configured local Whisper model.
2. Select CUDA only after runtime compatibility check; otherwise use CPU fallback.
3. Transcribe audio with VAD where appropriate.
4. Store language, provider/model, segment text, start/end times.
5. Preserve original segment order.
6. Display transcript and transcription status.
7. Record failure without pretending the call is complete.

**Edge cases:** No speech, low-volume speech, accents, overlapping speech, long recordings, model unavailable, CUDA out-of-memory.

**Acceptance criteria:**
- [ ] Test audio produces non-empty transcript when speech is audible.
- [ ] Segment timestamps are non-negative and ordered.
- [ ] Transcription errors are visible.
- [ ] No paid speech API is called.
- [ ] Transcript is linked to the correct call.

## Feature 5 — Speaker diarization and role confirmation

**User story:** As a sales manager, I want speakers distinguished so the system evaluates the representative rather than the customer.

**Components:** pyannote Community-1 adapter, Speaker model, segment-speaker mapping, role confirmation UI.

**Build order:**
1. Run diarization on the same audio timeline.
2. Store speaker turns and timestamps.
3. Map transcript segments to speaker turns using temporal overlap.
4. Assign neutral labels such as `SPEAKER_00`.
5. Do not infer the representative from speaker order.
6. Provide role confirmation when the role is not reliably known.
7. Preserve `UNKNOWN` if no confirmation is available.
8. Continue transcript display even if diarization fails.

**Edge cases:** One speaker, more than two speakers, overlapping speech, diarization failure, low confidence, speaker changes mid-call.

**Acceptance criteria:**
- [ ] Speaker IDs are consistent within a call.
- [ ] Speaker order is not treated as role identity.
- [ ] Unknown role is supported.
- [ ] Diarization failure does not fabricate roles.
- [ ] Tone analysis is blocked or marked insufficient when representative identity is unresolved.

## Feature 6 — Tone analysis

**User story:** As a sales manager, I want to know whether the representative used a negative tone and why.

**Components:** Analysis service, Ollama local client, settings resolver, evidence model, result panel.

**Build order:**
1. Confirm representative speaker role.
2. Select only representative-attributed transcript segments.
3. Apply configured criteria (rude, hostile, dismissive, and approved additions).
4. Send transcript evidence and strict instructions to local Ollama.
5. Require schema-constrained JSON output.
6. Validate classification, explanation, and evidence references.
7. Verify evidence text exists in the stored transcript.
8. Store RED, GREEN, or INSUFFICIENT_EVIDENCE.
9. Display uncertainty clearly.

**Important semantic rules:**
- RED = negative representative communication supported by evidence.
- GREEN = no negative tone identified under the selected criteria after sufficient representative speech was evaluated.
- INSUFFICIENT_EVIDENCE = representative identity, transcript quality, or available speech is insufficient.
- Do not classify the customer's speech.
- Do not treat a negative business outcome as proof of negative tone.
- Do not invent confidence scores. Only store a confidence value if the chosen method defines and validates it.

**Edge cases:** Sarcasm, ambiguous wording, transcription errors, very short representative speech, customer-only recording, unknown role, malformed model output.

**Acceptance criteria:**
- [ ] Only representative speech is evaluated.
- [ ] Every RED result includes transcript-grounded evidence.
- [ ] GREEN is not used when evidence is insufficient.
- [ ] Evidence references valid transcript segments.
- [ ] Invalid LLM output is rejected or retried safely.
- [ ] Local Ollama is used; no paid API is called.

## Feature 7 — Action-item extraction

**User story:** As a sales manager, I want explicit commitments and follow-ups extracted from the call.

**Components:** Action extraction service, ActionItem and ActionItemEvidence models, action list UI.

**Build order:**
1. Analyze the transcript for explicit commitments and follow-ups.
2. Extract concise task descriptions.
3. Assign owner only when explicitly supported.
4. Assign deadline only when explicitly mentioned.
5. Preserve missing owner/deadline as null.
6. Link each item to one or more source transcript segments.
7. Validate evidence before persistence.
8. Display extracted items and unspecified fields.

**Edge cases:** Vague intent, conditional promise, customer request mistaken for representative commitment, multiple owners, relative dates without a known call date, duplicate commitments.

**Acceptance criteria:**
- [ ] Every action item has supporting transcript evidence.
- [ ] No owner is invented.
- [ ] No deadline is invented.
- [ ] Unsupported or speculative tasks are excluded.
- [ ] No-action-item calls display a clear empty state.

## Feature 8 — Call analysis results

**User story:** As a sales manager, I want all call analysis in one place.

**Components:** Call results page, tone status card, evidence cards, transcript viewer, action list, processing status.

**Build order:**
1. Fetch call metadata and processing state.
2. Fetch transcript and speaker data.
3. Fetch tone analysis and evidence.
4. Fetch action items.
5. Render each section independently.
6. Add loading, empty, partial, and error states.
7. Add transcript search if included in approved design.

**Acceptance criteria:**
- [ ] Results are associated with the correct call.
- [ ] RED/GREEN/INSUFFICIENT_EVIDENCE is text-labelled, not color-only.
- [ ] Evidence and model explanation are visually distinct.
- [ ] Partial results are not presented as complete.
- [ ] Timestamps are displayed consistently.

## Feature 9 — Call history and dashboard

**User story:** As a sales manager, I want to find and compare analyzed calls.

**Components:** Dashboard summary cards, call history table, search and filters.

**Build order:**
1. Implement paginated call listing.
2. Add filters for status and tone.
3. Add date sorting and search.
4. Calculate dashboard counts from database records.
5. Add empty and failed states.
6. Link each row to its call analysis.

**Acceptance criteria:**
- [ ] Counts are derived from stored data.
- [ ] Filters and pagination work together.
- [ ] Failed and incomplete jobs are distinguishable.
- [ ] No mock metrics are shown as real data.

## Feature 10 — Configurable analysis settings

**User story:** As a sales manager, I want to adjust tone criteria and action-item rules without changing code.

**Components:** Settings page, settings API, versioned settings record.

**Build order:**
1. Define allowed criteria and sensitivity values.
2. Retrieve current settings.
3. Build UI controls with descriptions.
4. Validate and persist updates.
5. Increment settings version.
6. Associate each new analysis with the settings version used.
7. Keep historical analysis unchanged.

**Acceptance criteria:**
- [ ] Settings can be changed in the UI.
- [ ] Invalid values are rejected.
- [ ] New analysis uses the saved version.
- [ ] Historical analysis retains its original settings reference.
- [ ] Defaults can be restored if the product specification includes reset.

## Feature 11 — Processing orchestration

**User story:** As a user, I want to see processing status while a call is analyzed.

**Components:** Background job runner, job status API, frontend status display.

**Build order:**
1. Create a job record when processing starts.
2. Prevent duplicate active jobs for the same call.
3. Execute validation, transcription, diarization, tone analysis, and action extraction in sequence.
4. Persist each stage's status.
5. Capture safe error details.
6. Support retry only for retryable failures.
7. Limit concurrency to one job for the 8 GB RAM target.

**Acceptance criteria:**
- [ ] Processing does not block normal API requests.
- [ ] Stage status reflects actual work.
- [ ] Failures are recorded.
- [ ] A retry does not duplicate completed records.
- [ ] No fabricated percentage progress is displayed.

## Feature implementation protocol

For each feature, the coding assistant must:
1. Read the source-of-truth documents.
2. Inspect existing files and tests.
3. List files to create or modify.
4. Implement only the selected feature.
5. Run targeted tests.
6. Run relevant regression tests.
7. Update documentation and `PLAN.md`.
8. Summarize actual changes and test results.
9. Stop and wait for user confirmation before starting the next feature.

## Definition of Done

A feature is done only when implementation, validation, error handling, tests, and documentation are complete. A visual mockup or hardcoded sample response does not count as a working feature.
