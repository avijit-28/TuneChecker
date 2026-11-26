import os
import tempfile
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from app.config import settings
from app.db.models.calls import Call
from app.db.models.transcripts import Transcript
from app.db.models.speaker_roles import SpeakerRole
from app.db.models.utterances import Utterance
from app.audio.normalize import normalize_to_wav
from app.utils.pii import redact_pii
from app.pipeline.providers.stt.faster_whisper import FasterWhisperProvider
from app.pipeline.safeguards.speaker_alignment import align_segments_to_speakers

def surgically_infill_segments(aligned_segments: list, wav_path: Path) -> list:
    """
    Surgically infills low-confidence or inaudible segments using Gemini Audio API.
    Only triggered if GEMINI_API_KEY is configured and segments have low confidence (< 0.40) or empty/inaudible text.
    Cuts ONLY the specific 2-5 second slice to avoid unnecessary token consumption.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        return aligned_segments

    candidates = []
    for idx, seg in enumerate(aligned_segments):
        is_low_conf = getattr(seg, "confidence", None) is not None and seg.confidence < 0.40
        is_inaudible = "[inaudible]" in seg.text.lower() or seg.text.strip() == ""
        if (is_low_conf or is_inaudible) and (seg.end_ms - seg.start_ms) >= 800:
            candidates.append((idx, seg))
            if len(candidates) >= 3:
                break

    if not candidates:
        return aligned_segments

    try:
        from google import genai
        from google.genai import types
        # Set strict 4s timeout so it NEVER hangs on 503/429
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=4000))
        from app.audio.ffmpeg import run_ffmpeg

        for idx, seg in candidates:
            start_sec = max(0.0, (seg.start_ms - 150) / 1000.0)
            duration_sec = max(0.5, (seg.end_ms - seg.start_ms + 300) / 1000.0)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_slice:
                slice_path = Path(tmp_slice.name)
            try:
                cut_args = [
                    "-y",
                    "-ss", str(start_sec),
                    "-t", str(duration_sec),
                    "-i", str(wav_path),
                    "-c:a", "pcm_s16le",
                    str(slice_path)
                ]
                proc = run_ffmpeg(cut_args, timeout=5)
                if proc.returncode == 0 and slice_path.exists() and slice_path.stat().st_size > 1000:
                    uploaded = client.files.upload(file=str(slice_path))
                    resp = client.interactions.create(
                        model="gemini-3.5-flash",
                        input=[
                            {"type": "audio", "uri": uploaded.uri, "mime_type": "audio/wav"},
                            {"type": "text", "text": "Transcribe this short audio snippet verbatim in plain text. Only return the spoken words, nothing else."}
                        ],
                        store=False
                    )
                    infill_text = getattr(resp, "output_text", "")
                    if not infill_text:
                        for step in getattr(resp, "steps", None) or []:
                            if getattr(step, "type", None) in (None, "model_output"):
                                for item in getattr(step, "content", None) or []:
                                    t = getattr(item, "text", "")
                                    if t:
                                        infill_text += t
                    infill_text = infill_text.strip()
                    if infill_text and len(infill_text) > 1 and not infill_text.lower().startswith("inaudible"):
                        seg.text = infill_text
                        seg.confidence = 0.95
            except Exception:
                # If Gemini is busy, rate-limited (429/503), or times out, immediately break to avoid delaying transcription!
                break
            finally:
                if slice_path.exists():
                    try:
                        slice_path.unlink()
                    except Exception:
                        pass
    except Exception:
        # Fallback gracefully if API or network is unavailable
        pass

    return aligned_segments

def run_transcription_stage(db: Session, call_id: str) -> dict:
    call = db.query(Call).filter(Call.id == call_id).first()
    audio_path = Path(settings.STORAGE_LOCAL_PATH) / call.storage_key

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / f"{call_id}_16k.wav"
        normalize_to_wav(audio_path, wav_path)

        provider = FasterWhisperProvider()
        stt_result = provider.transcribe(wav_path)

        # Align utterances to acoustic speaker turns (A / B)
        aligned_segments = align_segments_to_speakers(stt_result.segments, wav_path=wav_path)

        # Apply surgical infilling for low-confidence gaps via Gemini Audio
        aligned_segments = surgically_infill_segments(aligned_segments, wav_path)

    speaker_labels = sorted(list({seg.speaker_label for seg in aligned_segments if seg.speaker_label}))
    if not speaker_labels:
        speaker_labels = ["A"]

    # 1. Create transcript record
    transcript = Transcript(
        call_id=call_id,
        status="completed",
        provider="faster_whisper",
        model=settings.WHISPER_MODEL,
        language=stt_result.language,
        speaker_count=len(speaker_labels),
        audio_seconds=stt_result.duration_sec,
        raw_response=stt_result.raw_payload
    )
    db.merge(transcript)

    # 2. Initialize speaker_roles as 'unknown / unresolved'
    for label in speaker_labels:
        role_row = SpeakerRole(
            call_id=call_id,
            speaker_label=label,
            role="unknown",
            source="auto",
            status="unresolved",
            level="low"
        )
        db.merge(role_row)
    db.commit()

    # 3. Create utterances
    db.query(Utterance).filter(Utterance.call_id == call_id).delete()
    for idx, seg in enumerate(aligned_segments):
        utt = Utterance(
            id=str(uuid.uuid4()),
            call_id=call_id,
            idx=idx,
            speaker_label=seg.speaker_label or "A",
            start_ms=seg.start_ms,
            end_ms=seg.end_ms,
            text=redact_pii(seg.text) if getattr(settings, "REDACT_PII", False) else seg.text,
            asr_confidence=seg.confidence,
            low_attribution=0
        )
        db.add(utt)
    db.commit()

    word_count = sum(len(s.text.split()) for s in aligned_segments)
    return {
        "message": f"Transcribed {len(aligned_segments)} utterances ({word_count} words).",
        "speaker_count": len(speaker_labels),
        "word_count": word_count
    }
