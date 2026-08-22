# -*- coding: utf-8 -*-
"""Unit checks for Walk→Map focus handoff (no Streamlit runtime).

    python tools/test_walk_map_handoff.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.ui_walk_land import (
    MAP_FOCUS_KEY,
    MAP_FOCUS_LABEL_KEY,
    apply_map_focus,
    map_focus_payload,
)

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def main():
    print("== map_focus_payload ==")
    p = map_focus_payload("Okhema", "Okhema — Eternal Holy City")
    check("payload has place key", p.get(MAP_FOCUS_KEY) == "Okhema", str(p))
    check(
        "payload has label key",
        p.get(MAP_FOCUS_LABEL_KEY) == "Okhema — Eternal Holy City",
        str(p),
    )
    p2 = map_focus_payload("Styxia")
    check("label optional", MAP_FOCUS_LABEL_KEY not in p2 and p2[MAP_FOCUS_KEY] == "Styxia")
    p3 = map_focus_payload("  Grove of Epiphany  ", "  Grove  ")
    check("strips whitespace", p3[MAP_FOCUS_KEY] == "Grove of Epiphany")

    print("== apply_map_focus (session_state-like) ==")
    state = {}
    apply_map_focus(state, "Aidonia", label="Aidonia / Memortis Shore")
    check("focus key readable", state.get(MAP_FOCUS_KEY) == "Aidonia")
    check(
        "label key readable",
        state.get(MAP_FOCUS_LABEL_KEY) == "Aidonia / Memortis Shore",
    )
    # Simulate Map tab reading the same keys
    focus = (state.get(MAP_FOCUS_KEY) or "").strip() or None
    check("map tab can read focus", focus == "Aidonia")

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        sys.exit(1)


if __name__ == "__main__":
    main()
