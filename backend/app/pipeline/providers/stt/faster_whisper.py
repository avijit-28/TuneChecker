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

            # Select language and prompt based on WHISPER_LANGUAGE_MODE
            mode = getattr(settings, "WHISPER_LANGUAGE_MODE", "hinglish").lower()
            if mode == "hinglish":
                lang_param = "en"
                initial_prompt_val = (
                    "Yeh customer sales call Hindi aur Hinglish me hai. Roman script me verbatim Hinglish me transcribe karo: "
                    "Haan, boliye, green packet khajoor do, pumpkin seeds, mix dry fruits, anjeer, do dena, teen dena."
                )
            elif mode == "hindi":
                lang_param = "hi"
                initial_prompt_val = "यह ग्राहक बिक्री कॉल हिंदी और हिंग्लिश में है। कृपया देवनागरी में ट्रांसक्राइब करें।"
            elif mode == "bengali":
                lang_param = "bn"
                initial_prompt_val = "কাস্টমার সেলস কল, অর্ডার, দাম, প্রোডাক্ট এবং ডেলিভারির কথা।"
            elif mode == "english":
                lang_param = "en"
                initial_prompt_val = "Customer sales call, product orders, quantities, pricing, delivery, English conversation."
            else:
                lang_param = settings.WHISPER_LANGUAGE
                initial_prompt_val = settings.WHISPER_INITIAL_PROMPT

            segments_gen, info = model.transcribe(
                str(audio_path),
                beam_size=settings.WHISPER_BEAM_SIZE,
                language=lang_param,
                initial_prompt=initial_prompt_val,
                vad_filter=True,
                condition_on_previous_text=settings.WHISPER_CONDITION_ON_PREVIOUS_TEXT,
                no_speech_threshold=settings.WHISPER_NO_SPEECH_THRESHOLD,
                log_prob_threshold=settings.WHISPER_LOG_PROB_THRESHOLD,
                word_timestamps=True
            )

            # If language was auto-detected with low confidence (< 0.40) and not English,
            # re-transcribe with language='en' to avoid spurious foreign language hallucinations
            if lang_param is None and info.language != "en" and getattr(info, "language_probability", 0.0) < 0.40:
                segments_gen, info = model.transcribe(
                    str(audio_path),
                    beam_size=settings.WHISPER_BEAM_SIZE,
                    language="en",
                    initial_prompt=initial_prompt_val,
                    vad_filter=True,
                    condition_on_previous_text=settings.WHISPER_CONDITION_ON_PREVIOUS_TEXT,
                    no_speech_threshold=settings.WHISPER_NO_SPEECH_THRESHOLD,
                    log_prob_threshold=settings.WHISPER_LOG_PROB_THRESHOLD,
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
