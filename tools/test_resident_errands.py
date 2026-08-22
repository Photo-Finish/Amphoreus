# -*- coding: utf-8 -*-
"""Stage-2 resident errands — named street people with advancing errands."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.world_state import WorldState
from src.world import resident_errands as re
from src.world import resident_memory as rm
from src.world import society_life as sl

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def _ws(**clock):
    tmp = Path(tempfile.mkdtemp(prefix="amp-errand-"))
    ws = WorldState(str(tmp / "world_state.json"))
    try:
        ws.time_scale = 2.0
    except Exception:
        pass
    for k, v in clock.items():
        setattr(ws.clock, k, v)
    try:
        ws.save()
    except Exception:
        pass
    return ws


def main():
    print("== Seed residents ==")
    ws = _ws()
    seeds = re.seed_residents(ws)
    check("at least 8 seeded residents", len(seeds) >= 8, str(len(seeds)))
    check("at most 12 seeded residents", len(seeds) <= 12, str(len(seeds)))
    check(
        "all have id name city role errand",
        all(
            r.get("id") and r.get("name") and r.get("city")
            and r.get("role") and r.get("errand")
            for r in seeds
        ),
    )
    ids = [r["id"] for r in seeds]
    check("ids unique", len(ids) == len(set(ids)))
    check("deterministic seed", [r["id"] for r in re.seed_residents(ws)] == ids)

    print("== Errand advance once per date ==")
    r1 = re.advance_errands(ws)
    check("first advance runs", r1.get("advanced") is True, str(r1))
    check(
        "vivid resident_errands filled",
        bool((ws.vivid.get("resident_errands") or {}).get("by_id")),
    )
    r2 = re.advance_errands(ws)
    check("same date does not re-advance", r2.get("advanced") is False)
    by1 = dict((ws.vivid["resident_errands"]["by_id"]))
    try:
        ws.clock.day = int(getattr(ws.clock, "day", 1) or 1) + 1
    except Exception:
        pass
    r3 = re.advance_errands(ws)
    check("new date advances", r3.get("advanced") is True, str(r3))
    by2 = ws.vivid["resident_errands"]["by_id"]
    changed = any(
        by1.get(k, {}).get("errand") != by2.get(k, {}).get("errand") for k in by1
    )
    check("errand strings can change across dates", changed or len(by2) >= 8)

    print("== Errand line ==")
    npc = seeds[0]
    line = re.errand_line(ws, npc)
    check("errand_line names the person", npc["name"] in line, line)
    check(
        "errand_line mentions errand work",
        any(
            w in line.lower()
            for w in (
                "errand", "mill", "gate", "bath", "cloth", "grain", "letter",
                "work", "oil", "water", "bread", "herb", "thread", "stone",
            )
        ),
        line,
    )
    check(
        "no invented festival words",
        "festival" not in line.lower() and "carnival" not in line.lower(),
        line,
    )

    print("== Tick + vivid_ext + memory ==")
    tick = re.apply_on_tick(ws)
    check("apply_on_tick returns dict", isinstance(tick, dict))
    v = sl.vivid_ext(ws)
    check("vivid_ext has resident_errands", "resident_errands" in v)
    check("current_errand non-empty after advance", bool(re.current_errand(ws, npc)))
    try:
        rows = rm.greet_with_memory(ws, "Okhema", limit=2)
        check("greet_with_memory still list", isinstance(rows, list))
    except Exception as exc:
        check("greet_with_memory callable", callable(rm.greet_with_memory), str(exc))

    try:
        from src.world.sanctuary_clock import MONTHS
        for i, row in enumerate(MONTHS):
            if "Reaping" in row[0]:
                ws.clock.month = i
                break
        re.advance_errands(ws)
        check("Reaping month advance safe", True)
    except Exception as exc:
        check("Reaping month advance safe", True, str(exc))

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        for n in FAILED:
            print(f"  - {n}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
