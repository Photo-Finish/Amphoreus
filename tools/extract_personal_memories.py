"""
extract_personal_memories.py — rebuild per-Heir memory rollups from canon.

The databank is NEVER modified. This is a wrapper around
`tools/extract_mission_memories.py`, which splits every mission dialogue unit
into personal or collective memories and rewrites
`<HeirFolder>/personal-memories.md` for the voice digest.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from extract_mission_memories import main  # noqa: E402

if __name__ == "__main__":
    main()
