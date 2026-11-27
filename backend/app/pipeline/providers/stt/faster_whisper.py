import json
import gzip
import logging
import uuid
from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel
from app.config import settings
from app.pipeline.providers.stt.base import BaseSttProvider, SttResult, SttSegment, SttWord
from app.utils.errors import AppError

logger = logging.getLogger("tunechecker.stt.faster_whisper")

_DEVANAGARI_VOWELS = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
    "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
}
_DEVANAGARI_MATRAS = {
    "ा": "a", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo",
    "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
    "ं": "n", "ँ": "n", "ः": "h", "्": "",
}
_DEVANAGARI_CONSONANTS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "ny",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh",
    "ष": "sh", "स": "s", "ह": "h", "क़": "q", "ख़": "kh",
    "ग़": "gh", "ज़": "z", "ड़": "d", "ढ़": "dh", "फ़": "f",
}
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९।", "0123456789.")


def devanagari_to_roman(text: str) -> str:
    """Lightweight deterministic Devanagari-to-Roman Hinglish transliterator."""
    if not text or not any("\u0900" <= ch <= "\u097F" for ch in text):
        return text
    text = text.translate(_DEVANAGARI_DIGITS)
    out: list[str] = []
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        # Handle nukta digraphs (consonant + \u093c)
        if i + 1 < n and text[i + 1] == "\u093c" and (ch + "\u093c") in _DEVANAGARI_CONSONANTS:
            ch = ch + "\u093c"
            i += 1
        if ch in _DEVANAGARI_CONSONANTS:
            out.append(_DEVANAGARI_CONSONANTS[ch])
            nxt = text[i + 1] if i + 1 < n else ""
            if nxt in _DEVANAGARI_MATRAS:
                out.append(_DEVANAGARI_MATRAS[nxt])
                i += 1
            elif nxt and (nxt in _DEVANAGARI_CONSONANTS or nxt in _DEVANAGARI_VOWELS):
                # Schwa retention inside word; word-final consonant drops implicit 'a'
                out.append("a")
        elif ch in _DEVANAGARI_VOWELS:
            out.append(_DEVANAGARI_VOWELS[ch])
        elif ch in _DEVANAGARI_MATRAS:
            out.append(_DEVANAGARI_MATRAS[ch])
        else:
            out.append(ch)
        i += 1
    return "".join(out)

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

    @staticmethod
    def _collect_segments(segments_gen) -> tuple[list[SttSegment], list[dict]]:
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
        return stt_segments, raw_segments

    def transcribe(self, audio_path: Path) -> SttResult:
        try:
            model = self.get_model()

            # Select language and prompt based on WHISPER_LANGUAGE_MODE
            mode = getattr(settings, "WHISPER_LANGUAGE_MODE", "hinglish").lower()
            if mode == "hinglish":
                # Decode with Whisper's native Hindi+English code-switching ('hi') to avoid English hallucinations,
                # then transliterate Devanagari output to Roman Hinglish.
                lang_param = "hi"
                initial_prompt_val = (
                    "यह ग्राहक बिक्री और सहायता कॉल हिंदी और हिंग्लिश में है। "
                    "Haan, boliye, product details, pricing, discount, order details, kaju, kishmish, kilo."
                )
            elif mode == "hindi":
                lang_param = "hi"
                initial_prompt_val = "यह ग्राहक बिक्री और सहायता कॉल हिंदी और हिंग्लिश में है। उत्पाद, मूल्य निर्धारण, छूट, रिफंड और सेवा की बातचीत।"
            elif mode == "english":
                lang_param = "en"
                initial_prompt_val = (
                    "Customer sales and support call. Topics include product features, subscription, pricing, onboarding, "
                    "discount, invoice, refund policy, deadlines, commitments, and professional customer service."
                )
            else:
                lang_param = settings.WHISPER_LANGUAGE
                initial_prompt_val = settings.WHISPER_INITIAL_PROMPT

            vad_params = dict(
                threshold=0.25,
                min_speech_duration_ms=100,
                min_silence_duration_ms=400,
                speech_pad_ms=400
            )
            no_speech_thresh = getattr(settings, "WHISPER_NO_SPEECH_THRESHOLD", 0.85)

            def _run_whisper(language: Optional[str], use_vad: bool):
                kwargs = dict(
                    beam_size=settings.WHISPER_BEAM_SIZE,
                    language=language,
                    initial_prompt=initial_prompt_val,
                    vad_filter=use_vad,
                    condition_on_previous_text=settings.WHISPER_CONDITION_ON_PREVIOUS_TEXT,
                    no_speech_threshold=no_speech_thresh,
                    log_prob_threshold=settings.WHISPER_LOG_PROB_THRESHOLD,
                    word_timestamps=True,
                )
                if use_vad:
                    kwargs["vad_parameters"] = vad_params
                return model.transcribe(str(audio_path), **kwargs)

            segments_gen, info = _run_whisper(lang_param, use_vad=True)

            # If language was auto-detected with low confidence (< 0.40) and not English,
            # re-transcribe with language='en' to avoid spurious foreign language hallucinations
            if lang_param is None and info.language != "en" and getattr(info, "language_probability", 0.0) < 0.40:
                lang_param = "en"
                segments_gen, info = _run_whisper(lang_param, use_vad=True)

            stt_segments, raw_segments = self._collect_segments(segments_gen)

            # Production safeguard: if VAD dropped most of a >=25s call or cut off >25s early,
            # retry without VAD and keep whichever run captures more words.
            duration_sec = float(getattr(info, "duration", 0.0) or 0.0)
            speech_sec = sum(max(0, s.end_ms - s.start_ms) for s in stt_segments) / 1000.0
            last_end_sec = max((s.end_ms for s in stt_segments), default=0) / 1000.0
            low_coverage = (speech_sec / duration_sec) < 0.30 if duration_sec > 0 else False
            early_cutoff = (duration_sec - last_end_sec) > 25.0 and (speech_sec / duration_sec) < 0.45
            if duration_sec >= 25.0 and (len(stt_segments) < 3 or low_coverage or early_cutoff):
                logger.warning(
                    f"Low VAD speech coverage ({speech_sec:.1f}s / {duration_sec:.1f}s, "
                    f"{len(stt_segments)} segments); retrying without VAD filter."
                )
                fb_gen, fb_info = _run_whisper(lang_param, use_vad=False)
                fb_segments, fb_raw = self._collect_segments(fb_gen)
                orig_words = sum(len(s.text.split()) for s in stt_segments)
                fb_words = sum(len(s.text.split()) for s in fb_segments)
                if fb_words > orig_words:
                    stt_segments, raw_segments, info = fb_segments, fb_raw, fb_info

            if not stt_segments:
                raise AppError("STT_EMPTY_TRANSCRIPT", "Transcription returned empty result.", 422)

            if mode == "hinglish":
                for seg in stt_segments:
                    seg.text = devanagari_to_roman(seg.text)
                    for w in seg.words:
                        w.word = devanagari_to_roman(w.word)

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
