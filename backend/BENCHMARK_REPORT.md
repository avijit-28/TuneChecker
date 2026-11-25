# TuneChecker Transcription Benchmark Report

- **Generated (UTC)**: 2026-11-25T05:27:46Z
- **Execution Mode**: `mock`
- **Local Engine**: `faster-whisper:large-v3-turbo` (`language_mode=english`)
- **Cloud Reference Engine**: `gemini-4-hydrogen`
- **Gemini API Key Configured**: `no`

## Tier A: Faster-Whisper vs. Human/TTS Ground Truth (`samples/`)

| Sample | Verdict | Duration (s) | Engine | Status | Latency (s) | RTF (proc/audio) | Speed (audio/proc) | Throughput (WPS) | WER (%) | CER (%) | S / D / I | Accuracy (%) |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `green_call_01` | GREEN | 55.63 | `faster-whisper:large-v3-turbo` | `ok` | 7.788 | 0.14x | 7.14x | 17.21 | 2.94% | 0.51% | 2 / 2 / 0 | 97.06% |
| `green_call_01` | GREEN | 55.63 | `gemini-4-hydrogen` | `ok` | 2.225 | 0.04x | 25.0x | 61.12 | 0.0% | 0.0% | 0 / 0 / 0 | 100.0% |
| `red_call_01` | RED | 55.70 | `faster-whisper:large-v3-turbo` | `ok` | 7.798 | 0.14x | 7.14x | 16.67 | 3.05% | 1.11% | 3 / 1 / 0 | 96.95% |
| `red_call_01` | RED | 55.70 | `gemini-4-hydrogen` | `ok` | 2.228 | 0.04x | 25.0x | 58.8 | 0.0% | 0.0% | 0 / 0 / 0 | 100.0% |

**Tier A Local Corpus Aggregate (2 calls, 111.33s audio):** WER **3.0%**, CER **0.8%**, Accuracy **97.0%**, S/D/I = `5/3/0`, RTF `0.14x`, Speed `7.14x`, Throughput `16.94 WPS`.
**Tier A Gemini Corpus Aggregate (2 calls):** WER **0.0%**, CER **0.0%**, Accuracy **100.0%**, RTF `0.04x`, Speed `25.0x`, Throughput `59.96 WPS`.

## Tier B: Cross-Model Benchmark on `datahiveai/english-conversations-sample`

*Note: `datahiveai/english-conversations-sample` does not ship human transcripts; Tier B measures cross-model divergence treating Gemini output as reference.*

| Audio File | Topic | Duration (s) | Whisper Words | Whisper Latency (s) | Whisper RTF | Whisper Speed | Whisper WPS | Gemini Status | Cross-Model WER (%) | Cross-Model CER (%) | S / D / I |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `en_000001.mp3` | business_finance | 389.04 | 46 | 85.589 | 0.22x | 4.55x | 0.54 | `ok` | 4.26% | 2.36% | 1 / 1 / 0 |
| `en_000002.mp3` | business_finance | 666.58 | 35 | 146.647 | 0.22x | 4.55x | 0.24 | `ok` | 8.33% | 1.22% | 2 / 1 / 0 |

### Speed, Throughput & Cost Comparison

| Dimension | TuneChecker Local (`faster-whisper`) | Gemini Cloud (`gemini-4-hydrogen`) |
| :--- | :---: | :---: |
| **Total Audio Duration** | 1055.62s | 1055.62s |
| **Total Processing Latency** | 232.236s | 31.668s |
| **RTF / Speed Factor** | 0.22x (Speed: 4.55x) | 0.03x (Speed: 33.33x) |
| **Throughput (WPS)** | 0.35 WPS | 2.62 WPS |
| **Estimated Inference Cost** | $0.00 (Offline CPU) | ~$0.03519 |

**Tier B Cross-Model Corpus Divergence (2 files):** WER **6.02%**, CER **1.88%**, S/D/I = `3/2/0`, Jaccard Vocab Overlap = `0.8919`.

## Vocabulary Divergence & Substitution Highlights

### Tier A `green_call_01` (Ground Truth vs Whisper)
- **Jaccard Overlap**: `0.96`
- **Only in Reference (2)**: am, i
- **Only in Whisper (2)**: im, thats
- **Top Substitutions**: `i am` -> `im` (1x); `that is` -> `thats` (1x)

### Tier A `red_call_01` (Ground Truth vs Whisper)
- **Jaccard Overlap**: `0.9417`
- **Only in Reference (3)**: 5, are, cannot
- **Only in Whisper (3)**: cant, five, youre
- **Top Substitutions**: `cannot` -> `cant` (1x); `you are` -> `youre` (1x); `5` -> `five` (1x)

### Tier B `en_000001.mp3` (Gemini vs Whisper)
- **Jaccard Overlap**: `0.9268`
- **Only in Gemini (2)**: summary, that
- **Only in Whisper (1)**: summaries
- **Top Divergences**: `summary` -> `summaries` (1x)

### Tier B `en_000002.mp3` (Gemini vs Whisper)
- **Jaccard Overlap**: `0.8611`
- **Only in Gemini (3)**: let, threshold, us
- **Only in Whisper (2)**: lets, thresholds
- **Top Divergences**: `let us` -> `lets` (1x); `threshold` -> `thresholds` (1x)
