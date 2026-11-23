# Product Requirements Document: Sales Call Quality Analysis Agent

| | |
|---|---|
| **Project** | Sales Call Quality Analysis Agent |
| **Context** | ScaleWorks AI Forward Deployed Engineer take-home assessment |
| **Version** | 1.0 (MVP scope) |
| **Date** | 23 Nov 2026 |
| **Timebox** | 24-48 hours |
| **Status** | Draft for review. No application code written yet. |

---

## 1. Problem Statement and Business Objectives

### 1.1 Problem
Sales managers cannot listen to every customer call. Manual review is slow and inconsistent, and rude or dismissive behavior from a representative can go unnoticed until it costs a deal or a customer. Follow-up commitments made on calls are often forgotten because nobody writes them down reliably.

Existing AI call-analysis tools tend to be opaque. They produce scores without evidence, hide uncertainty, and can invent action items, owners, or deadlines. That makes managers distrust them.

### 1.2 Product Vision
A focused web application where a manager uploads a call recording and, within minutes, sees:
1. A clear **RED / GREEN** verdict on the sales representative's tone.
2. The exact transcript quotes and timestamps that justify the verdict.
3. A list of concrete action items, each tied to the line in the call that supports it.
4. Settings the manager can tune to match their team's standards, with no engineering involved.

### 1.3 Business Objectives
| # | Objective | Measure |
|---|---|---|
| O1 | Reduce manager time spent reviewing calls | Review time per call drops from the full call length to under 2 minutes |
| O2 | Surface problematic rep behavior quickly | RED calls are identified with evidence on first view |
| O3 | Improve follow-through on commitments | Action items are extracted and visible without re-listening |
| O4 | Build trust in AI output | 100% of evidence quotes verifiably exist in the transcript; zero fabricated owners or deadlines |
| O5 | Fit different team cultures | Managers adjust criteria and sensitivity without code changes |

---

## 2. Target Users and Personas

**Primary user:** Sales managers who review calls to coach reps and protect customer relationships.
**Secondary users:** Sales team leads, QA/compliance reviewers, and sales enablement staff.

### Persona 1: Priya, Sales Manager (primary)
- **Role:** Manages 8 inside-sales reps and has roughly 150 recorded calls per week she cannot all hear.
- **Goals:** Find calls where a rep was rude or dismissive. Make sure promised follow-ups happen.
- **Frustrations:** No time to listen to full calls. Distrusts black-box scores.
- **Needs:** Fast verdict, quoted proof, the ability to jump to the moment in the call.

### Persona 2: Marcus, Sales Enablement / QA Lead
- **Role:** Maintains the team's call-quality standards.
- **Goals:** Apply consistent criteria across reps. Tune what counts as "negative" for his industry (e.g., a blunt style may be acceptable in some contexts).
- **Frustrations:** Tools that cannot be configured and force one definition of "good."
- **Needs:** Editable tone criteria, sensitivity control, and a record of which settings produced which result.

### Persona 3: Dana, Sales Representative (indirect user)
- **Role:** Reviews her own calls with her manager during coaching.
- **Goals:** Understand fairly why a call was flagged. Recall commitments she made.
- **Frustrations:** Being judged by unexplained scores or for the customer's tone.
- **Needs:** Judgments based only on her own words, with context, and clear separation of AI interpretation from what was actually said.

---

## 3. Goals and Non-Goals

### 3.1 Goals
- **G1.** End-to-end flow: upload, transcribe, analyze, view, with every state visible.
- **G2.** Evidence-grounded tone classification of the **representative only**.
- **G3.** Action items that never include invented owners, deadlines, or hypothetical tasks.
- **G4.** Honest uncertainty: low-confidence states and failures are shown, never hidden or fabricated.
- **G5.** Meaningful in-app configuration that changes outputs.
- **G6.** Simple, modular, testable architecture, demonstrable within 48 hours.

### 3.2 Non-Goals (MVP)
- Real-time or live call analysis.
- Audio formats other than `.m4a` (e.g., `.mp3`, `.wav`).
- CRM integration, telephony integration, or automatic call ingestion.
- Multi-tenant user management, SSO, or role-based access control.
- Scoring customer sentiment or customer tone (explicitly out of scope).
- Coaching recommendations, rep scorecards, or cross-call trend analytics.
- Multi-language support beyond English.
- Emotion detection from vocal prosody (analysis is based on transcript text).
- Compliance certification (HIPAA, PCI, etc.).

---

## 4. Core Features

### 4.1 MVP (Must-Have)

| ID | Feature | Description |
|---|---|---|
| M1 | `.m4a` upload | Drag-and-drop and file picker. Shows progress and file details. |
| M2 | Audio validation | Checks extension, MIME type, container signature, size, duration, and decodability before spending any API cost. |
| M3 | Transcription | Readable transcript with timestamps (segment level at minimum). |
| M4 | Speaker identification | Speaker diarization where feasible. Assigns the "Sales Rep" and "Customer" roles with a visible confidence indicator. The user can swap roles with one click. |
| M5 | Tone analysis (rep only) | Binary RED/GREEN verdict, explanation, and a list of supporting evidence quotes with timestamps. |
| M6 | Evidence verification | Each quote is programmatically checked to exist verbatim in the transcript and to be attributed to the rep. Unverifiable evidence is discarded, and the user sees a notice. |
| M7 | Uncertainty handling | Confidence level (High / Medium / Low) is shown with the verdict. Insufficient evidence yields GREEN with a "limited evidence" note, never an unsupported RED. |
| M8 | Action-item extraction | Task text, owner (only if explicit), deadline (only if explicit), and supporting quote with timestamp. |
| M9 | Dashboard | Verdict banner, explanation, evidence list, transcript, and action items on one screen. Clicking evidence highlights it in the transcript. |
| M10 | Processing states and errors | Visible pipeline stages (Uploaded, Validating, Transcribing, Analyzing, Complete/Failed). Specific, actionable error messages. Retry on failure. |
| M11 | Call history | List of past analyses with filename, date, verdict, and status. Open any previous result. |
| M12 | Settings UI | Editable tone criteria, sensitivity (Low / Medium / High), action-item definition, and optional custom guidance. Persisted server-side. Applied to subsequent analyses. |
| M13 | Settings snapshot | Each analysis stores the settings used so results are explainable and reproducible. |
| M14 | Basic export | Download the analysis as JSON and as Markdown. |
| M15 | Secure key handling | All API keys are server-side only, loaded from environment variables. |

### 4.2 V2 (Should-Have)
| ID | Feature |
|---|---|
| V1 | Re-analyze an existing transcript with new settings without re-transcribing |
| V2 | Audio player synchronized with transcript (click a quote to play from that moment) |
| V3 | PDF export of the report |
| V4 | Settings presets (e.g., "Strict QA", "Relaxed", "Compliance") and reset-to-default |
| V5 | Side-by-side comparison of results under different settings |
| V6 | Edit and confirm action items (mark done, correct text), clearly marked as user-edited |
| V7 | Batch upload |
| V8 | Manager feedback on verdicts ("agree / disagree") to measure accuracy over time |

### 4.3 Later (Nice-to-Have)
- Per-rep trends and team dashboards.
- Prosody-aware tone analysis from audio (volume, interruptions, pace).
- Multi-language support.
- CRM / calendar integration to push action items.
- Additional audio formats and direct integration with call-recording platforms.
- Role-based access and team workspaces.
- Automated PII redaction.

---

## 5. User Stories

### Upload and Processing
- As a sales manager, I want to upload an `.m4a` recording by drag-and-drop, so that I can start an analysis in seconds.
- As a sales manager, I want to be told immediately if my file is invalid, too large, too long, or corrupted, so that I do not wait for a result that will never arrive.
- As a sales manager, I want to see which processing stage my call is in, so that I know it is working and roughly how long it will take.
- As a sales manager, I want to retry a failed analysis without re-uploading, so that temporary service errors do not waste my time.

### Transcript and Speakers
- As a sales manager, I want a readable transcript with timestamps and speaker labels, so that I can follow the conversation.
- As a sales manager, I want to swap which speaker is the rep if it was guessed wrong, so that the tone analysis targets the right person.
- As a sales manager, I want to be warned when speaker separation is uncertain, so that I do not over-trust the result.

### Tone Evaluation
- As a sales manager, I want a clear RED or GREEN indicator for the rep's tone, so that I can triage calls at a glance.
- As a sales manager, I want exact quotes and timestamps supporting the verdict, so that I can verify it myself.
- As a sales manager, I want the tone judged only on the rep's words, so that an angry customer does not unfairly cause a RED.
- As a sales manager, I want the app to say when evidence is thin, so that I am not misled by overconfident AI claims.
- As a rep, I want AI interpretation visually separated from my actual words, so that I can fairly dispute or accept the finding.

### Action Items
- As a sales manager, I want a list of concrete commitments and follow-ups from the call, so that nothing promised is forgotten.
- As a sales manager, I want owners and deadlines shown only when explicitly stated, so that I never act on invented details.
- As a sales manager, I want each action item linked to its supporting quote, so that I can confirm it was really said.

### Settings
- As a QA lead, I want to edit what counts as negative tone, so that the app matches my team's standards.
- As a QA lead, I want a sensitivity setting, so that I can choose between strict and lenient flagging.
- As a QA lead, I want to define what qualifies as an action item, so that casual remarks are excluded.
- As a QA lead, I want each result to record the settings used, so that I can explain why two calls were judged differently.

### History and Export
- As a sales manager, I want to reopen past analyses, so that I can revisit calls during coaching.
- As a sales manager, I want to export a result, so that I can share it with a rep or attach it to a coaching note.

---

## 6. Complete User Workflows

### 6.1 Upload an Audio Recording
1. User opens the Upload view and drags in or selects an `.m4a` file.
2. The client performs instant checks (extension, size). Failures show an inline error without upload.
3. The file uploads with a progress indicator. The server returns a call ID, and the call appears in History with status **Uploaded**.
4. The user may start the analysis (or it starts automatically). A short summary of the active settings (e.g., "Sensitivity: Medium") is shown so the user knows what will be applied.

### 6.2 Audio Validation and Processing
Server-side, in order, stopping at the first failure:
1. **Type check:** extension `.m4a`, MIME `audio/mp4` or `audio/x-m4a`, and MP4/`ftyp` container signature (not just the filename).
2. **Size check:** within the configured maximum (default 50 MB).
3. **Integrity check:** the file can be decoded and probed (e.g., ffprobe). Corrupted or DRM-protected files are rejected.
4. **Duration check:** within the configured range (default 10 seconds to 30 minutes).
5. **Audio presence check:** not silent or near-silent.

On failure: status **Failed (Validation)** with a specific message (e.g., "File is 74 MB; the limit is 50 MB") and no paid API call is made. On success, status moves to **Transcribing**.

### 6.3 Transcription and Speaker Identification
1. The server sends audio to the transcription service (converting format if the provider requires it).
2. The response is normalized into segments: `{speaker, start, end, text}`.
3. Speaker roles are assigned:
   - Diarization labels (Speaker A/B) are mapped to **Sales Rep** and **Customer** by a role-inference step that uses conversational cues (e.g., who introduces the company, who asks discovery questions).
   - The result carries a role-confidence value. Below the threshold, the UI shows a visible warning and prompts the user to confirm roles.
4. If diarization is unavailable or yields one speaker, the transcript is shown without speaker labels, a warning appears, and the tone analysis proceeds only if the user identifies rep speech (otherwise it is marked "cannot attribute to rep" rather than guessing).
5. On transcription failure, the status is **Failed (Transcription)** with a retry button. The transcript is never fabricated.

### 6.4 Sales Representative Tone Evaluation
1. Only rep-attributed segments (with surrounding customer lines as read-only context) are sent to the analysis model.
2. The prompt is built from the user's settings: tone criteria, sensitivity, and custom guidance.
3. The model returns structured output: verdict, confidence, explanation, and evidence items (quote, timestamp, category, severity).
4. **Decision rule:** RED only when the evidence meets the configured threshold for the selected sensitivity (see FR-T5). Otherwise GREEN.
5. The customer's tone, however negative, never contributes to the verdict.

### 6.5 Evidence Extraction and Verification
1. Each evidence quote is matched against the transcript (normalized for whitespace and punctuation).
2. The quote must (a) appear verbatim, (b) belong to a rep-attributed segment, and (c) carry a timestamp resolved from the transcript, not from the model.
3. Evidence that fails any check is dropped and logged. If dropping evidence removes the basis for a RED, the verdict is re-evaluated or downgraded with a visible "evidence could not be verified" notice.
4. The UI labels two distinct kinds of content: **"From the transcript"** (verbatim quote) and **"AI interpretation"** (explanation).

### 6.6 Action-Item Identification
1. The analysis model extracts candidate commitments and follow-ups from the whole conversation, applying the user's action-item definition.
2. For each item the model returns: task, owner (nullable), deadline (nullable), supporting quote, and the speaker who made the commitment.
3. Verification: the quote must exist verbatim; the owner must appear in or be directly implied by the quote's speaker role; the deadline must be present in the quote text. Otherwise the field is set to "Not specified."
4. Hypothetical or conditional statements ("maybe I could...", "if you want, we might...") are excluded unless the user's settings explicitly include them.
5. If none are found, the UI says "No action items identified."

### 6.7 Viewing and Exporting Results
1. When the status reaches **Complete**, the Dashboard opens with: verdict banner (RED/GREEN + confidence), explanation, evidence cards, action items, and the full transcript.
2. Clicking an evidence card or action item scrolls to and highlights the quote in the transcript.
3. The Settings Snapshot panel shows the settings used for this analysis.
4. **Export:** the user chooses JSON or Markdown. The export includes the verdict, explanation, evidence, transcript, action items, settings snapshot, and generation timestamp.

### 6.8 Adjusting Analysis Settings
1. User opens Settings and sees the current configuration.
2. They can edit:
   - **Tone criteria:** list of behaviors that count as negative (rude, hostile, dismissive, etc.), each toggleable, with the ability to add custom criteria in plain language.
   - **Sensitivity:** Low / Medium / High.
   - **Action-item definition:** toggles (include verbal commitments, scheduled follow-ups, information promised, tasks for customer) and custom guidance text.
   - **Custom guidance:** optional free text (e.g., "Brisk, direct language is acceptable in this team").
3. Inline helper text explains each option; input is validated (length limits, non-empty criteria).
4. Saving applies the settings to **subsequent** analyses. A clear notice states that past results are unchanged.
5. Reset-to-defaults is available.

---

## 7. Functional Requirements

### 7.1 Upload and Validation
| ID | Requirement |
|---|---|
| FR-U1 | The system shall accept only `.m4a` files and reject all others with a clear message. |
| FR-U2 | The system shall validate extension, MIME type, and file signature server-side. |
| FR-U3 | The system shall enforce configurable max file size (default 50 MB) and duration (default 10 s to 30 min). |
| FR-U4 | The system shall verify the audio can be decoded and is not silent before transcription. |
| FR-U5 | Validation failures shall not trigger paid external API calls. |
| FR-U6 | Uploaded files shall be stored with generated IDs, not user-supplied filenames, on disk or storage. |

### 7.2 Transcription and Speakers
| ID | Requirement |
|---|---|
| FR-S1 | The system shall produce a transcript with segment-level timestamps. |
| FR-S2 | The system shall attempt speaker diarization and label segments by speaker. |
| FR-S3 | The system shall infer which speaker is the sales rep and expose a confidence value. |
| FR-S4 | The user shall be able to swap or manually assign rep/customer roles; doing so shall allow re-running the analysis. |
| FR-S5 | If diarization fails, the system shall show an unlabeled transcript with a warning and shall not fabricate speaker attribution. |
| FR-S6 | Transcription errors (timeout, provider error, unsupported audio) shall result in a Failed status with a retry option. |

### 7.3 Tone Analysis
| ID | Requirement |
|---|---|
| FR-T1 | The system shall evaluate only the sales representative's utterances. Customer text is context only. |
| FR-T2 | The system shall output exactly one verdict: RED or GREEN. |
| FR-T3 | The system shall return an explanation and at least one evidence item for every RED verdict. |
| FR-T4 | Each evidence item shall include a verbatim quote, speaker, timestamp, and criterion matched. |
| FR-T5 | RED shall require evidence that meets the sensitivity threshold: **Low** = at least one clear, severe instance (e.g., hostility, insults); **Medium** = one clear instance or repeated milder instances; **High** = any identifiable instance of a configured criterion. |
| FR-T6 | The system shall report confidence (High / Medium / Low) and shall flag limited evidence (e.g., very short rep speech, uncertain speaker attribution). |
| FR-T7 | A GREEN verdict shall include a brief explanation (e.g., "No behaviors matching the configured criteria were found") and shall not claim positive traits it cannot support. |
| FR-T8 | Every evidence quote shall be verified against the transcript; unverified quotes shall be excluded. |
| FR-T9 | The model shall be instructed to quote and not paraphrase, and to consider context so that professional firmness is not misclassified as rudeness. |

### 7.4 Action Items
| ID | Requirement |
|---|---|
| FR-A1 | The system shall extract commitments and follow-ups according to the user's action-item definition. |
| FR-A2 | Each action item shall include task text and a supporting verbatim quote with timestamp. |
| FR-A3 | Owner shall be populated only when explicitly stated or unambiguously attributable to the committing speaker's role; otherwise "Not specified." |
| FR-A4 | Deadline shall be populated only when explicitly stated in the transcript; relative dates ("next Friday") are shown as stated and never converted to inferred calendar dates. |
| FR-A5 | The system shall not generate hypothetical, suggested, or inferred action items. |
| FR-A6 | The system shall show an explicit empty state when no action items are found. |

### 7.5 Dashboard and History
| ID | Requirement |
|---|---|
| FR-D1 | The dashboard shall show the verdict indicator, confidence, explanation, evidence, transcript, and action items. |
| FR-D2 | The UI shall visually distinguish verbatim transcript content from AI-generated interpretation. |
| FR-D3 | The UI shall show the processing stage and handle loading, empty, partial-failure, and error states. |
| FR-D4 | Selecting evidence or an action item shall highlight the corresponding transcript line. |
| FR-D5 | The system shall persist analyses and list them in a History view with status, date, filename, and verdict. |
| FR-D6 | Users shall be able to open, and delete, previous analyses. |
| FR-D7 | The system shall support export to JSON and Markdown. |

### 7.6 Settings
| ID | Requirement |
|---|---|
| FR-C1 | The system shall provide an in-app Settings page with editable tone criteria, sensitivity, and action-item definition. |
| FR-C2 | Settings shall be persisted server-side and applied to all subsequent analyses. |
| FR-C3 | Each analysis shall store an immutable snapshot of the settings used. |
| FR-C4 | Settings changes shall demonstrably affect output (e.g., the same transcript can flip from GREEN to RED when moving from Low to High sensitivity). |
| FR-C5 | Setting inputs shall be validated and sanitized, including length limits to mitigate prompt injection and cost abuse. |
| FR-C6 | The system shall provide sensible defaults and a reset-to-defaults action. |

### 7.7 Error Handling and Integrity
| ID | Requirement |
|---|---|
| FR-E1 | When any external service fails, the system shall show the failure and shall not generate substitute or placeholder analysis. |
| FR-E2 | Errors shall be specific and actionable (what failed, what the user can do). |
| FR-E3 | Transient failures shall be retried automatically with bounded backoff, and the user shall have a manual retry. |
| FR-E4 | Model output shall be validated against a strict schema. Malformed output triggers one retry and then a Failed (Analysis) state. |
| FR-E5 | Partial results shall be preserved (e.g., if transcription succeeds and analysis fails, the transcript remains viewable and analysis can be retried). |

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Accuracy and reliability** | Evidence quote validity of 100% (programmatically enforced). Zero fabricated owners or deadlines on the test set. Tone verdict deterministic enough that repeated runs on the same input agree at least 90% of the time (low temperature, structured output). |
| **Performance** | Median end-to-end processing under 2 minutes for a 5-minute call. UI remains responsive during processing, with status updates at least every few seconds (polling or server-sent events). |
| **Usability** | A first-time user can complete upload-to-result without instructions. Core flow works on current desktop Chrome, Safari, and Firefox. Responsive layout for tablet widths. |
| **Accessibility** | RED/GREEN indicated by text and icon, not color alone. Keyboard-navigable and WCAG AA contrast targeted. |
| **Security** | API keys only in server environment variables, never sent to the client or committed. File uploads sanitized and size-limited. Basic rate limiting. Uploaded audio stored with generated names. |
| **Privacy** | Only consented or synthetic recordings are used. Provide a delete function removing audio, transcript, and analysis. The README discloses which third-party services receive the audio and transcript. |
| **Maintainability** | Modular pipeline (validation, transcription, role assignment, analysis, verification), with each stage behind an interface so providers can be swapped. Typed schemas for all stage inputs and outputs. |
| **Testability** | Evidence verification, validation, and settings-to-prompt logic are pure, unit-testable functions. Provider calls are mockable. A fixture-based reliability test set is included. |
| **Observability** | Structured logs per call ID with stage timings and error codes (no transcript content in logs by default). |
| **Portability** | Runs locally with a documented setup of under 10 minutes, and deployable to a single host for the demo. |

---

## 9. Success Metrics and Acceptance Criteria

### 9.1 Success Metrics
| Metric | Target |
|---|---|
| Tone verdict agreement with human labels on the test set | 85% or higher (target 100% on the two required demo calls) |
| False-RED rate on professional calls | 10% or lower |
| Evidence validity (quotes verifiably in transcript and attributed to rep) | 100% |
| Fabricated owner or deadline occurrences | 0 |
| Action-item precision (items judged valid by reviewer) | 90% or higher |
| Action-item recall on clearly stated commitments | 80% or higher |
| Median processing time (5-minute call) | Under 2 minutes |
| Invalid-input handling | 100% of invalid test files rejected with a specific message |
| Settings impact | At least one test transcript changes verdict or action items when settings change |
| Task completion | Reviewer can go from upload to understanding the result in under 3 minutes |

### 9.2 Acceptance Criteria (MVP)

**Audio processing**
- [ ] Given a valid `.m4a`, a transcript with timestamps is displayed.
- [ ] Given a `.mp3` renamed to `.m4a`, a corrupted `.m4a`, an oversized file, or a silent file, the app rejects it with a specific message and makes no transcription call.
- [ ] Given a transcription provider failure, the app shows an error and a retry option and displays no invented transcript.

**Tone analysis**
- [ ] The RED demo call returns RED with at least one verified evidence quote from the rep and a timestamp.
- [ ] The GREEN demo call returns GREEN with an explanation and no unsupported claims.
- [ ] A call with a hostile customer and a professional rep returns GREEN.
- [ ] A call with very little rep speech shows limited-evidence or low-confidence messaging.
- [ ] No evidence quote appears that is absent from the transcript.

**Action items**
- [ ] Each item shows task, supporting quote, and timestamp.
- [ ] Owner and deadline display "Not specified" when not stated.
- [ ] Hypothetical statements are not listed as commitments (under default settings).

**Dashboard**
- [ ] Verdict, explanation, evidence, transcript, and action items are visible on one view.
- [ ] Processing stages, loading states, and errors are displayed.
- [ ] Past analyses can be listed and reopened after a page refresh.
- [ ] Verbatim quotes and AI interpretation are visually distinguishable.

**Settings**
- [ ] Editing criteria, sensitivity, and action-item definition from the UI changes subsequent analysis behavior with no code change or restart.
- [ ] Each result displays the settings snapshot it used.

**Delivery**
- [ ] README covers setup, tools, assumptions. Two test recordings (RED and GREEN) and their transcripts are included. Design-decisions note, known limitations, and reliability-testing documentation are included. No API keys in the repository.

---

## 10. Risks, Assumptions, Dependencies, and Open Questions

### 10.1 Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| LLM hallucinates evidence, owners, or deadlines | High: breaks trust and the accuracy criterion | Strict structured output, programmatic verbatim verification, null-by-default fields, drop unverifiable items |
| Diarization is wrong or role inference mislabels the rep | High: customer tone could be blamed on the rep | Role confidence, warning UI, one-click role swap, attribution only to rep-labeled text |
| Tone is subjective, so professional firmness is flagged as rude (or the reverse) | High | Configurable criteria and sensitivity, context-aware prompts, confidence display, evidence the manager can judge |
| Text-only analysis misses sarcasm and vocal tone | Medium | Disclose the limitation; prosody analysis deferred to Later |
| Third-party outage, rate limits, or latency | Medium | Retries with backoff, clear failure states, partial-result preservation, provider abstraction |
| Prompt injection via transcript content or custom settings text | Medium | Delimited input, instruction hierarchy, schema validation, settings length limits |
| Test audio quality or availability (synthetic recordings sound unnatural) | Medium | Use text-to-speech with two distinct voices or consenting volunteers; include a script and transcript for reproducibility |
| Scope creep beyond 48 hours | High | Strict MVP list, V2 items deferred, no auth or multi-tenant work |
| Privacy of audio sent to third parties | Medium | Synthetic or consented audio only, documented data flow, delete function |
| Cost overrun from large files | Low | Validation before API calls, size and duration caps |

### 10.2 Assumptions
1. English-language calls, two speakers (one rep, one customer).
2. Recordings are mono or stereo single-file `.m4a`, with duration up to 30 minutes.
3. A single-user demo environment is acceptable (no login) as the assessment does not require authentication.
4. A third-party transcription service with diarization and an LLM API with structured output are available to the candidate.
5. "Negative tone" is judged from transcript text and conversational context, not audio prosody.
6. The binary RED/GREEN verdict is mandatory. Uncertainty is conveyed through a separate confidence indicator and notes and never through a third verdict color.
7. Settings are global (one active configuration) rather than per-user or per-team.
8. The two demo recordings are synthetic or consented, and ideally created from scripts the candidate controls.
9. Relative deadlines ("by Friday") are shown verbatim and not resolved to calendar dates.

### 10.3 Dependencies
- Speech-to-text provider with diarization and timestamps (candidates include AssemblyAI, Deepgram, or OpenAI transcription models).
- LLM provider with structured/JSON-schema output for tone and action-item analysis.
- ffmpeg / ffprobe for integrity and duration checks (and format conversion if required).
- Persistent storage (SQLite or equivalent) for calls, results, and settings.
- Hosting for the demo, plus environment-variable secret management.

### 10.4 Open Questions
| # | Question | Default if unanswered |
|---|---|---|
| Q1 | Which transcription and LLM providers and API keys are available? | Provider-agnostic design; pick one diarization-capable STT provider and one LLM with JSON-schema output |
| Q2 | Is authentication required, or is a single-user demo acceptable? | No auth; single global settings profile |
| Q3 | How will the demo be delivered (hosted URL vs. local run with instructions)? | Both: local setup documented and a hosted instance if time allows |
| Q4 | Will the RED/GREEN test calls be recorded by you with consent, or generated via text-to-speech? | Scripted calls generated with two distinct TTS voices, with scripts and expected verdicts documented |
| Q5 | Should a low-confidence result still return a hard RED/GREEN, or should the UI lead with the uncertainty? | Always return RED or GREEN as the spec requires, with confidence and a limited-evidence banner shown prominently |
