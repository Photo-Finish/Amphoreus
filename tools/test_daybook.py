# -*- coding: utf-8 -*-
"""Stage-2 daybook — literary view over tick facts. No LLM."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.world_state import WorldState
from src.world import daybook as db
from src.world import lived_mechanisms as lm

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def _ws(**clock):
    tmp = Path(tempfile.mkdtemp(prefix="amp-day-"))
    ws = WorldState(str(tmp / "world_state.json"))
    ws.time_scale = 2.0
    for k, v in clock.items():
        setattr(ws.clock, k, v)
    ws.ambient = {
        "weather": {
            "Okhema": "clear and bright, the Dawn Device steady",
            "Styxia": "pale hush over the drowned quays",
        },
        "news": "The Dawn Device holds.",
    }
    ws.visitor_location = "Okhema"
    ws.surge = {"active": False, "remaining": 0, "cities": []}
    ws.save()
    return ws


def main():
    print("== compose shape ==")
    ws = _ws(period=1, month=6, day=2, week=1)
    lm.apply_tick(ws)
    rows = [
        {"kind": "encounter", "text": "Aglaea meets a weaver in the square.",
         "time": "now"},
        {"kind": "letter", "text": "A letter travels the roads toward Okhema.",
         "time": "now"},
        {"kind": "surge", "text": "The black tide presses the edge cities.",
         "time": "now"},
        {"kind": "flavor", "text": "Should be ignored flavor noise.",
         "time": "now"},
        {"kind": "encounter",
         "text": "Raw inventory dump {\"gold\": 12} and https://evil.example",
         "time": "now"},
    ]
    entry = db.compose_daybook(ws, rows, limit_facts=8)
    check("has title", entry.get("title") == "Today in Amphoreus")
    check("has date_label", bool(entry.get("date_label")))
    paras = entry.get("paragraphs") or []
    check("2–4 paragraphs", 2 <= len(paras) <= 4, str(len(paras)))
    facts = entry.get("facts") or []
    check("facts is list capped", isinstance(facts, list) and len(facts) <= 8,
          str(len(facts)))
    joined = " ".join(paras).lower()
    check("mentions Amphoreus life tone",
          "live" in joined or "amphoreus" in joined or "day" in joined)
    check("pulls ambient news into facts or prose",
          "Dawn Device" in " ".join(paras + facts)
          or "dawn device" in joined)

    print("== chronicle filter / sanitize ==")
    blob = " ".join(facts + paras)
    check("includes encounter/letter/surge text",
          "weaver" in blob or "letter" in blob.lower() or "tide" in blob.lower(),
          blob[:200])
    check("rejects inventory/url dumps",
          "gold" not in blob.lower() and "https://" not in blob.lower()
          and "{\"gold\"" not in blob)

    print("== determinism ==")
    e2 = db.compose_daybook(ws, rows, limit_facts=8)
    check("deterministic compose",
          e2 == entry, "paragraphs differ")

    print("== markdown ==")
    md = db.daybook_markdown(entry)
    check("markdown has heading", md.lstrip().startswith("### "))
    check("markdown has italic date", "*" in md and entry["date_label"] in md)
    check("markdown includes a paragraph",
          any(p in md for p in paras))

    print("== empty / sparse world ==")
    ws_empty = _ws(period=2, month=1, day=1, week=1)
    ws_empty.ambient = {}
    sparse = db.compose_daybook(ws_empty, None, limit_facts=4)
    check("sparse world still 2–4 paragraphs",
          2 <= len(sparse.get("paragraphs") or []) <= 4)
    check("limit_facts respected",
          len(sparse.get("facts") or []) <= 4)

    print()
    print(f"Passed: {len(PASSED)}  Failed: {len(FAILED)}")
    if FAILED:
        print("Failed checks:", ", ".join(FAILED))
        sys.exit(1)
    print("ALL OK")
    return 0


if __name__ == "__main__":
    main()
