# -*- coding: utf-8 -*-
"""Guest Walk gate: notice/touch OK; Heir-care chat operator-only.

    python tools/test_guest_walk_gate.py
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.ui_scene_life import heir_care_chat_blocked
from src.world import ecosystem as eco

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def _walk_focus_call_kwargs() -> dict:
    """Parse render_walk_page's render_focus_strip call for gate kwargs."""
    src = (ROOT / "src" / "ui_walk_land.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = getattr(fn, "id", None) or getattr(fn, "attr", None)
        if name != "render_focus_strip":
            continue
        out = {}
        for kw in node.keywords:
            if kw.arg in {"heir_id", "read_only", "heir_name"}:
                try:
                    out[kw.arg] = ast.literal_eval(kw.value)
                except Exception:
                    out[kw.arg] = "<<expr>>"
        if out:
            return out
    return {}


def main():
    print("== heir_care_chat_blocked matrix ==")
    check(
        "operator Visit with heir: care open",
        heir_care_chat_blocked(
            read_only=False, is_guest=False, heir_id="phainon",
        )
        is False,
    )
    check(
        "guest Visit with heir: care blocked",
        heir_care_chat_blocked(
            read_only=True, is_guest=True, heir_id="phainon",
        )
        is True,
    )
    check(
        "guest flag alone blocks care",
        heir_care_chat_blocked(
            read_only=False, is_guest=True, heir_id="phainon",
        )
        is True,
    )
    check(
        "Walk (empty heir + read_only): care blocked",
        heir_care_chat_blocked(
            read_only=True, is_guest=False, heir_id="",
        )
        is True,
    )
    check(
        "Walk as guest still blocked",
        heir_care_chat_blocked(
            read_only=True, is_guest=True, heir_id="",
        )
        is True,
    )
    check(
        "whitespace heir_id counts as missing",
        heir_care_chat_blocked(
            read_only=False, is_guest=False, heir_id="   ",
        )
        is True,
    )

    print("== Walk land wires gate ==")
    walk_kw = _walk_focus_call_kwargs()
    check("Walk focus strip found", bool(walk_kw), str(walk_kw))
    check(
        "Walk passes heir_id empty",
        walk_kw.get("heir_id") == "",
        str(walk_kw),
    )
    check(
        "Walk passes read_only True",
        walk_kw.get("read_only") is True,
        str(walk_kw),
    )

    print("== visitor_touch does not write Heir chat ==")
    check(
        "visitor_touch docstring: no Heir write",
        "No Heir write" in (eco.visitor_touch.__doc__ or ""),
    )
    # Source contract: care chat hist.append lives only behind the gate helper.
    scene_src = (ROOT / "src" / "ui_scene_life.py").read_text(encoding="utf-8")
    check(
        "focus strip uses heir_care_chat_blocked",
        "heir_care_chat_blocked(" in scene_src
        and "care_blocked = heir_care_chat_blocked" in scene_src,
    )
    check(
        "chat hist.append only after apply_care path",
        'hist.append({' in scene_src
        and "eco.apply_care" in scene_src,
    )

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        sys.exit(1)


if __name__ == "__main__":
    main()
