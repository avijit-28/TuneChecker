#!/usr/bin/env python3
"""
Backwards-compatible delegating shim for TuneChecker Transcription Benchmark.
Canonical implementation lives at `<repo_root>/scripts/benchmark_transcription.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from benchmark_transcription import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
