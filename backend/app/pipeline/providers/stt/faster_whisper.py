import json
import gzip
import uuid
from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel
from app.config import settings
from app.pipeline.providers.stt.base import BaseSttProvider, SttResult, SttSegment, SttWord
from app.utils.errors import AppError

class FasterWhisperProvider(BaseSttProvider):
    _model_instance: Optional[WhisperModel] = None

    @classmethod
    def get_model(cls) -> WhisperModel:
        if cls._model_instance is None:
            cls._model_instance = WhisperModel(
                settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE
            )
        return cls._model_instance

    def transcribe(self, audio_path: Path) -> SttResult:
        try:
            model = self.get_model()
            segments_gen, info = model.transcribe(
                str(audio_path),
                beam_size=5,
                language="en",
                word_timestamps=True
            )

            raw_segments = []
            stt_segments = []

            for seg in segments_gen:
                words_list = []
                if seg.words:
                    for w in seg.words:
                        words_list.append(SttWord(
                            word=w.word.strip(),
                            start_ms=int(w.start * 1000),
                            end_ms=int(w.end * 1000),
                            confidence=getattr(w, "probability", None)
                        ))

                stt_seg = SttSegment(
                    id=str(uuid.uuid4()),
                    text=seg.text.strip(),
                    start_ms=int(seg.start * 1000),
                    end_ms=int(seg.end * 1000),
                    words=words_list,
                    confidence=getattr(seg, "avg_logprob", None)
                )
                stt_segments.append(stt_seg)
                raw_segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "words": [{"word": w.word, "start": w.start, "end": w.end} for w in (seg.words or [])]
                })

            if not stt_segments:
                raise AppError("STT_EMPTY_TRANSCRIPT", "Transcription returned empty result.", 422)

            raw_dict = {
                "language": info.language,
                "duration": info.duration,
                "segments": raw_segments
            }
            compressed_raw = gzip.compress(json.dumps(raw_dict).encode("utf-8"))

            return SttResult(
                segments=stt_segments,
                language=info.language or "en",
                duration_sec=info.duration,
                raw_payload=compressed_raw
            )
        except AppError:
            raise
        except Exception as e:
            raise AppError("STT_PROVIDER_ERROR", f"Transcription error: {str(e)}", 500)
