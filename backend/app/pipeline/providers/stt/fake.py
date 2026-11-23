import gzip
import json
from pathlib import Path
from app.pipeline.providers.stt.base import BaseSttProvider, SttResult, SttSegment, SttWord

class FakeSttProvider(BaseSttProvider):
    def __init__(self, segments: list[SttSegment] = None, fail_with: Exception = None):
        self.segments = segments or [
            SttSegment(
                id="fake-seg-1",
                text="Hello, thank you for calling Brightwave Software.",
                start_ms=0,
                end_ms=3000,
                words=[
                    SttWord("Hello,", 0, 800),
                    SttWord("thank", 850, 1200),
                    SttWord("you", 1250, 1500),
                    SttWord("for", 1550, 1800),
                    SttWord("calling", 1850, 2400),
                    SttWord("Brightwave", 2450, 2800),
                    SttWord("Software.", 2850, 3000),
                ]
            )
        ]
        self.fail_with = fail_with

    def transcribe(self, audio_path: Path) -> SttResult:
        if self.fail_with:
            raise self.fail_with
        raw = gzip.compress(json.dumps({"fake": True}).encode("utf-8"))
        return SttResult(
            segments=self.segments,
            language="en",
            duration_sec=3.0,
            raw_payload=raw
        )
