# -*- coding: utf-8 -*-
"""Stage-2 resident memory — named street people remember the visitor."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.world_state import WorldState
from src.world import resident_memory as rm
from src.world import resident_npcs as rn
from src.world import vivid_stage2 as v2

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def _ws(**clock):
    tmp = Path(tempfile.mkdtemp(prefix="amp-mem-"))
    ws = WorldState(str(tmp / "world_state.json"))
    ws.time_scale = 2.0
    for k, v in clock.items():
        setattr(ws.clock, k, v)
    ws.ambient = {
        "weather": {"Okhema": "clear and bright, the Dawn Device steady"},
        "news": "The Dawn Device holds.",
    }
    ws.visitor_location = "Okhema"
    ws.surge = {"active": False, "remaining": 0, "cities": []}
    ws.save()
    return ws


def main():
    print("== Bucket ==")
    ws = _ws(period=1, month=6, day=2, week=1)
    b = rm.memory_bucket(ws)
    check("bucket is dict", isinstance(b, dict))
    check("nested under vivid.resident_memory",
          ws.vivid.get("resident_memory") is b)

    print("== remember_meeting ==")
    rec1 = rm.remember_meeting(
        ws, "okhema-test-npc", name="Lysa", city="Okhema",
        line="Hello from the square.")
    check("meets starts at 1", rec1.get("meets") == 1, str(rec1))
    check("stores name city line day",
          rec1.get("name") == "Lysa"
          and rec1.get("city") == "Okhema"
          and "Hello" in (rec1.get("last_line") or "")
          and bool(rec1.get("last_day")))
    rec2 = rm.remember_meeting(
        ws, "okhema-test-npc", name="Lysa", city="Okhema", line="Again.")
    check("meets increments to 2", rec2.get("meets") == 2, str(rec2))

    print("== recognition_line ==")
    unknown = {"id": "never-met", "name": "Ghost", "city": "Okhema"}
    check("unknown has no recognition",
          rm.recognition_line(ws, unknown) is None)

    npc1 = {"id": "okhema-test-npc", "name": "Lysa", "city": "Okhema"}
    # After 2 meets, warmer line
    line_warm = rm.recognition_line(ws, npc1)
    check("meets>=2 warmer recognition",
          line_warm is not None and ("Back again" in line_warm
                                     or "Welcome back" in line_warm
                                     or "familiar" in line_warm.lower()),
          repr(line_warm))

    # Reset a one-meet NPC
    ws2 = _ws(period=1, month=6, day=3, week=1)
    rm.remember_meeting(ws2, "okhema-once", name="Meria", city="Okhema")
    line_once = rm.recognition_line(
        ws2, {"id": "okhema-once", "name": "Meria", "city": "Okhema"})
    check("meets==1 first-return acknowledgment",
          line_once is not None and (
              "again" in line_once.lower()
              or "recognition" in line_once.lower()
              or "spoken" in line_once.lower()
              or "passed" in line_once.lower()),
          repr(line_once))

    a = rm.recognition_line(
        ws2, {"id": "okhema-once", "name": "Meria", "city": "Okhema"})
    b_line = rm.recognition_line(
        ws2, {"id": "okhema-once", "name": "Meria", "city": "Okhema"})
    check("recognition deterministic", a == b_line)

    print("== npc_key ==")
    check("key prefers id",
          rm.npc_key({"id": "x-y", "name": "A", "city": "B"}) == "x-y")
    check("key from name+city slug",
          rm.npc_key({"name": "Eikura Shuu", "city": "Okhema"})
          == "okhema-eikura-shuu")

    print("== greet / talk wrappers ==")
    ws3 = _ws(period=1, month=6, day=4, week=1)  # Lucid Hour — markets open
    visible = rn.greet_here(ws3, "Okhema", limit=4)
    check("base greet returns people", len(visible) >= 1, str(len(visible)))
    if visible:
        first = visible[0]
        key = rm.npc_key(first)
        rm.remember_meeting(
            ws3, key, name=first["name"], city="Okhema", line="met")
        greets = rm.greet_with_memory(ws3, "Okhema", limit=4)
        known = [g for g in greets if g.get("id") == first.get("id")]
        check("greet_with_memory attaches recognition",
              known and "recognition" in known[0],
              str(known[0] if known else greets[:1]))

        # First talk — no prior recognition prepend
        talk1 = rm.talk_with_memory(ws3, "Okhema", first["name"])
        check("talk_with_memory ok", talk1.get("ok") is True, str(talk1))
        # Second talk — should prepend
        talk2 = rm.talk_with_memory(ws3, "Okhema", first["name"])
        check("returning talk prepends recognition",
              talk2.get("ok") and talk2.get("recognition")
              and str(talk2.get("line") or "").startswith(
                  talk2.get("recognition")),
              str(talk2.get("line", ""))[:120])
        mem = rm.memory_bucket(ws3).get(key) or {}
        check("talk increments meets",
              int(mem.get("meets") or 0) >= 2, str(mem))

    print("== vivid_stage2 wiring ==")
    ws4 = _ws(period=1, month=6, day=5, week=1)
    g = v2.greet_here(ws4, "Okhema", limit=3)
    check("v2.greet_here returns list", isinstance(g, list) and len(g) >= 1)
    if g:
        name = g[0]["name"]
        t1 = v2.talk_to_npc(ws4, "Okhema", name)
        t2 = v2.talk_to_npc(ws4, "Okhema", name)
        check("v2.talk_to_npc remembers across calls",
              t1.get("ok") and t2.get("ok") and t2.get("recognition"),
              str(t2)[:160])

    print()
    print(f"Passed: {len(PASSED)}  Failed: {len(FAILED)}")
    if FAILED:
        print("Failed checks:", ", ".join(FAILED))
        sys.exit(1)
    print("ALL OK")
    return 0


if __name__ == "__main__":
    main()
