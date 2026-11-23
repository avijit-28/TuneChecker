# DEBUGGING.md — Systematic Debugging Playbook

## 1. Objective

Diagnose failures in the Sales Call Quality Analysis Agent without guessing, broad rewrites, or unrelated changes.

## 2. Required information

Before debugging, collect:
- Full error message and traceback.
- Command used.
- Steps immediately before the failure.
- Expected behavior.
- Actual behavior.
- Operating system.
- Python and Node versions.
- GPU model, VRAM, and `nvidia-smi` output if relevant.
- Relevant sanitized logs.
- Relevant source files and test output.

Never paste API tokens, Hugging Face tokens, passwords, private recordings, or sensitive transcripts into issue reports.

## 3. Mandatory debugging workflow

1. Read the full error and identify the failing layer.
2. Inspect the relevant code and source-of-truth documents.
3. List the three most likely root causes, ranked by evidence.
4. Propose a command, log, or test to confirm the leading cause.
5. Do not modify code until the cause is reasonably confirmed.
6. Make the smallest scoped fix.
7. Add or update a regression test.
8. Run targeted tests, then relevant regression tests.
9. Update documentation if behavior or setup changed.
10. Report changed files and actual test results.

If evidence is insufficient, ask for the missing information instead of guessing.

## 4. Common failure areas

### A. FFmpeg not found
Checks:
```powershell
where.exe ffmpeg
ffmpeg -version
```
Likely causes: PATH not updated, wrong install directory, terminal not restarted. Fix PATH and reopen the shell. Do not bypass media validation.

### B. NVIDIA GPU not detected
Checks:
```powershell
nvidia-smi
```
Then:
```powershell
python -c "import torch; print(torch.cuda.is_available())"
```
Likely causes: driver issue, CPU-only PyTorch build, incompatible runtime. Verify the official compatibility instructions for the installed package. Keep CPU fallback.

### C. Faster-Whisper CUDA/cuDNN error
Check installed CTranslate2 version and its documented CUDA/cuDNN requirements. Do not assume PyTorch CUDA success proves CTranslate2 compatibility. Test a minimal CPU `int8` transcription to isolate the issue.

### D. Out-of-memory
- Stop concurrent analysis jobs.
- Close memory-heavy applications.
- Use Whisper `base`.
- Use CPU `int8` if needed.
- Keep Ollama context bounded.
- Run models sequentially.
- Capture RAM/VRAM before and after each stage.
Do not claim a memory leak without measurements.

### E. Hugging Face / pyannote access denied
Check:
- User accepted the current model access conditions.
- Token is valid and has required read access.
- Token is loaded by the backend process.
- Model identifier is exact.
Do not print the token. If diarization cannot run, preserve transcript and mark speaker role unknown.

### F. Ollama connection refused
Checks:
```powershell
ollama list
Invoke-RestMethod http://localhost:11434/api/tags
```
Start Ollama and verify the configured host/port. Check firewall only if there is evidence of a network issue.

### G. Ollama model not found
Check exact tag:
```powershell
ollama list
```
Pull the configured model if missing. Ensure `.env` model name matches the installed tag.

### H. Invalid LLM JSON
- Save a sanitized copy of the response in development logs.
- Check prompt and schema.
- Reduce output scope or transcript chunk size.
- Use JSON/schema mode only if supported by the selected runtime/model.
- Validate with Pydantic.
Never persist malformed output as a successful analysis.

### I. Incorrect RED/GREEN result
Inspect:
1. Which speaker segments were passed to the model?
2. Was the representative role confirmed?
3. Were customer segments excluded?
4. Which settings version was used?
5. Does each evidence ID resolve to an actual transcript segment?
6. Is the transcript accurate enough?
Do not fix a classification by hardcoding a phrase list without a documented test and product decision.

### J. Hallucinated action item
Trace the action item to its transcript segment. Reject unsupported tasks. Verify owner and deadline are nullable. Add a regression test for the exact failure.

### K. SQLite database locked
Inspect concurrent writers and transaction duration. Keep transactions short, avoid holding a transaction while waiting for model inference, and ensure each job updates state safely.

### L. Frontend cannot reach backend
Check:
- Backend process and port.
- Vite API base URL.
- Browser network error.
- CORS allowed origin.
- Endpoint path and HTTP method.
Do not use wildcard CORS with credentials as a shortcut.

### M. Upload fails
Check file size, request content type, multipart field name, configured size limit, storage permissions, and FFprobe output. Verify the backend generated a safe filename.

## 5. Regression tests required after fixes

At minimum, rerun tests for the affected feature and its downstream dependencies:
- Upload fix → upload validation and processing initiation.
- Transcription fix → segment schema and transcript display.
- Diarization fix → speaker mapping and representative-only analysis.
- Tone fix → RED, GREEN, insufficient evidence, evidence references.
- Action-item fix → evidence, null owner, null deadline.
- Settings fix → versioning and new-analysis behavior.
- Storage/database fix → persistence and deletion behavior.

## 6. Debug report template

```text
## Bug title

### Error message
[Paste sanitized full error]

### Steps to reproduce
1.
2.
3.

### Expected behavior

### Actual behavior

### Environment
- Windows:
- Python:
- Node:
- GPU:
- VRAM:

### Relevant files

### Root cause
[Confirmed cause, or state that it is not yet confirmed]

### Minimal fix

### Regression test

### Verification
[Exact commands and actual results]

### Remaining limitations
```

## 7. Rules

- Do not guess.
- Do not rewrite large parts of the code.
- Do not change architecture to hide a bug.
- Do not remove validation to make a test pass.
- Do not log secrets or sensitive recordings.
- Do not claim tests passed unless they were executed.
- Keep the fix limited to the confirmed issue.
