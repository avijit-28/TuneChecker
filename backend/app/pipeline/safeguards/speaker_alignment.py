from typing import Any
from app.pipeline.providers.stt.base import SttSegment

def align_segments_to_speakers(segments: list[SttSegment]) -> list[SttSegment]:
    """
    Assigns speaker labels ('A', 'B') to segments based on pause boundaries
    and conversational alternation if external diarizer is not present.
    In two-speaker phone calls, speakers typically alternate when pauses exceed ~400ms.
    """
    if not segments:
        return []

    labeled_segments: list[SttSegment] = []
    current_speaker = "A"
    last_end_ms = 0

    for idx, seg in enumerate(segments):
        pause = seg.start_ms - last_end_ms
        # Turn-taking between speakers on phone calls typically occurs across pauses > 1200ms
        # or when a speaker stops. Monologues with short breath pauses (< 1200ms) belong to the same speaker.
        if idx > 0 and pause > 1200:
            current_speaker = "B" if current_speaker == "A" else "A"

        seg.speaker_label = current_speaker
        labeled_segments.append(seg)
        last_end_ms = seg.end_ms

    return labeled_segments
