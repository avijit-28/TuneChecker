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
