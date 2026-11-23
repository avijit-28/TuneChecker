# TESTING.md — Quality and Reliability Test Plan

## 1. Objectives

Verify that the Sales Call Quality Analysis Agent:
- Accepts and validates `.m4a` audio.
- Produces readable transcripts.
- Distinguishes speakers where feasible.
- Evaluates only the confirmed sales representative.
- Produces evidence-grounded RED/GREEN outcomes.
- Preserves insufficient evidence.
- Extracts only concrete commitments and follow-ups.
- Does not invent owners or deadlines.
- Allows user-controlled analysis settings.
- Works without paid inference APIs.

## 2. Test levels and tools

| Level | Tool | Purpose |
|---|---|---|
| Unit | Pytest | Functions, schemas, validators, services |
| API | FastAPI TestClient / HTTPX | Endpoint behavior |
| Integration | Pytest fixtures | SQLite and local service adapters |
| Frontend | Vitest + React Testing Library, if selected | UI states and interactions |
| End-to-end | Playwright, if selected | Complete upload-to-results flow |
| Manual | Browser + synthetic recordings | Usability and demo readiness |

Use the test tools actually installed in the project. Do not claim a tool is configured before adding it.

## 3. Test data and privacy

Use synthetic or consented recordings only. Create at least:
- One RED example with clearly negative representative communication.
- One GREEN example with professional representative communication.
- One ambiguous/insufficient-evidence example.
- One customer-negative / representative-professional example.
- One audio file with multiple speakers.

Label all synthetic fixtures clearly. Do not represent them as real customer calls.

## 4. Audio upload tests

| ID | Scenario | Input | Expected |
|---|---|---|---|
| AUD-01 | Valid M4A | Valid short recording | Accepted and stored |
| AUD-02 | Wrong extension | PDF renamed `.m4a` | Rejected |
| AUD-03 | Empty file | 0-byte file | Rejected |
| AUD-04 | Oversized file | Above configured limit | Rejected |
| AUD-05 | Corrupt audio | Invalid media bytes | Rejected with safe error |
| AUD-06 | Duplicate filename | Two files with same name | Both stored with distinct generated names |
| AUD-07 | Path traversal | Filename contains `../` | Storage remains inside approved directory |
| AUD-08 | Silent audio | Valid silence | No fabricated transcript |

## 5. Transcription tests

- [ ] Speech produces non-empty transcript.
- [ ] Empty/silent recording is handled.
- [ ] Segment start/end values are valid.
- [ ] Segment order is stable.
- [ ] Language metadata is stored when available.
- [ ] Transcription provider/model metadata is recorded.
- [ ] Model unavailable is handled.
- [ ] CUDA failure triggers configured fallback or clear failure.
- [ ] Long recording does not exhaust memory silently.

Avoid asserting exact transcription wording for every model run unless the fixture and expected transcript are tightly controlled. Use phrase-level or semantic checks where appropriate.

## 6. Speaker diarization tests

- [ ] One-speaker audio produces one speaker or a documented uncertainty state.
- [ ] Two-speaker audio yields distinguishable turns where feasible.
- [ ] Speaker IDs remain consistent.
- [ ] Transcript-to-speaker mapping uses temporal overlap.
- [ ] Speaker order is not interpreted as sales/customer role.
- [ ] Unknown role is supported.
- [ ] Diarization failure preserves transcript.
- [ ] Overlapping speech is handled without fabricated certainty.

## 7. Tone classification tests

| ID | Scenario | Expected |
|---|---|---|
| TONE-01 | Representative clearly rude/hostile | RED with exact representative evidence |
| TONE-02 | Representative professional | GREEN if sufficient evidence |
| TONE-03 | Customer is rude; representative is professional | Must not become RED due to customer speech |
| TONE-04 | Representative identity unknown | INSUFFICIENT_EVIDENCE |
| TONE-05 | Very short/unclear representative speech | INSUFFICIENT_EVIDENCE where appropriate |
| TONE-06 | LLM returns invalid JSON | Rejected; no successful analysis record |
| TONE-07 | Evidence quote not in transcript | Rejected |
| TONE-08 | Settings sensitivity changes | New analysis uses new settings version |

Every RED test must verify that evidence references real transcript segments assigned to the representative. Do not rely solely on the LLM's self-reported confidence.

## 8. Action-item tests

| ID | Scenario | Expected |
|---|---|---|
| ACT-01 | Explicit promise with owner and date | Extract supported fields |
| ACT-02 | Promise with no named owner | Owner is null |
| ACT-03 | Promise with no deadline | Deadline is null |
| ACT-04 | Customer asks for a task; no commitment made | Do not invent representative commitment |
| ACT-05 | Vague possibility only | Exclude or mark as unconfirmed according to product rules |
| ACT-06 | Evidence missing | Do not persist as a valid extracted action |
| ACT-07 | Duplicate mention | Avoid duplicate action items where clearly same commitment |

## 9. Settings tests

- [ ] Default settings load.
- [ ] Valid criteria can be saved.
- [ ] Invalid sensitivity is rejected.
- [ ] Action-item rules are persisted.
- [ ] Settings version increments.
- [ ] Historical analysis retains its original settings version.
- [ ] New analysis uses current settings.

## 10. API and database tests

Test:
- Correct HTTP status codes.
- Invalid request schemas.
- Missing call IDs.
- Invalid status transitions.
- Pagination and filtering.
- Foreign key integrity.
- Duplicate active job prevention.
- Delete-call cascade/retention behavior.
- Unauthorized access if authentication is implemented.
- SQLite lock/error behavior.

Use a temporary test database. Never run destructive tests against real user data.

## 11. End-to-end scenarios

### E2E-01 — RED call
1. Upload synthetic RED `.m4a`.
2. Verify audio validation.
3. Wait for transcription.
4. Verify diarization and representative role confirmation.
5. Run tone analysis.
6. Verify RED result and evidence.
7. Verify action items and evidence.
8. Reload page and confirm results persist.

### E2E-02 — GREEN call
Repeat the flow with a professional representative recording. Verify GREEN only when the representative speech is sufficiently available and no configured negative tone is supported.

### E2E-03 — Insufficient evidence
Upload a call where representative identity cannot be established. Verify the result is not incorrectly shown as GREEN.

### E2E-04 — Local service unavailable
Stop Ollama or make a model unavailable. Verify the job fails or becomes partial with a useful error and no fabricated analysis.

## 12. Reliability and assessment alignment

ScaleWorks assessment weighting:
- Accuracy & Reliability: 40%.
- User Experience: 30%.
- Configurability: 30%.

Prioritize tests in that order:
1. Speaker-role correctness and evidence grounding.
2. Action-item factuality.
3. Error and uncertainty handling.
4. Upload-to-results usability.
5. Settings persistence and effect on new analyses.

Do not claim a numeric accuracy score unless a labelled evaluation set and reproducible calculation exist. Report sample size, test procedure, and known limitations.

## 13. Commands

Use commands matching the actual repository. Typical backend command:

```powershell
pytest -q
```

Frontend commands depend on `package.json`, for example:

```powershell
npm test
```

Do not invent test scripts. Add them explicitly to package configuration before documenting them.

## 14. Release checklist

- [ ] RED synthetic call passes.
- [ ] GREEN synthetic call passes.
- [ ] Insufficient-evidence test passes.
- [ ] Customer tone is not attributed to representative.
- [ ] Evidence references valid transcript segments.
- [ ] No unsupported owners or deadlines.
- [ ] Upload validation passes.
- [ ] Local-only integrations verified.
- [ ] No paid API calls.
- [ ] Known limitations documented.
- [ ] Test commands and actual results recorded.
