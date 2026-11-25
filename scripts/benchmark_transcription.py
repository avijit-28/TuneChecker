#!/usr/bin/env python3
"""
TuneChecker Transcription Benchmarking Engine (Milestone 4)

Two-tier transcription benchmark:
  - Tier A: Local Faster-Whisper (and optional Gemini) vs. Human/TTS Ground Truth
    on `samples/green_call_01.m4a` and `samples/red_call_01.m4a`.
  - Tier B: Local Faster-Whisper vs. Gemini Cloud Reference on
    `datahiveai/english-conversations-sample`.

Computes WER, CER, substitutions/deletions/insertions via `jiwer`, Real-Time
Factor (RTF), speed factor, throughput (WPS), and bidirectional vocabulary
divergence. Outputs `BENCHMARK_REPORT.md` and `benchmark_results.json`.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.metadata
import json
import logging
import math
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import jiwer
from dotenv import load_dotenv

# Resolve repository and backend directories
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load backend/.env without overriding explicit environment variables
load_dotenv(BACKEND_DIR / ".env", override=False)

logger = logging.getLogger("tune_checker.benchmark")

DATAHIVE_DATASET_ID = "datahiveai/english-conversations-sample"
TIER_A_FIXTURE_PATH = BACKEND_DIR / "tests" / "fixtures" / "tier_a_ground_truth.json"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEPRECATED_GEMINI_PREFIXES = ("gemini-2.5", "gemini-2.0", "gemini-1.5", "gemini-1.0")

# Jiwer normalization pipeline applied symmetrically to reference and hypothesis
_TEXT_NORMALIZER = jiwer.Compose(
    [
        jiwer.ToLowerCase(),
        jiwer.RemovePunctuation(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.Strip(),
    ]
)


@dataclass
class EngineResult:
    engine: str
    model: str
    status: str  # "ok", "skipped_missing_api_key", "failed", "not_requested"
    text: Optional[str] = None
    audio_duration_seconds: float = 0.0
    processing_time_seconds: float = 0.0
    model_load_seconds: float = 0.0
    real_time_factor: Optional[float] = None  # processing_time / audio_duration
    speed_factor: Optional[float] = None  # audio_duration / processing_time
    throughput_wps: Optional[float] = None  # words / processing_time
    word_count: int = 0
    utterance_count: int = 0
    cost_usd: Optional[float] = None
    error: Optional[str] = None
    mode: str = "live"  # "live" or "mock"
    segments: list[dict[str, Any]] = field(default_factory=list)


def normalize_text(text: str) -> str:
    """Normalize text deterministically before WER/CER computation."""
    if not text:
        return ""
    cleaned = (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", " ")
        .replace("\u2014", " ")
        .replace("-", " ")
    )
    return _TEXT_NORMALIZER(cleaned)


def compute_transcription_metrics(reference_text: str, hypothesis_text: str) -> dict[str, Any]:
    """
    Compute WER, CER, accuracy, and word/character S/D/I/H counts using `jiwer`.
    """
    ref_norm = normalize_text(reference_text)
    hyp_norm = normalize_text(hypothesis_text)

    ref_words = ref_norm.split()
    hyp_words = hyp_norm.split()

    if not ref_norm and not hyp_norm:
        return {
            "wer": 0.0,
            "wer_percent": 0.0,
            "cer": 0.0,
            "cer_percent": 0.0,
            "accuracy_percent": 100.0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": 0,
            "hits": 0,
            "char_substitutions": 0,
            "char_deletions": 0,
            "char_insertions": 0,
            "char_hits": 0,
            "ref_word_count": 0,
            "hyp_word_count": 0,
            "ref_char_count": 0,
            "hyp_char_count": 0,
        }

    if not ref_norm:
        return {
            "wer": 1.0,
            "wer_percent": 100.0,
            "cer": 1.0,
            "cer_percent": 100.0,
            "accuracy_percent": 0.0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": len(hyp_words),
            "hits": 0,
            "char_substitutions": 0,
            "char_deletions": 0,
            "char_insertions": len(hyp_norm),
            "char_hits": 0,
            "ref_word_count": 0,
            "hyp_word_count": len(hyp_words),
            "ref_char_count": 0,
            "hyp_char_count": len(hyp_norm),
        }

    wer_val = float(jiwer.wer(ref_norm, hyp_norm))
    cer_val = float(jiwer.cer(ref_norm, hyp_norm))
    word_out = jiwer.process_words(ref_norm, hyp_norm)
    char_out = jiwer.process_characters(ref_norm, hyp_norm)

    wer_pct = round(wer_val * 100.0, 2)
    cer_pct = round(cer_val * 100.0, 2)

    return {
        "wer": round(wer_val, 6),
        "wer_percent": wer_pct,
        "cer": round(cer_val, 6),
        "cer_percent": cer_pct,
        "accuracy_percent": round(max(0.0, 100.0 - wer_pct), 2),
        "substitutions": int(word_out.substitutions),
        "deletions": int(word_out.deletions),
        "insertions": int(word_out.insertions),
        "hits": int(word_out.hits),
        "char_substitutions": int(char_out.substitutions),
        "char_deletions": int(char_out.deletions),
        "char_insertions": int(char_out.insertions),
        "char_hits": int(char_out.hits),
        "ref_word_count": len(ref_words),
        "hyp_word_count": len(hyp_words),
        "ref_char_count": len(ref_norm),
        "hyp_char_count": len(hyp_norm),
    }


def compute_vocab_diff(
    reference_text: str,
    hypothesis_text: str,
    max_terms: int = 25,
    max_pairs: int = 15,
) -> dict[str, Any]:
    """Compute distinct vocabulary divergence and aligned substitution pairs."""
    ref_tokens = normalize_text(reference_text).split()
    hyp_tokens = normalize_text(hypothesis_text).split()

    ref_vocab = set(ref_tokens)
    hyp_vocab = set(hyp_tokens)
    shared = ref_vocab & hyp_vocab
    union = ref_vocab | hyp_vocab

    only_in_ref = sorted(ref_vocab - hyp_vocab)
    only_in_hyp = sorted(hyp_vocab - ref_vocab)
    jaccard = round(len(shared) / len(union), 4) if union else 1.0

    pair_counts: Counter[tuple[str, str]] = Counter()
    matcher = difflib.SequenceMatcher(None, ref_tokens, hyp_tokens)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            ref_phrase = " ".join(ref_tokens[i1:i2])
            hyp_phrase = " ".join(hyp_tokens[j1:j2])
            pair_counts[(ref_phrase, hyp_phrase)] += 1

    substitution_pairs = [
        {"reference": ref_p, "hypothesis": hyp_p, "count": count}
        for (ref_p, hyp_p), count in pair_counts.most_common(max_pairs)
    ]

    return {
        "ref_unique_vocab_count": len(ref_vocab),
        "hyp_unique_vocab_count": len(hyp_vocab),
        "shared_vocab_count": len(shared),
        "jaccard_similarity": jaccard,
        "only_in_reference": only_in_ref[:max_terms],
        "only_in_reference_total": len(only_in_ref),
        "only_in_hypothesis": only_in_hyp[:max_terms],
        "only_in_hypothesis_total": len(only_in_hyp),
        "substitution_pairs": substitution_pairs,
    }


def compute_performance_metrics(
    audio_duration_sec: float,
    processing_time_sec: float,
    word_count: int,
) -> dict[str, float]:
    """Compute RTF (proc/audio), speed factor (audio/proc), and WPS throughput."""
    safe_dur = max(float(audio_duration_sec), 0.001)
    safe_proc = max(float(processing_time_sec), 0.0001)
    return {
        "real_time_factor": round(safe_proc / safe_dur, 4),
        "speed_factor": round(safe_dur / safe_proc, 2),
        "throughput_wps": round(word_count / safe_proc, 2),
    }


def resolve_gemini_model(requested_model: str) -> tuple[str, Optional[str]]:
    """
    Resolve Gemini model name, substituting deprecated models with gemini-4-hydrogen.
    """
    model_clean = (requested_model or DEFAULT_GEMINI_MODEL).strip()
    lower = model_clean.lower()
    if any(lower.startswith(prefix) for prefix in DEPRECATED_GEMINI_PREFIXES):
        note = (
            f"Requested Gemini model '{model_clean}' is deprecated; "
            "substituting 'gemini-4-hydrogen' per google-genai guidelines."
        )
        return "gemini-4-hydrogen", note
    return model_clean, None


def get_gemini_api_key() -> Optional[str]:
    """Resolve Gemini API key from environment or TuneChecker Settings."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key and key.strip():
        return key.strip()
    try:
        from app.config import settings

        cfg_key = getattr(settings, "GEMINI_API_KEY", None)
        if cfg_key and cfg_key.strip():
            return cfg_key.strip()
    except Exception:
        pass
    return None


def probe_audio_duration(audio_path: Path) -> float:
    """Probe audio duration in seconds via ffprobe, returning 0.0 on failure."""
    try:
        from app.audio.ffmpeg import probe_audio

        info = probe_audio(audio_path)
        return float(info.get("format", {}).get("duration", 0.0) or 0.0)
    except Exception:
        return 0.0


def maybe_trim_audio(
    audio_path: Path,
    max_audio_seconds: Optional[float],
    workdir: Path,
) -> Path:
    """Trim audio deterministically if max_audio_seconds is set and > 0."""
    if not max_audio_seconds or max_audio_seconds <= 0:
        return audio_path

    from app.audio.ffmpeg import run_ffmpeg

    trimmed_path = workdir / f"{audio_path.stem}_trimmed.wav"
    try:
        proc = run_ffmpeg(
            [
                "-loglevel",
                "error",
                "-y",
                "-t",
                f"{max_audio_seconds}",
                "-i",
                str(audio_path),
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(trimmed_path),
            ],
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Timed out trimming audio {audio_path}: {exc}") from exc

    if proc.returncode != 0 or not trimmed_path.exists():
        stderr_text = (proc.stderr or "").strip()
        stderr_tail = stderr_text[-500:] if stderr_text else "unknown ffmpeg error (no stderr)"
        raise RuntimeError(f"Failed to trim audio {audio_path}: {stderr_tail}")
    return trimmed_path


def load_tier_a_ground_truth(fixture_path: Path = TIER_A_FIXTURE_PATH) -> list[dict[str, Any]]:
    """Load Tier A ground truth definitions."""
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    return list(data.get("samples", []))


def parse_dataset_slice(slice_spec: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Parse --dataset-slice into a deterministic subset of dataset items.
    Supports:
      - Integer count: "2" -> first 2 items
      - Slice syntax: "1:3", ":2", "1:" -> items[start:end]
      - Comma-separated filenames or stems: "en_000001.mp3,en_000015.mp3"
    """
    spec = (slice_spec or "2").strip()

    if re.fullmatch(r"-?\d+", spec):
        count = int(spec)
        if count <= 0:
            raise ValueError(f"--dataset-slice integer must be > 0, got {count}")
        return items[:count] if items else []

    if ":" in spec and "," not in spec:
        if spec.count(":") > 1:
            raise ValueError(f"Invalid slice format: too many colons in '{spec}'")
        parts = spec.split(":", 1)
        try:
            start = int(parts[0]) if parts[0].strip() else None
            end = int(parts[1]) if parts[1].strip() else None
        except ValueError as exc:
            raise ValueError(f"Invalid slice format: non-integer bounds in '{spec}'") from exc
        if not items:
            return []
        selected = items[start:end]
        if not selected:
            raise ValueError(f"--dataset-slice '{spec}' selected 0 items")
        return selected

    if not items:
        return []

    requested = [token.strip() for token in spec.split(",") if token.strip()]
    if not requested:
        raise ValueError(f"Invalid --dataset-slice specification: '{slice_spec}'")

    by_name = {item["file_name"]: item for item in items}
    by_stem = {Path(item["file_name"]).stem: item for item in items}

    selected: list[dict[str, Any]] = []
    missing: list[str] = []
    for token in requested:
        if token in by_name:
            selected.append(by_name[token])
        elif token in by_stem:
            selected.append(by_stem[token])
        else:
            missing.append(token)

    if missing:
        raise ValueError(
            f"Requested dataset files not found in {DATAHIVE_DATASET_ID}: {', '.join(missing)}"
        )
    return selected


def _mock_datahive_catalog() -> list[dict[str, Any]]:
    """Deterministic fallback catalog for --mock when HF cache is absent."""
    return [
        {
            "file_name": "en_000001.mp3",
            "topic": "business_finance",
            "duration_seconds": 389.04,
            "turns_per_minute": 10.6,
            "overlap_percent": 16.5,
            "language": "en",
            "audio_path": None,
        },
        {
            "file_name": "en_000002.mp3",
            "topic": "business_finance",
            "duration_seconds": 666.576,
            "turns_per_minute": 13.1,
            "overlap_percent": 15.4,
            "language": "en",
            "audio_path": None,
        },
        {
            "file_name": "en_000015.mp3",
            "topic": "customer_service",
            "duration_seconds": 304.56,
            "turns_per_minute": 11.4,
            "overlap_percent": 12.0,
            "language": "en",
            "audio_path": None,
        },
        {
            "file_name": "en_000020.mp3",
            "topic": "sales_inquiry",
            "duration_seconds": 320.57,
            "turns_per_minute": 9.8,
            "overlap_percent": 10.5,
            "language": "en",
            "audio_path": None,
        },
    ]


def _read_datahive_metadata(snapshot_dir: Path) -> list[dict[str, Any]]:
    """Read preview/metadata.jsonl (or fallback to preview/*.mp3) from snapshot dir."""
    preview_dir = snapshot_dir / "preview"
    if not preview_dir.exists():
        preview_dir = snapshot_dir

    metadata_path = preview_dir / "metadata.jsonl"
    items: list[dict[str, Any]] = []

    if metadata_path.exists():
        for line in metadata_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            fname = row.get("file_name")
            if not fname:
                continue
            row["audio_path"] = preview_dir / fname
            items.append(row)
    else:
        for mp3 in sorted(preview_dir.glob("*.mp3")):
            items.append(
                {
                    "file_name": mp3.name,
                    "topic": "unknown",
                    "duration_seconds": probe_audio_duration(mp3),
                    "language": "en",
                    "audio_path": mp3,
                }
            )
    return items


def load_datahive_slice(
    slice_spec: str,
    local_files_only: bool = False,
    mock: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Resolve `datahiveai/english-conversations-sample` snapshot and slice it."""
    from huggingface_hub import snapshot_download

    snapshot_path: Optional[Path] = None
    source_note = "huggingface_cache"

    try:
        dl_path = snapshot_download(
            repo_id=DATAHIVE_DATASET_ID,
            repo_type="dataset",
            local_files_only=True if mock else local_files_only,
        )
        snapshot_path = Path(dl_path)
    except Exception as exc:
        if mock:
            catalog = _mock_datahive_catalog()
            return parse_dataset_slice(slice_spec, catalog), {
                "snapshot_path": None,
                "source": "mock_synthetic_catalog",
            }
        if not local_files_only:
            # Retry cache-only if online check failed
            try:
                dl_path = snapshot_download(
                    repo_id=DATAHIVE_DATASET_ID,
                    repo_type="dataset",
                    local_files_only=True,
                )
                snapshot_path = Path(dl_path)
                source_note = "huggingface_cache_offline_fallback"
            except Exception as cache_exc:
                raise RuntimeError(
                    f"Unable to load {DATAHIVE_DATASET_ID} online or from cache: {cache_exc}"
                ) from exc
        else:
            raise RuntimeError(
                f"Cached snapshot for {DATAHIVE_DATASET_ID} not found with --local-files-only: {exc}"
            ) from exc

    items = _read_datahive_metadata(snapshot_path)
    selected = parse_dataset_slice(slice_spec, items)
    return selected, {"snapshot_path": str(snapshot_path), "source": source_note}


class LocalWhisperRunner:
    """Runs TuneChecker's FasterWhisperProvider with controlled language mode."""

    def __init__(self, whisper_model: Optional[str] = None, language_mode: str = "english"):
        self.whisper_model_override = whisper_model
        self.language_mode = language_mode
        self._model_loaded = False

    def transcribe(self, audio_path: Path) -> EngineResult:
        from app.audio.normalize import normalize_to_wav
        from app.config import settings
        from app.pipeline.providers.stt.faster_whisper import FasterWhisperProvider

        orig_model = settings.WHISPER_MODEL
        orig_mode = settings.WHISPER_LANGUAGE_MODE
        effective_model = self.whisper_model_override or orig_model

        try:
            if self.whisper_model_override and self.whisper_model_override != orig_model:
                settings.WHISPER_MODEL = self.whisper_model_override
                FasterWhisperProvider._model_instance = None
            settings.WHISPER_LANGUAGE_MODE = self.language_mode

            load_seconds = 0.0
            if FasterWhisperProvider._model_instance is None:
                t_load = time.perf_counter()
                FasterWhisperProvider.get_model()
                load_seconds = time.perf_counter() - t_load
                self._model_loaded = True

            provider = FasterWhisperProvider()
            with tempfile.TemporaryDirectory() as tmpdir:
                norm_wav = Path(tmpdir) / f"{audio_path.stem}_norm.wav"
                t0 = time.perf_counter()
                normalize_to_wav(audio_path, norm_wav)
                stt_result = provider.transcribe(norm_wav)
                proc_time = time.perf_counter() - t0

            segments = [
                {
                    "start_ms": seg.start_ms,
                    "end_ms": seg.end_ms,
                    "text": seg.text.strip(),
                }
                for seg in stt_result.segments
            ]
            text = " ".join(s["text"] for s in segments if s["text"]).strip()
            audio_dur = float(stt_result.duration_sec or probe_audio_duration(audio_path))
            word_count = len(normalize_text(text).split())
            perf = compute_performance_metrics(audio_dur, proc_time, word_count)

            return EngineResult(
                engine="local",
                model=f"faster-whisper:{effective_model}",
                status="ok",
                text=text,
                audio_duration_seconds=round(audio_dur, 2),
                processing_time_seconds=round(proc_time, 3),
                model_load_seconds=round(load_seconds, 3),
                real_time_factor=perf["real_time_factor"],
                speed_factor=perf["speed_factor"],
                throughput_wps=perf["throughput_wps"],
                word_count=word_count,
                utterance_count=len(segments),
                cost_usd=0.0,
                mode="live",
                segments=segments,
            )
        except Exception as exc:
            return EngineResult(
                engine="local",
                model=f"faster-whisper:{effective_model}",
                status="failed",
                error=str(exc),
                cost_usd=0.0,
                mode="live",
            )
        finally:
            if self.whisper_model_override and self.whisper_model_override != orig_model:
                FasterWhisperProvider._model_instance = None
            settings.WHISPER_MODEL = orig_model
            settings.WHISPER_LANGUAGE_MODE = orig_mode


def _extract_interaction_text(interaction: Any) -> str:
    """Defensively extract text from a google-genai Interaction response."""
    output_text = getattr(interaction, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    for step in getattr(interaction, "steps", None) or []:
        step_type = getattr(step, "type", None)
        if step_type in (None, "model_output"):
            for item in getattr(step, "content", None) or []:
                text_val = getattr(item, "text", None)
                if isinstance(text_val, str) and text_val.strip():
                    chunks.append(text_val.strip())
    return " ".join(chunks).strip()


class GeminiTranscriber:
    """Runs Gemini transcription via google-genai SDK with honest missing-key handling."""

    def __init__(self, gemini_model: str = DEFAULT_GEMINI_MODEL):
        self.requested_model = gemini_model
        self.effective_model, self.deprecation_note = resolve_gemini_model(gemini_model)

    def transcribe(
        self,
        audio_path: Path,
        audio_duration_sec: float = 0.0,
        language_mode: str = "english",
    ) -> EngineResult:
        api_key = get_gemini_api_key()
        if not api_key:
            return EngineResult(
                engine="gemini",
                model=self.effective_model,
                status="skipped_missing_api_key",
                text=None,
                audio_duration_seconds=round(audio_duration_sec, 2),
                cost_usd=None,
                error="GEMINI_API_KEY / GOOGLE_API_KEY is not configured.",
                mode="live",
            )

        from google import genai

        client = genai.Client(api_key=api_key)
        mime_type, _ = mimetypes.guess_type(str(audio_path))
        if not mime_type:
            ext = audio_path.suffix.lower()
            mime_type = {
                ".mp3": "audio/mpeg",
                ".m4a": "audio/mp4",
                ".wav": "audio/wav",
                ".mpeg": "audio/mpeg",
            }.get(ext, "audio/mpeg")

        uploaded = None
        t0 = time.perf_counter()
        try:
            uploaded = client.files.upload(file=str(audio_path))
            prompt = (
                "Transcribe this audio conversation verbatim in plain text. "
                "Include every spoken word accurately without commentary, summaries, or timestamps."
            )
            create_kwargs: dict[str, Any] = {
                "model": self.effective_model,
                "input": [
                    {
                        "type": "audio",
                        "uri": uploaded.uri,
                        "mime_type": getattr(uploaded, "mime_type", None) or mime_type,
                    },
                    {"type": "text", "text": prompt},
                ],
                "store": False,
            }
            if self.effective_model == "gemini-3.5-transcribe":
                lang_code = "hi" if language_mode == "hindi" else "en"
                create_kwargs["generation_config"] = {
                    "transcription_config": {
                        "mode": {"type": "verbatim"},
                        "language_codes": [lang_code],
                    }
                }

            interaction = client.interactions.create(**create_kwargs)
            proc_time = time.perf_counter() - t0
            text = _extract_interaction_text(interaction)
            if not text:
                raise RuntimeError("Gemini interaction returned empty transcript.")

            dur = audio_duration_sec or probe_audio_duration(audio_path)
            word_count = len(normalize_text(text).split())
            perf = compute_performance_metrics(dur, proc_time, word_count)
            est_cost = round((max(dur, 0.0) / 60.0) * 0.002, 5)

            return EngineResult(
                engine="gemini",
                model=self.effective_model,
                status="ok",
                text=text,
                audio_duration_seconds=round(dur, 2),
                processing_time_seconds=round(proc_time, 3),
                real_time_factor=perf["real_time_factor"],
                speed_factor=perf["speed_factor"],
                throughput_wps=perf["throughput_wps"],
                word_count=word_count,
                utterance_count=0,
                cost_usd=est_cost,
                mode="live",
            )
        except Exception as exc:
            proc_time = time.perf_counter() - t0
            return EngineResult(
                engine="gemini",
                model=self.effective_model,
                status="failed",
                text=None,
                audio_duration_seconds=round(audio_duration_sec, 2),
                processing_time_seconds=round(proc_time, 3),
                cost_usd=None,
                error=str(exc),
                mode="live",
            )
        finally:
            if uploaded is not None and getattr(uploaded, "name", None):
                try:
                    client.files.delete(name=uploaded.name)
                except Exception:
                    pass


# Deterministic mock scripts for Tier B so --mock exercises real jiwer WER/CER/vocab diff
_MOCK_TIER_B_SCRIPTS: dict[str, tuple[str, str]] = {
    "en_000001.mp3": (
        # Gemini reference mock
        "Good morning everyone, thank you for joining the quarterly finance alignment call. "
        "We reviewed the disbursement schedule for the vendor onboarding milestones and confirmed "
        "that the invoice reconciliation will finalize on Friday afternoon. Please confirm whether "
        "the procurement team received the updated compliance addendum and ledger summary.",
        # Local Whisper mock (realistic minor ASR divergence: contraction, homophone, punctuation)
        "Good morning everyone, thank you for joining the quarterly finance alignment call. "
        "We reviewed the disbursement schedule for the vendor onboarding milestones and confirmed "
        "the invoice reconciliation will finalize on Friday afternoon. Please confirm whether "
        "the procurement team received the updated compliance addendum and ledger summaries.",
    ),
    "en_000002.mp3": (
        "Let us walk through the regional credit utilization metrics for the second quarter. "
        "Our partner banks reported faster turnaround times on small business loan approvals, "
        "though cross border settlement fees remain slightly above our target threshold.",
        "Let's walk through the regional credit utilization metrics for the second quarter. "
        "Our partner banks reported faster turnaround times on small business loan approvals, "
        "though cross border settlement fees remain slightly above our target thresholds.",
    ),
}


def _simulate_whisper_from_ground_truth(sample_id: str, reference_text: str) -> str:
    """Create deterministic realistic mock Whisper output from Tier A ground truth."""
    if sample_id == "green_call_01":
        # Realistic slight ASR differences: "step by step" vs "step-by-step", "deep dive", one word variant
        return (
            reference_text.replace("step-by-step", "step by step")
            .replace("technical deep-dive", "technical deep dive")
            .replace("I am really glad", "I'm really glad")
            .replace("That is completely", "That's completely")
        )
    if sample_id == "red_call_01":
        return (
            reference_text.replace("non-negotiable", "non negotiable")
            .replace("cannot afford", "can't afford")
            .replace("you are frankly", "you're frankly")
            .replace("5 PM", "five PM")
        )
    return reference_text


def _simulate_gemini_from_ground_truth(sample_id: str, reference_text: str) -> str:
    """Create deterministic realistic mock Gemini output from Tier A ground truth."""
    if sample_id == "green_call_01":
        return reference_text.replace("step-by-step", "step by step")
    if sample_id == "red_call_01":
        return reference_text.replace("non-negotiable", "non negotiable")
    return reference_text


def run_mock_tier_a(
    sample: dict[str, Any],
    models: set[str],
    whisper_model: str,
    gemini_model: str,
) -> dict[str, EngineResult]:
    """Deterministic mock transcription for Tier A."""
    ref_text = sample["reference_transcript"]
    audio_path = REPO_ROOT / sample["audio_path"]
    dur = probe_audio_duration(audio_path) if audio_path.exists() else 55.6
    if dur <= 0:
        dur = 55.6

    results: dict[str, EngineResult] = {}
    if "local" in models:
        text = _simulate_whisper_from_ground_truth(sample["id"], ref_text)
        proc = round(dur * 0.14, 3)
        wc = len(normalize_text(text).split())
        perf = compute_performance_metrics(dur, proc, wc)
        results["local"] = EngineResult(
            engine="local",
            model=f"faster-whisper:{whisper_model}",
            status="ok",
            text=text,
            audio_duration_seconds=round(dur, 2),
            processing_time_seconds=proc,
            real_time_factor=perf["real_time_factor"],
            speed_factor=perf["speed_factor"],
            throughput_wps=perf["throughput_wps"],
            word_count=wc,
            utterance_count=len(sample.get("utterances", [])),
            cost_usd=0.0,
            mode="mock",
        )
    if "gemini" in models:
        text = _simulate_gemini_from_ground_truth(sample["id"], ref_text)
        proc = round(max(1.2, dur * 0.04), 3)
        wc = len(normalize_text(text).split())
        perf = compute_performance_metrics(dur, proc, wc)
        results["gemini"] = EngineResult(
            engine="gemini",
            model=gemini_model,
            status="ok",
            text=text,
            audio_duration_seconds=round(dur, 2),
            processing_time_seconds=proc,
            real_time_factor=perf["real_time_factor"],
            speed_factor=perf["speed_factor"],
            throughput_wps=perf["throughput_wps"],
            word_count=wc,
            cost_usd=round((dur / 60.0) * 0.002, 5),
            mode="mock",
        )
    return results


def run_mock_tier_b(
    item: dict[str, Any],
    models: set[str],
    whisper_model: str,
    gemini_model: str,
) -> dict[str, EngineResult]:
    """Deterministic mock transcription for Tier B."""
    fname = item["file_name"]
    dur = float(item.get("duration_seconds") or 300.0)
    default_gem, default_whisp = _MOCK_TIER_B_SCRIPTS["en_000001.mp3"]
    gem_text, whisp_text = _MOCK_TIER_B_SCRIPTS.get(fname, (default_gem, default_whisp))

    results: dict[str, EngineResult] = {}
    if "local" in models:
        proc = round(dur * 0.22, 3)
        wc = len(normalize_text(whisp_text).split())
        perf = compute_performance_metrics(dur, proc, wc)
        results["local"] = EngineResult(
            engine="local",
            model=f"faster-whisper:{whisper_model}",
            status="ok",
            text=whisp_text,
            audio_duration_seconds=round(dur, 2),
            processing_time_seconds=proc,
            real_time_factor=perf["real_time_factor"],
            speed_factor=perf["speed_factor"],
            throughput_wps=perf["throughput_wps"],
            word_count=wc,
            utterance_count=8,
            cost_usd=0.0,
            mode="mock",
        )
    if "gemini" in models:
        proc = round(max(1.5, dur * 0.03), 3)
        wc = len(normalize_text(gem_text).split())
        perf = compute_performance_metrics(dur, proc, wc)
        results["gemini"] = EngineResult(
            engine="gemini",
            model=gemini_model,
            status="ok",
            text=gem_text,
            audio_duration_seconds=round(dur, 2),
            processing_time_seconds=proc,
            real_time_factor=perf["real_time_factor"],
            speed_factor=perf["speed_factor"],
            throughput_wps=perf["throughput_wps"],
            word_count=wc,
            cost_usd=round((dur / 60.0) * 0.002, 5),
            mode="mock",
        )
    return results


def _aggregate_engine_tier_a(samples_out: list[dict[str, Any]], engine_key: str) -> Optional[dict[str, Any]]:
    """Aggregate Tier A ground-truth metrics across completed samples for an engine."""
    refs: list[str] = []
    hyps: list[str] = []
    procs: list[float] = []
    durs: list[float] = []
    words: list[int] = []

    for sample in samples_out:
        eng = sample.get(engine_key)
        if not eng or eng.get("status") != "ok" or eng.get("text") is None:
            continue
        refs.append(sample["reference_transcript"])
        hyps.append(eng["text"])
        procs.append(float(eng.get("processing_time_seconds") or 0.0))
        durs.append(float(eng.get("audio_duration_seconds") or 0.0))
        words.append(int(eng.get("word_count") or 0))

    if not refs:
        return None

    corpus_metrics = compute_transcription_metrics(" ".join(refs), " ".join(hyps))
    total_proc = sum(procs)
    total_dur = sum(durs)
    total_words = sum(words)
    perf = compute_performance_metrics(total_dur, total_proc, total_words)

    return {
        "evaluated_samples": len(refs),
        "total_audio_duration_seconds": round(total_dur, 2),
        "total_processing_time_seconds": round(total_proc, 3),
        **perf,
        **corpus_metrics,
    }


def _aggregate_tier_b(samples_out: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Tier B metrics across DataHive files."""
    local_durs: list[float] = []
    local_procs: list[float] = []
    local_words: list[int] = []

    gemini_durs: list[float] = []
    gemini_procs: list[float] = []
    gemini_words: list[int] = []
    gemini_costs: list[float] = []
    gemini_statuses: list[str] = []

    comp_refs: list[str] = []
    comp_hyps: list[str] = []

    for sample in samples_out:
        loc = sample.get("local")
        if loc and loc.get("status") == "ok":
            local_durs.append(float(loc.get("audio_duration_seconds") or 0.0))
            local_procs.append(float(loc.get("processing_time_seconds") or 0.0))
            local_words.append(int(loc.get("word_count") or 0))

        gem = sample.get("gemini")
        if gem:
            gemini_statuses.append(gem.get("status", "unknown"))
            if gem.get("status") == "ok" and gem.get("text") is not None:
                gemini_durs.append(float(gem.get("audio_duration_seconds") or 0.0))
                gemini_procs.append(float(gem.get("processing_time_seconds") or 0.0))
                gemini_words.append(int(gem.get("word_count") or 0))
                if gem.get("cost_usd") is not None:
                    gemini_costs.append(float(gem["cost_usd"]))

        if (
            loc
            and loc.get("status") == "ok"
            and loc.get("text") is not None
            and gem
            and gem.get("status") == "ok"
            and gem.get("text") is not None
        ):
            comp_refs.append(gem["text"])
            comp_hyps.append(loc["text"])

    local_summary = None
    if local_durs:
        total_dur = sum(local_durs)
        total_proc = sum(local_procs)
        total_words = sum(local_words)
        local_summary = {
            "evaluated_files": len(local_durs),
            "total_audio_duration_seconds": round(total_dur, 2),
            "total_processing_time_seconds": round(total_proc, 3),
            "total_words": total_words,
            "total_cost_usd": 0.0,
            **compute_performance_metrics(total_dur, total_proc, total_words),
        }

    gemini_summary: dict[str, Any] = {
        "statuses": sorted(set(gemini_statuses)) if gemini_statuses else ["not_requested"],
        "evaluated_files": len(gemini_durs),
    }
    if gemini_durs:
        g_dur = sum(gemini_durs)
        g_proc = sum(gemini_procs)
        g_words = sum(gemini_words)
        gemini_summary.update(
            {
                "total_audio_duration_seconds": round(g_dur, 2),
                "total_processing_time_seconds": round(g_proc, 3),
                "total_words": g_words,
                "estimated_total_cost_usd": round(sum(gemini_costs), 5),
                **compute_performance_metrics(g_dur, g_proc, g_words),
            }
        )

    cross_model_summary: Optional[dict[str, Any]] = None
    if comp_refs and comp_hyps:
        cross_model_summary = {
            "compared_files": len(comp_refs),
            **compute_transcription_metrics(" ".join(comp_refs), " ".join(comp_hyps)),
            "vocab_diff": compute_vocab_diff(" ".join(comp_refs), " ".join(comp_hyps)),
        }

    return {
        "local": local_summary,
        "gemini": gemini_summary,
        "cross_model_comparison": cross_model_summary,
    }


def _fmt_num(val: Optional[float | int], suffix: str = "") -> str:
    if val is None:
        return "N/A"
    return f"{val}{suffix}"


def generate_markdown_report(results: dict[str, Any]) -> str:
    """Render structured benchmark results into BENCHMARK_REPORT.md."""
    meta = results["metadata"]
    tier_a = results.get("tier_a")
    tier_b = results.get("tier_b")

    lines: list[str] = [
        "# TuneChecker Transcription Benchmark Report",
        "",
        f"- **Generated (UTC)**: {meta['timestamp_utc']}",
        f"- **Execution Mode**: `{'mock' if meta['mock_mode'] else 'live'}`",
        f"- **Local Engine**: `faster-whisper:{meta['whisper_model']}` (`language_mode={meta['language_mode']}`)",
        f"- **Cloud Reference Engine**: `{meta['effective_gemini_model']}`"
        + (
            f" (substituted from `{meta['requested_gemini_model']}`)"
            if meta.get("deprecation_note")
            else ""
        ),
        f"- **Gemini API Key Configured**: `{'yes' if meta['gemini_api_key_configured'] else 'no'}`",
        "",
    ]

    if meta.get("deprecation_note"):
        lines.extend([f"> **Note**: {meta['deprecation_note']}", ""])

    if not meta["mock_mode"] and "gemini" in meta["models_requested"] and not meta["gemini_api_key_configured"]:
        lines.extend(
            [
                "> **Honest Fallback Notice**: `GEMINI_API_KEY` / `GOOGLE_API_KEY` is not set. "
                "Gemini evaluations were skipped (`skipped_missing_api_key`) with `N/A` error rates "
                "rather than fabricating metrics.",
                "",
            ]
        )

    # Tier A
    if tier_a:
        lines.extend(
            [
                "## Tier A: Faster-Whisper vs. Human/TTS Ground Truth (`samples/`)",
                "",
                "| Sample | Verdict | Duration (s) | Engine | Status | Latency (s) | RTF (proc/audio) | Speed (audio/proc) | Throughput (WPS) | WER (%) | CER (%) | S / D / I | Accuracy (%) |",
                "| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
            ]
        )
        for sample in tier_a["samples"]:
            for eng_key in ("local", "gemini"):
                eng = sample.get(eng_key)
                if not eng:
                    continue
                m = eng.get("metrics") or {}
                sdi = (
                    f"{m['substitutions']} / {m['deletions']} / {m['insertions']}"
                    if m
                    else "N/A"
                )
                lines.append(
                    f"| `{sample['id']}` | {sample['expected_verdict']} | "
                    f"{sample['audio_duration_seconds']:.2f} | `{eng['model']}` | `{eng['status']}` | "
                    f"{_fmt_num(eng.get('processing_time_seconds'))} | "
                    f"{_fmt_num(eng.get('real_time_factor'), 'x')} | "
                    f"{_fmt_num(eng.get('speed_factor'), 'x')} | "
                    f"{_fmt_num(eng.get('throughput_wps'))} | "
                    f"{_fmt_num(m.get('wer_percent'), '%')} | "
                    f"{_fmt_num(m.get('cer_percent'), '%')} | "
                    f"{sdi} | "
                    f"{_fmt_num(m.get('accuracy_percent'), '%')} |"
                )

        agg = tier_a.get("aggregate") or {}
        if agg.get("local"):
            la = agg["local"]
            lines.extend(
                [
                    "",
                    f"**Tier A Local Corpus Aggregate ({la['evaluated_samples']} calls, {la['total_audio_duration_seconds']:.2f}s audio):** "
                    f"WER **{la['wer_percent']}%**, CER **{la['cer_percent']}%**, "
                    f"Accuracy **{la['accuracy_percent']}%**, "
                    f"S/D/I = `{la['substitutions']}/{la['deletions']}/{la['insertions']}`, "
                    f"RTF `{la['real_time_factor']}x`, Speed `{la['speed_factor']}x`, Throughput `{la['throughput_wps']} WPS`.",
                ]
            )
        if agg.get("gemini"):
            ga = agg["gemini"]
            lines.append(
                f"**Tier A Gemini Corpus Aggregate ({ga['evaluated_samples']} calls):** "
                f"WER **{ga['wer_percent']}%**, CER **{ga['cer_percent']}%**, "
                f"Accuracy **{ga['accuracy_percent']}%**, "
                f"RTF `{ga['real_time_factor']}x`, Speed `{ga['speed_factor']}x`, Throughput `{ga['throughput_wps']} WPS`."
            )
        lines.append("")

    # Tier B
    if tier_b:
        lines.extend(
            [
                f"## Tier B: Cross-Model Benchmark on `{DATAHIVE_DATASET_ID}`",
                "",
                "*Note: `datahiveai/english-conversations-sample` does not ship human transcripts; "
                "Tier B measures cross-model divergence treating Gemini output as reference.*",
                "",
                "| Audio File | Topic | Duration (s) | Whisper Words | Whisper Latency (s) | Whisper RTF | Whisper Speed | Whisper WPS | Gemini Status | Cross-Model WER (%) | Cross-Model CER (%) | S / D / I |",
                "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
            ]
        )
        for sample in tier_b["samples"]:
            loc = sample.get("local") or {}
            gem = sample.get("gemini") or {}
            comp = sample.get("cross_model_comparison") or {}
            sdi = (
                f"{comp['substitutions']} / {comp['deletions']} / {comp['insertions']}"
                if comp.get("status") == "ok"
                else "N/A"
            )
            lines.append(
                f"| `{sample['file_name']}` | {sample.get('topic', 'unknown')} | "
                f"{sample.get('duration_seconds', 0.0):.2f} | "
                f"{loc.get('word_count', 'N/A')} | "
                f"{_fmt_num(loc.get('processing_time_seconds'))} | "
                f"{_fmt_num(loc.get('real_time_factor'), 'x')} | "
                f"{_fmt_num(loc.get('speed_factor'), 'x')} | "
                f"{_fmt_num(loc.get('throughput_wps'))} | "
                f"`{gem.get('status', 'not_requested')}` | "
                f"{_fmt_num(comp.get('wer_percent'), '%')} | "
                f"{_fmt_num(comp.get('cer_percent'), '%')} | "
                f"{sdi} |"
            )

        agg_b = tier_b.get("aggregate") or {}
        loc_b = agg_b.get("local")
        gem_b = agg_b.get("gemini") or {}
        comp_b = agg_b.get("cross_model_comparison")
        lines.extend(
            [
                "",
                "### Speed, Throughput & Cost Comparison",
                "",
                "| Dimension | TuneChecker Local (`faster-whisper`) | Gemini Cloud (`"
                + meta["effective_gemini_model"]
                + "`) |",
                "| :--- | :---: | :---: |",
                f"| **Total Audio Duration** | {loc_b['total_audio_duration_seconds']:.2f}s |"
                if loc_b
                else "| **Total Audio Duration** | N/A |",
            ]
        )
        # Fix the split row cleanly
        lines.pop()
        loc_dur = f"{loc_b['total_audio_duration_seconds']:.2f}s" if loc_b else "N/A"
        gem_dur = f"{gem_b['total_audio_duration_seconds']:.2f}s" if gem_b.get("evaluated_files") else "N/A"
        loc_lat = f"{loc_b['total_processing_time_seconds']:.3f}s" if loc_b else "N/A"
        gem_lat = f"{gem_b['total_processing_time_seconds']:.3f}s" if gem_b.get("evaluated_files") else "N/A"
        loc_rtf = f"{loc_b['real_time_factor']}x (Speed: {loc_b['speed_factor']}x)" if loc_b else "N/A"
        gem_rtf = (
            f"{gem_b['real_time_factor']}x (Speed: {gem_b['speed_factor']}x)"
            if gem_b.get("evaluated_files")
            else "N/A"
        )
        loc_wps = f"{loc_b['throughput_wps']} WPS" if loc_b else "N/A"
        gem_wps = f"{gem_b['throughput_wps']} WPS" if gem_b.get("evaluated_files") else "N/A"
        gem_cost = (
            f"~${gem_b['estimated_total_cost_usd']:.5f}"
            if gem_b.get("estimated_total_cost_usd") is not None
            else "N/A"
        )
        lines.extend(
            [
                f"| **Total Audio Duration** | {loc_dur} | {gem_dur} |",
                f"| **Total Processing Latency** | {loc_lat} | {gem_lat} |",
                f"| **RTF / Speed Factor** | {loc_rtf} | {gem_rtf} |",
                f"| **Throughput (WPS)** | {loc_wps} | {gem_wps} |",
                f"| **Estimated Inference Cost** | $0.00 (Offline CPU) | {gem_cost} |",
                "",
            ]
        )
        if comp_b:
            lines.append(
                f"**Tier B Cross-Model Corpus Divergence ({comp_b['compared_files']} files):** "
                f"WER **{comp_b['wer_percent']}%**, CER **{comp_b['cer_percent']}%**, "
                f"S/D/I = `{comp_b['substitutions']}/{comp_b['deletions']}/{comp_b['insertions']}`, "
                f"Jaccard Vocab Overlap = `{comp_b['vocab_diff']['jaccard_similarity']}`."
            )
            lines.append("")

    # Vocabulary Divergence Section
    lines.extend(["## Vocabulary Divergence & Substitution Highlights", ""])
    any_vocab = False
    if tier_a:
        for sample in tier_a["samples"]:
            loc = sample.get("local") or {}
            vdiff = loc.get("vocab_diff")
            if vdiff:
                any_vocab = True
                lines.append(f"### Tier A `{sample['id']}` (Ground Truth vs Whisper)")
                lines.append(f"- **Jaccard Overlap**: `{vdiff['jaccard_similarity']}`")
                lines.append(
                    f"- **Only in Reference ({vdiff['only_in_reference_total']})**: "
                    f"{', '.join(vdiff['only_in_reference']) or 'None'}"
                )
                lines.append(
                    f"- **Only in Whisper ({vdiff['only_in_hypothesis_total']})**: "
                    f"{', '.join(vdiff['only_in_hypothesis']) or 'None'}"
                )
                if vdiff["substitution_pairs"]:
                    pairs_str = "; ".join(
                        f"`{p['reference']}` -> `{p['hypothesis']}` ({p['count']}x)"
                        for p in vdiff["substitution_pairs"][:8]
                    )
                    lines.append(f"- **Top Substitutions**: {pairs_str}")
                lines.append("")

    if tier_b:
        for sample in tier_b["samples"]:
            comp = sample.get("cross_model_comparison") or {}
            vdiff = comp.get("vocab_diff")
            if vdiff:
                any_vocab = True
                lines.append(f"### Tier B `{sample['file_name']}` (Gemini vs Whisper)")
                lines.append(f"- **Jaccard Overlap**: `{vdiff['jaccard_similarity']}`")
                lines.append(
                    f"- **Only in Gemini ({vdiff['only_in_reference_total']})**: "
                    f"{', '.join(vdiff['only_in_reference']) or 'None'}"
                )
                lines.append(
                    f"- **Only in Whisper ({vdiff['only_in_hypothesis_total']})**: "
                    f"{', '.join(vdiff['only_in_hypothesis']) or 'None'}"
                )
                if vdiff["substitution_pairs"]:
                    pairs_str = "; ".join(
                        f"`{p['reference']}` -> `{p['hypothesis']}` ({p['count']}x)"
                        for p in vdiff["substitution_pairs"][:8]
                    )
                    lines.append(f"- **Top Divergences**: {pairs_str}")
                lines.append("")

    if not any_vocab:
        lines.append("No vocabulary comparisons available (missing reference/Gemini outputs).")
        lines.append("")

    # Surface per-sample errors in Markdown report when any occurred
    error_lines: list[str] = []
    if tier_a:
        for sample in tier_a["samples"]:
            if sample.get("status") == "failed" and sample.get("error"):
                error_lines.append(f"- Tier A `{sample['id']}`: {sample['error']}")
            else:
                for eng_key in ("local", "gemini"):
                    eng = sample.get(eng_key) or {}
                    if eng.get("status") == "failed" and eng.get("error"):
                        error_lines.append(f"- Tier A `{sample['id']}` ({eng_key}): {eng['error']}")
    if tier_b:
        for sample in tier_b["samples"]:
            if sample.get("status") == "failed" and sample.get("error"):
                error_lines.append(f"- Tier B `{sample['file_name']}`: {sample['error']}")
            else:
                for eng_key in ("local", "gemini"):
                    eng = sample.get(eng_key) or {}
                    if eng.get("status") == "failed" and eng.get("error"):
                        error_lines.append(f"- Tier B `{sample['file_name']}` ({eng_key}): {eng['error']}")
    if error_lines:
        lines.extend(["## Sample Processing Errors", ""])
        lines.extend(error_lines)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TuneChecker Two-Tier Transcription Benchmarking Engine (Faster-Whisper vs Ground Truth & Gemini)."
    )
    parser.add_argument(
        "--tier",
        choices=["all", "a", "b"],
        default="all",
        help="Benchmark tier to execute: 'a' (ground truth), 'b' (DataHive), or 'all' (default).",
    )
    parser.add_argument(
        "--dataset-slice",
        default="2",
        help="DataHive slice: integer count (e.g. 2), start:end slice, or comma-separated filenames (default: 2).",
    )
    parser.add_argument(
        "--models",
        default="local,gemini",
        help="Comma-separated models to run: subset of 'local,gemini' (default: local,gemini).",
    )
    parser.add_argument(
        "--output-dir",
        default="backend",
        help="Directory where BENCHMARK_REPORT.md and benchmark_results.json are written (default: backend).",
    )
    parser.add_argument(
        "--gemini-model",
        default=DEFAULT_GEMINI_MODEL,
        help=f"Gemini model identifier (default: {DEFAULT_GEMINI_MODEL}; supports gemini-3.5-transcribe).",
    )
    parser.add_argument(
        "--whisper-model",
        default=None,
        help="Optional override for Faster-Whisper model (defaults to settings.WHISPER_MODEL).",
    )
    parser.add_argument(
        "--language-mode",
        choices=["english", "hinglish", "hindi", "auto"],
        default="english",
        help="Override WHISPER_LANGUAGE_MODE during benchmark to prevent Hinglish prompt biasing (default: english).",
    )
    parser.add_argument(
        "--max-audio-seconds",
        type=float,
        default=None,
        help="Optional max audio duration in seconds to deterministically trim long audio files.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Use locally cached HuggingFace dataset snapshot only without network calls.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in deterministic offline mock mode without GPU, network, or API keys.",
    )
    args = parser.parse_args(argv)
    if args.max_audio_seconds is not None and (
        math.isnan(args.max_audio_seconds)
        or math.isinf(args.max_audio_seconds)
        or args.max_audio_seconds <= 0
    ):
        parser.error("--max-audio-seconds must be > 0")
    return args


def _resolve_output_dir(output_dir_arg: str) -> Path:
    p = Path(output_dir_arg)
    if p.is_absolute():
        return p
    return (REPO_ROOT / p).resolve()


def _parse_models_arg(models_arg: str) -> set[str]:
    valid = {"local", "gemini"}
    parsed = {m.strip().lower() for m in models_arg.split(",") if m.strip()}
    if not parsed or not parsed.issubset(valid):
        raise ValueError(f"Invalid --models '{models_arg}'. Must be subset of {sorted(valid)}.")
    return parsed


def run_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    from app.config import settings

    models = _parse_models_arg(args.models)
    output_dir = _resolve_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    whisper_model = args.whisper_model or settings.WHISPER_MODEL
    effective_gemini_model, deprecation_note = resolve_gemini_model(args.gemini_model)
    if deprecation_note:
        print(f"[WARN] {deprecation_note}")

    api_key_configured = bool(get_gemini_api_key())
    local_runner = None if args.mock else LocalWhisperRunner(args.whisper_model, args.language_mode)
    gemini_runner = None if args.mock else GeminiTranscriber(args.gemini_model)

    tier_a_payload: Optional[dict[str, Any]] = None
    tier_b_payload: Optional[dict[str, Any]] = None

    # --- Tier A ---
    if args.tier in ("all", "a"):
        gt_samples = load_tier_a_ground_truth()
        tier_a_samples_out: list[dict[str, Any]] = []

        for sample in gt_samples:
            audio_path = REPO_ROOT / sample["audio_path"]
            ref_text = sample["reference_transcript"]
            sample_error: Optional[str] = None

            if args.mock:
                eng_results = run_mock_tier_a(sample, models, whisper_model, effective_gemini_model)
                audio_dur = next(iter(eng_results.values())).audio_duration_seconds
            else:
                if not audio_path.exists():
                    raise FileNotFoundError(f"Tier A sample audio not found: {audio_path}")
                with tempfile.TemporaryDirectory() as trim_dir:
                    try:
                        eval_audio = audio_path if args.tier == "all" else maybe_trim_audio(audio_path, args.max_audio_seconds, Path(trim_dir))
                    except (RuntimeError, OSError) as exc:
                        sample_error = str(exc)
                        audio_dur = 0.0
                        eng_results = {}
                        if "local" in models:
                            eng_results["local"] = EngineResult(
                                engine="local",
                                model=f"faster-whisper:{whisper_model}",
                                status="failed",
                                error=sample_error,
                                cost_usd=0.0,
                                mode="live",
                            )
                        if "gemini" in models:
                            eng_results["gemini"] = EngineResult(
                                engine="gemini",
                                model=effective_gemini_model,
                                status="failed",
                                error=sample_error,
                                cost_usd=None,
                                mode="live",
                            )
                    else:
                        audio_dur = probe_audio_duration(eval_audio)
                        eng_results = {}
                        if "local" in models and local_runner is not None:
                            eng_results["local"] = local_runner.transcribe(eval_audio)
                        if "gemini" in models and gemini_runner is not None:
                            eng_results["gemini"] = gemini_runner.transcribe(
                                eval_audio,
                                audio_duration_sec=audio_dur,
                                language_mode=args.language_mode,
                            )

            sample_entry: dict[str, Any] = {
                "id": sample["id"],
                "audio_path": sample["audio_path"],
                "expected_verdict": sample.get("expected_verdict"),
                "audio_duration_seconds": round(audio_dur, 2),
                "reference_transcript": ref_text,
            }
            if sample_error is not None:
                sample_entry["status"] = "failed"
                sample_entry["error"] = sample_error

            for eng_key, res in eng_results.items():
                res_dict = asdict(res)
                if res.status == "ok" and res.text is not None:
                    res_dict["metrics"] = compute_transcription_metrics(ref_text, res.text)
                    res_dict["vocab_diff"] = compute_vocab_diff(ref_text, res.text)
                else:
                    res_dict["metrics"] = None
                    res_dict["vocab_diff"] = None
                sample_entry[eng_key] = res_dict

            tier_a_samples_out.append(sample_entry)

        tier_a_payload = {
            "description": "Faster-Whisper (and optional Gemini) vs. Human/TTS Ground Truth on TuneChecker sample calls",
            "fixture_path": str(TIER_A_FIXTURE_PATH.relative_to(REPO_ROOT)),
            "samples": tier_a_samples_out,
            "aggregate": {
                "local": _aggregate_engine_tier_a(tier_a_samples_out, "local") if "local" in models else None,
                "gemini": _aggregate_engine_tier_a(tier_a_samples_out, "gemini") if "gemini" in models else None,
            },
        }

    # --- Tier B ---
    if args.tier in ("all", "b"):
        dh_items, dh_meta = load_datahive_slice(
            args.dataset_slice,
            local_files_only=args.local_files_only,
            mock=args.mock,
        )
        tier_b_samples_out: list[dict[str, Any]] = []

        for item in dh_items:
            sample_error: Optional[str] = None
            if args.mock:
                eng_results = run_mock_tier_b(item, models, whisper_model, effective_gemini_model)
                dur = float(item.get("duration_seconds") or 0.0)
            else:
                audio_path = Path(item["audio_path"])
                if not audio_path.exists():
                    raise FileNotFoundError(f"DataHive audio file missing: {audio_path}")
                with tempfile.TemporaryDirectory() as trim_dir:
                    try:
                        eval_audio = maybe_trim_audio(audio_path, args.max_audio_seconds, Path(trim_dir))
                    except (RuntimeError, OSError) as exc:
                        sample_error = str(exc)
                        dur = float(item.get("duration_seconds") or 0.0)
                        eng_results = {}
                        if "local" in models:
                            eng_results["local"] = EngineResult(
                                engine="local",
                                model=f"faster-whisper:{whisper_model}",
                                status="failed",
                                error=sample_error,
                                cost_usd=0.0,
                                mode="live",
                            )
                        if "gemini" in models:
                            eng_results["gemini"] = EngineResult(
                                engine="gemini",
                                model=effective_gemini_model,
                                status="failed",
                                error=sample_error,
                                cost_usd=None,
                                mode="live",
                            )
                    else:
                        dur = probe_audio_duration(eval_audio) or float(item.get("duration_seconds") or 0.0)
                        eng_results = {}
                        if "local" in models and local_runner is not None:
                            eng_results["local"] = local_runner.transcribe(eval_audio)
                        if "gemini" in models and gemini_runner is not None:
                            eng_results["gemini"] = gemini_runner.transcribe(
                                eval_audio,
                                audio_duration_sec=dur,
                                language_mode=args.language_mode,
                            )

            sample_entry = {
                "file_name": item["file_name"],
                "topic": item.get("topic", "unknown"),
                "duration_seconds": round(dur, 2),
                "turns_per_minute": item.get("turns_per_minute"),
                "overlap_percent": item.get("overlap_percent"),
                "local": asdict(eng_results["local"]) if "local" in eng_results else None,
                "gemini": asdict(eng_results["gemini"]) if "gemini" in eng_results else None,
            }
            if sample_error is not None:
                sample_entry["status"] = "failed"
                sample_entry["error"] = sample_error

            loc = eng_results.get("local")
            gem = eng_results.get("gemini")
            if loc and loc.status == "ok" and loc.text is not None and gem and gem.status == "ok" and gem.text is not None:
                comp_metrics = compute_transcription_metrics(gem.text, loc.text)
                vocab_diff = compute_vocab_diff(gem.text, loc.text)
                sample_entry["cross_model_comparison"] = {
                    "status": "ok",
                    **comp_metrics,
                    "vocab_diff": vocab_diff,
                }
            elif gem and gem.status != "ok":
                sample_entry["cross_model_comparison"] = {
                    "status": gem.status,
                    "wer_percent": None,
                    "cer_percent": None,
                    "substitutions": None,
                    "deletions": None,
                    "insertions": None,
                    "reason": gem.error or f"Gemini status: {gem.status}",
                    "vocab_diff": None,
                }
            else:
                sample_entry["cross_model_comparison"] = {
                    "status": "not_available",
                    "wer_percent": None,
                    "cer_percent": None,
                    "vocab_diff": None,
                }

            tier_b_samples_out.append(sample_entry)

        tier_b_payload = {
            "dataset": DATAHIVE_DATASET_ID,
            "dataset_meta": dh_meta,
            "description": "Cross-model divergence benchmark (Faster-Whisper vs. Gemini reference; dataset has no human transcripts)",
            "samples": tier_b_samples_out,
            "aggregate": _aggregate_tier_b(tier_b_samples_out),
        }

    def _pkg_ver(name: str) -> str:
        try:
            return importlib.metadata.version(name)
        except Exception:
            return "unknown"

    results = {
        "metadata": {
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mock_mode": bool(args.mock),
            "tier": args.tier,
            "models_requested": sorted(models),
            "whisper_model": whisper_model,
            "language_mode": args.language_mode,
            "requested_gemini_model": args.gemini_model,
            "effective_gemini_model": effective_gemini_model,
            "deprecation_note": deprecation_note,
            "gemini_api_key_configured": api_key_configured,
            "dataset_slice": args.dataset_slice,
            "max_audio_seconds": args.max_audio_seconds,
            "local_files_only": bool(args.local_files_only),
            "jiwer_version": _pkg_ver("jiwer"),
            "google_genai_version": _pkg_ver("google-genai"),
            "faster_whisper_version": _pkg_ver("faster-whisper"),
        },
        "tier_a": tier_a_payload,
        "tier_b": tier_b_payload,
    }

    report_path = output_dir / "BENCHMARK_REPORT.md"
    json_path = output_dir / "benchmark_results.json"

    report_md = generate_markdown_report(results)
    report_path.write_text(report_md, encoding="utf-8")
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"Benchmark complete ({'MOCK' if args.mock else 'LIVE'}).")
    print(f"Report written to : {report_path}")
    print(f"JSON written to   : {json_path}")
    return results


def main(argv: Optional[list[str]] = None) -> int:
    try:
        args = parse_args(argv)
        run_benchmark(args)
        return 0
    except (ValueError, FileNotFoundError, FileExistsError, NotADirectoryError, RuntimeError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
