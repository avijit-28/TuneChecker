import pytest
from pathlib import Path
from app.audio.stereo import get_channel_count, split_stereo_channels

def test_channel_count_mono():
    # green_call_01.m4a is mono
    p = Path("D:/avi/TuneChecker/samples/green_call_01.m4a")
    if p.exists():
        assert get_channel_count(p) == 1

def test_split_non_existent_file():
    p = Path("D:/non_existent_audio.wav")
    assert split_stereo_channels(p, Path("D:/left.wav"), Path("D:/right.wav")) is False
