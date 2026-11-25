# TuneChecker Transcription Benchmark Report

- **Generated (UTC)**: 2026-11-25T10:39:29Z
- **Execution Mode**: `live`
- **Local Engine**: `faster-whisper:large-v3-turbo` (`language_mode=english`)
- **Cloud Reference Engine**: `gemini-3.5-flash`
- **Gemini API Key Configured**: `yes`

## Tier A: Faster-Whisper vs. Human/TTS Ground Truth (`samples/`)

| Sample | Verdict | Duration (s) | Engine | Status | Latency (s) | RTF (proc/audio) | Speed (audio/proc) | Throughput (WPS) | WER (%) | CER (%) | S / D / I | Accuracy (%) |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `green_call_01` | GREEN | 55.63 | `faster-whisper:large-v3-turbo` | `ok` | 18.326 | 0.3294x | 3.04x | 7.42 | 0.0% | 0.0% | 0 / 0 / 0 | 100.0% |
| `green_call_01` | GREEN | 55.63 | `gemini-3.5-flash` | `ok` | 9.28 | 0.1668x | 5.99x | 14.66 | 0.74% | 0.13% | 1 / 0 / 0 | 99.26% |
| `red_call_01` | RED | 55.70 | `faster-whisper:large-v3-turbo` | `ok` | 24.866 | 0.4464x | 2.24x | 5.27 | 0.0% | 0.0% | 0 / 0 / 0 | 100.0% |
| `red_call_01` | RED | 55.70 | `gemini-3.5-flash` | `ok` | 8.093 | 0.1453x | 6.88x | 16.19 | 0.76% | 0.28% | 1 / 0 / 0 | 99.24% |

**Tier A Local Corpus Aggregate (2 calls, 111.33s audio):** WER **0.0%**, CER **0.0%**, Accuracy **100.0%**, S/D/I = `0/0/0`, RTF `0.388x`, Speed `2.58x`, Throughput `6.18 WPS`.
**Tier A Gemini Corpus Aggregate (2 calls):** WER **0.75%**, CER **0.2%**, Accuracy **99.25%**, RTF `0.156x`, Speed `6.41x`, Throughput `15.37 WPS`.

## Tier B: Cross-Model Benchmark on `datahiveai/english-conversations-sample`

*Note: `datahiveai/english-conversations-sample` does not ship human transcripts; Tier B measures cross-model divergence treating Gemini output as reference.*

| Audio File | Topic | Duration (s) | Whisper Words | Whisper Latency (s) | Whisper RTF | Whisper Speed | Whisper WPS | Gemini Status | Cross-Model WER (%) | Cross-Model CER (%) | S / D / I |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `en_000001.mp3` | business_finance | 30.00 | 4 | 7.288 | 0.2429x | 4.12x | 0.55 | `ok` | 94.44% | 80.77% | 3 / 14 / 0 |
| `en_000002.mp3` | business_finance | 30.00 | 35 | 15.912 | 0.5304x | 1.89x | 2.2 | `ok` | 45.45% | 36.84% | 9 / 10 / 1 |

### Speed, Throughput & Cost Comparison

| Dimension | TuneChecker Local (`faster-whisper`) | Gemini Cloud (`gemini-3.5-flash`) |
| :--- | :---: | :---: |
| **Total Audio Duration** | 60.00s | 60.00s |
| **Total Processing Latency** | 23.200s | 16.531s |
| **RTF / Speed Factor** | 0.3867x (Speed: 2.59x) | 0.2755x (Speed: 3.63x) |
| **Throughput (WPS)** | 1.68 WPS | 3.75 WPS |
| **Estimated Inference Cost** | $0.00 (Offline CPU) | ~$0.00200 |

**Tier B Cross-Model Corpus Divergence (2 files):** WER **59.68%**, CER **47.88%**, S/D/I = `12/24/1`, Jaccard Vocab Overlap = `0.3818`.

## Vocabulary Divergence & Substitution Highlights

### Tier A `green_call_01` (Ground Truth vs Whisper)
- **Jaccard Overlap**: `1.0`
- **Only in Reference (0)**: None
- **Only in Whisper (0)**: None

### Tier A `red_call_01` (Ground Truth vs Whisper)
- **Jaccard Overlap**: `1.0`
- **Only in Reference (0)**: None
- **Only in Whisper (0)**: None

### Tier B `en_000001.mp3` (Gemini vs Whisper)
- **Jaccard Overlap**: `0.0769`
- **Only in Gemini (9)**: can, hear, league, master, me, need, sir, talk, to
- **Only in Whisper (3)**: much, thank, very
- **Top Divergences**: `can` -> `thank` (1x); `hear me need to talk can you hear me can you hear me sir league master` -> `very much` (1x)

### Tier B `en_000002.mp3` (Gemini vs Whisper)
- **Jaccard Overlap**: `0.4773`
- **Only in Gemini (14)**: 247, ah, are, attending, club, crypto, dear, in, mahesh, now, oh, shift, there, your
- **Only in Whisper (9)**: 24, 7, nadia, of, speak, students, them, turn, yoshi
- **Top Divergences**: `good afternoon now you are attending` -> `nadia i turn` (1x); `in your shift 247 mahesh mahesh mahesh club` -> `yoshi 24 7` (1x); `there oh ah crypto dear` -> `them` (1x)
