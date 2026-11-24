import os, sys
os.chdir('D:/avi/TuneChecker/backend')
sys.path.insert(0, '.')
from pathlib import Path
from app.config import settings
settings.WHISPER_LANGUAGE_MODE = "english"

from app.audio.normalize import normalize_to_wav
from app.pipeline.providers.stt.faster_whisper import FasterWhisperProvider
from app.pipeline.safeguards.speaker_alignment import align_segments_to_speakers

audio_src = Path('C:/Users/avijitpakhira/.gemini/antigravity/brain/760c9929-3067-4768-bc96-e6835e869f6d/.user_uploaded/media_1795518777984_fae6b537.mpeg')
norm_wav = Path('./data/audio/benchmark_sample.wav')
norm_wav.parent.mkdir(parents=True, exist_ok=True)

print("Normalizing audio...")
normalize_to_wav(audio_src, norm_wav)

print("Transcribing with Faster-Whisper (English mode)...")
stt = FasterWhisperProvider()
result = stt.transcribe(norm_wav)
segments = result.segments
print(f"Extracted {len(segments)} segments, detected language: {result.language}")

print("Diarizing speakers with acoustic clustering...")
aligned = align_segments_to_speakers(segments, norm_wav)

output_lines = []
for s in aligned:
    line = f"[{s.start_ms/1000:05.1f}s - {s.end_ms/1000:05.1f}s] Speaker {s.speaker_label}: {s.text}"
    print(line)
    output_lines.append(line)

with open("./data/audio/benchmark_whisper_transcript.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print("\nSaved transcript to ./data/audio/benchmark_whisper_transcript.txt")
