import logging
import tempfile
import wave
from pathlib import Path
from typing import Any, Optional
import numpy as np
from app.audio.ffmpeg import run_ffmpeg

logger = logging.getLogger("tunechecker.acoustics")

_SER_PIPELINE: Optional[Any] = None
_SER_FAILED: bool = False
_SER_LABEL_MAP = {
    "neu": "neutral",
    "hap": "happy",
    "ang": "angry",
    "sad": "sad",
}


def _get_ser_pipeline(device: int = -1):
    global _SER_PIPELINE, _SER_FAILED
    if _SER_FAILED:
        return None
    if _SER_PIPELINE is None:
        try:
            from transformers import pipeline  # type: ignore
            _SER_PIPELINE = pipeline(
                "audio-classification",
                model="superb/wav2vec2-base-superb-er",
                device=device,
            )
        except Exception as exc:
            logger.info(f"SER model unavailable, using prosody-only mode: {exc}")
            _SER_FAILED = True
            return None
    return _SER_PIPELINE


def _classify_emotions_batch(slices: list[tuple[str, np.ndarray]], sample_rate: int = 16000) -> dict[str, tuple[str, float]]:
    """Runs Speech Emotion Recognition on utterance PCM slices (GPU on ZeroGPU, graceful skip if unavailable)."""
    if not slices:
        return {}

    def _run(use_gpu: bool) -> dict[str, tuple[str, float]]:
        pipe = _get_ser_pipeline(device=0 if use_gpu else -1)
        if pipe is None:
            return {}
        out: dict[str, tuple[str, float]] = {}
        max_samples = sample_rate * 8
        for uid, seg in slices:
            try:
                clip = seg[:max_samples]
                preds = pipe({"raw": clip, "sampling_rate": sample_rate}, top_k=1)
                if preds and isinstance(preds, list):
                    raw_label = str(preds[0].get("label", "neu")).lower()
                    label = _SER_LABEL_MAP.get(raw_label, raw_label)
                    score = round(float(preds[0].get("score", 0.0)) * 100.0, 1)
                    out[uid] = (label, score)
            except Exception:
                continue
        return out

    try:
        import spaces  # type: ignore

        @spaces.GPU(duration=30)
        def _gpu_ser():
            return _run(use_gpu=True)

        return _gpu_ser()
    except ImportError:
        return {}
    except Exception:
        return _run(use_gpu=False)


def _estimate_f0_hz(samples: np.ndarray, sample_rate: int = 16000) -> float:
    """Fast autocorrelation pitch (F0) estimator in human speech range (70-350 Hz)."""
    if len(samples) < int(sample_rate * 0.05):
        return 0.0
    max_len = int(sample_rate * 0.5)
    if len(samples) > max_len:
        mid = len(samples) // 2
        seg = samples[mid - max_len // 2 : mid + max_len // 2]
    else:
        seg = samples

    seg = seg - np.mean(seg)
    energy = float(np.sum(seg * seg))
    if energy < 1e-6:
        return 0.0

    corr = np.correlate(seg, seg, mode="full")[len(seg) - 1 :]
    min_lag = max(1, int(sample_rate / 350))
    max_lag = min(len(corr) - 1, int(sample_rate / 70))
    if max_lag <= min_lag:
        return 0.0

    window = corr[min_lag : max_lag + 1]
    peak_idx = int(np.argmax(window))
    if corr[0] <= 0 or window[peak_idx] < 0.25 * corr[0]:
        return 0.0
    return float(sample_rate / (min_lag + peak_idx))


def analyze_utterance_acoustics(
    audio_path: Path,
    utterances: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Computes per-utterance acoustic prosody features (RMS dBFS, F0 pitch, ZCR)
    plus Speech Emotion Recognition (SER: angry/happy/sad/neutral) when available.
    Returns a mapping of utterance_id -> acoustic metadata + human-readable tag.
    """
    if not audio_path or not audio_path.exists() or not utterances:
        return {}

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "acoustics_16k.wav"
            proc = run_ffmpeg(
                ["-y", "-i", str(audio_path), "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav_path)],
                timeout=20,
            )
            if proc.returncode != 0 or not wav_path.exists():
                return {}

            with wave.open(str(wav_path), "rb") as w:
                sr = w.getframerate()
                raw = w.readframes(w.getnframes())

            pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if len(pcm) == 0:
                return {}

            raw_metrics: list[tuple[str, float, float, float]] = []
            ser_slices: list[tuple[str, np.ndarray]] = []
            for u in utterances:
                uid = str(u["id"])
                s_idx = max(0, int((u.get("start_ms", 0) / 1000.0) * sr))
                e_idx = min(len(pcm), int((u.get("end_ms", 0) / 1000.0) * sr))
                seg = pcm[s_idx:e_idx]
                if len(seg) < int(sr * 0.1):
                    raw_metrics.append((uid, -60.0, 0.0, 0.0))
                    continue

                if len(seg) >= int(sr * 0.25):
                    ser_slices.append((uid, seg))

                rms = float(np.sqrt(np.mean(seg * seg)) + 1e-9)
                rms_db = float(20.0 * np.log10(rms))
                zcr = float(np.mean(np.abs(np.diff(np.signbit(seg)))))
                f0 = _estimate_f0_hz(seg, sr)
                raw_metrics.append((uid, rms_db, f0, zcr))

            ser_map = _classify_emotions_batch(ser_slices, sample_rate=sr)

            valid_dbs = [m[1] for m in raw_metrics if m[1] > -55.0]
            valid_f0s = [m[2] for m in raw_metrics if m[2] > 0.0]
            valid_zcrs = [m[3] for m in raw_metrics if m[3] > 0.0]

            base_db = float(np.median(valid_dbs)) if valid_dbs else -25.0
            base_f0 = float(np.median(valid_f0s)) if valid_f0s else 150.0
            base_zcr = float(np.median(valid_zcrs)) if valid_zcrs else 0.08

            results: dict[str, dict[str, Any]] = {}
            for uid, rms_db, f0, zcr in raw_metrics:
                delta_db = round(rms_db - base_db, 1)
                f0_ratio = round((f0 / base_f0) if (f0 > 0 and base_f0 > 0) else 1.0, 2)
                zcr_ratio = round((zcr / base_zcr) if (zcr > 0 and base_zcr > 0) else 1.0, 2)

                ser_info = ser_map.get(uid)
                ser_prefix = f"Emotion: {ser_info[0]} ({ser_info[1]}%), " if ser_info else ""

                if (ser_info and ser_info[0] == "angry" and ser_info[1] >= 55.0) or delta_db >= 5.5 or (delta_db >= 3.5 and f0_ratio >= 1.20):
                    emotion_hint = "loud_or_agitated"
                    tag = f"{ser_prefix}loud/agitated voice ({delta_db:+.1f}dB vs baseline, pitch x{f0_ratio})"
                elif zcr_ratio >= 1.35 or f0_ratio >= 1.25:
                    emotion_hint = "tense_or_sharp"
                    tag = f"{ser_prefix}tense/sharp voice (pitch x{f0_ratio}, sharpness x{zcr_ratio})"
                else:
                    emotion_hint = "calm_or_normal"
                    tag = f"{ser_prefix}calm/normal voice ({delta_db:+.1f}dB vs baseline)"

                results[uid] = {
                    "rms_db": round(rms_db, 1),
                    "delta_db": delta_db,
                    "f0_hz": round(f0, 1),
                    "f0_ratio": f0_ratio,
                    "zcr_ratio": zcr_ratio,
                    "ser_emotion": ser_info[0] if ser_info else None,
                    "ser_score": ser_info[1] if ser_info else None,
                    "emotion_hint": emotion_hint,
                    "tag": tag,
                }
            return results
    except Exception:
        return {}
