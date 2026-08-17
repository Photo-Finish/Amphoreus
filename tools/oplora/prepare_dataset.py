"""Deprecated thin wrapper — prefer shape_training_data.py (databank copies)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    script = Path(__file__).with_name("shape_training_data.py")
    cmd = [sys.executable, str(script), "--clean", *sys.argv[1:]]
    print("Delegating to shape_training_data.py (duplicates databank; originals untouched).")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
