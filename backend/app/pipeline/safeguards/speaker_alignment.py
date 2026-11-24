from pathlib import Path
from typing import Optional
import numpy as np
import scipy.io.wavfile as wavfile
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from app.pipeline.providers.stt.base import SttSegment

def align_segments_to_speakers(segments: list[SttSegment], wav_path: Optional[Path] = None) -> list[SttSegment]:
    """
    Separates speakers using acoustic spectral clustering (MFCC/spectral centroid/energy ratios)
    when audio is available, with pause-based conversational alternation as fallback.
    """
    if not segments:
        return []

    # Acoustic spectral clustering
    if wav_path and Path(wav_path).exists() and len(segments) >= 4:
        try:
            sr, y = wavfile.read(str(wav_path))
            if y.dtype != np.float32:
                y = y.astype(np.float32) / 32768.0
            if y.ndim > 1:
                y = np.mean(y, axis=1)

            features = []
            for seg in segments:
                start_idx = max(0, int(seg.start_ms * sr / 1000))
                end_idx = min(len(y), int(seg.end_ms * sr / 1000))
                chunk = y[start_idx:end_idx]
                if len(chunk) < int(0.15 * sr):
                    chunk = y[start_idx : min(len(y), start_idx + int(0.15 * sr))]
                if len(chunk) == 0:
                    features.append([0.0] * 7)
                    continue

                rms = np.sqrt(np.mean(chunk**2) + 1e-9)
                zcr = np.mean(np.abs(np.diff(np.sign(chunk)))) / 2.0
                fft = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
                freqs = np.fft.rfftfreq(len(chunk), 1.0 / sr)

                sum_fft = np.sum(fft) + 1e-9
                spectral_centroid = np.sum(freqs * fft) / sum_fft
                spectral_spread = np.sqrt(np.sum(((freqs - spectral_centroid)**2) * fft) / sum_fft)

                low_e = np.sum(fft[freqs < 500]**2)
                mid_e = np.sum(fft[(freqs >= 500) & (freqs < 2000)]**2)
                high_e = np.sum(fft[freqs >= 2000]**2)
                total_e = low_e + mid_e + high_e + 1e-9

                features.append([
                    float(np.log(rms + 1e-9)),
                    float(zcr),
                    float(spectral_centroid),
                    float(spectral_spread),
                    float(low_e / total_e),
                    float(mid_e / total_e),
                    float(high_e / total_e)
                ])

            X = np.array(features)
            X_scaled = StandardScaler().fit_transform(X)
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10).fit(X_scaled)
            labels = kmeans.labels_

            # Normalize so the opening speaker is 'A' and respondent is 'B'
            first_label = labels[0]
            cluster_to_speaker = {first_label: "A", 1 - first_label: "B"}

            for seg, cluster in zip(segments, labels):
                seg.speaker_label = cluster_to_speaker[cluster]

            return segments
        except Exception:
            pass

    # Fallback to conversational pause alternation
    labeled_segments: list[SttSegment] = []
    current_speaker = "A"
    last_end_ms = 0

    for idx, seg in enumerate(segments):
        pause = seg.start_ms - last_end_ms
        if idx > 0 and pause > 1200:
            current_speaker = "B" if current_speaker == "A" else "A"

        seg.speaker_label = current_speaker
        labeled_segments.append(seg)
        last_end_ms = seg.end_ms

    return labeled_segments
