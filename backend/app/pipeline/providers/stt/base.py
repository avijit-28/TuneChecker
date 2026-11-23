from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

@dataclass
class SttWord:
    word: str
    start_ms: int
    end_ms: int
    confidence: Optional[float] = None

@dataclass
class SttSegment:
    id: str
    text: str
    start_ms: int
    end_ms: int
    words: list[SttWord]
    speaker_label: Optional[str] = None
    confidence: Optional[float] = None

@dataclass
class SttResult:
    segments: list[SttSegment]
    language: str
    duration_sec: float
    raw_payload: bytes

class BaseSttProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path) -> SttResult:
        pass
