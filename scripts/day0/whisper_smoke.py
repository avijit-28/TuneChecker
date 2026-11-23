import time
from pathlib import Path
from faster_whisper import WhisperModel

def test_whisper():
    audio_path = Path("D:/avi/TuneChecker/samples/red_call_01.m4a")
    print(f"Loading faster-whisper model 'base' on CPU int8...")
    start_load = time.time()
    model = WhisperModel("base", device="cpu", compute_type="int8")
    print(f"Model loaded in {time.time() - start_load:.2f}s")
    
    print(f"Transcribing {audio_path.name}...")
    start_infer = time.time()
    segments, info = model.transcribe(str(audio_path), beam_size=5, word_timestamps=True)
    
    print(f"Detected language: {info.language} with probability {info.language_probability:.2f}")
    
    segment_list = list(segments)
    infer_time = time.time() - start_infer
    print(f"Transcription finished in {infer_time:.2f}s (Audio duration: {info.duration:.2f}s)")
    print(f"Speed: {info.duration / infer_time:.2f}x real-time")
    
    for seg in segment_list[:3]:
        print(f"[{seg.start:.2f} - {seg.end:.2f}] {seg.text}")
        if seg.words:
            print(f"  First word: '{seg.words[0].word}' ({seg.words[0].start:.2f} - {seg.words[0].end:.2f})")
            
    assert len(segment_list) > 0, "No segments returned"
    print("Faster-Whisper smoke test: PASS")

if __name__ == "__main__":
    test_whisper()
