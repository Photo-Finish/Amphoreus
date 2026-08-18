# -*- coding: utf-8 -*-
"""Lived entities + ambient visibility / no-fallacy cross-checks. No LLM."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.world_state import WorldState
from src.world import lived_entities as le
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
    tmp = Path(tempfile.mkdtemp(prefix="amp-ent-"))
    ws = WorldState(str(tmp / "world_state.json"))
    for k, v in clock.items():
        setattr(ws.clock, k, v)
    ws.ambient = {
        "weather": {
            "Okhema": "clear and bright, the Dawn Device steady",
            "Grove of Epiphany": "leaves and a mild air",
            "Styxia": "pale hush over the drowned quays",
            "Castrum Kremnos": "the ring of the forge on a clear day",
            "Aedes Elysiae": "harvest-scented breeze",
            "Aidonia": "still and grey candlelight",
        },
        "errands": {
            "aglaea": {"ask": "Walk the lower city.", "cause": "The looms ran late."},
        },
        "news": "The Dawn Device holds.",
    }
    ws.visitor_location = "Okhema"
    ws.visitor_travel = {}
    ws.surge = {"active": False, "remaining": 0, "cities": []}
    ws.save()
    return ws


def _row(snap, eid):
    return next(r for r in snap["entities"] if r["id"] == eid)


def main():
    print("== Catalog grain ==")
    ids = {c["id"] for c in le.CATALOG}
    check("no famine entity", "famine" not in ids)
    check("no plague entity", "plague" not in ids)
    check("no war entity", "war" not in ids)
    check("no storm-catastrophe entity", "storm" not in ids)
    check("no grave / burial entity", "grave" not in ids)
    check("dawn device present", "dawn_device" in ids)
    check("market present", "market" in ids)
    check("catalog count coarse", 20 <= len(le.CATALOG) <= 40)

    print("== Daylight Okhema ==")
    ws = _ws(period=2, month=9)  # Action Hour, Weaving
    snap = le.snapshot(ws, place="Okhema")
    faults = le.logic_faults(snap)
    check("no faults Action/Weaving/Okhema", faults == [], str(faults))
    check("ambient weather in snapshot", "Okhema" in snap["weather"])
    check("errands in snapshot", "aglaea" in snap["errands"])
    check("news in snapshot", "Dawn Device" in snap["news"])
    check("sky echoes Keeper", "clear" in _row(snap, "sky")["status"].lower())
    check("market busy-ish at Action", "busiest" in _row(snap, "market")["status"].lower())
    check("harvest not reaping in Weaving",
          "comes in" not in _row(snap, "harvest")["status"].lower())
    check("sea not HERE in Okhema", _row(snap, "sea")["presence"] != "here")
    check("mountain HERE in Okhema", _row(snap, "mountain")["presence"] == "here")
    here_ids = {r["id"] for r in le.here_entities(snap, limit=12)}
    check("chat does not inject sea in Okhema", "sea" not in here_ids)
    check("chat injects dawn device", "dawn_device" in here_ids)

    print("== Curtain-Fall vs blazing day ==")
    ws = _ws(period=4, month=6)
    ws.ambient["weather"]["Okhema"] = "blazing and bright; the Dawn Device shines its strongest"
    snap = le.snapshot(ws, place="Okhema")
    faults = le.logic_faults(snap)
    check("no faults night+blazing-day-weather", faults == [], str(faults))
    dawn = _row(snap, "dawn_device")["status"].lower()
    check("device withdrawn at night", "withdrawn" in dawn or "veil" in dawn or "sleep" in dawn)
    check("not still 'high and hot' at night", "stands high and hot" not in dawn)
    check("thief star out at curtain-fall", "is out" in _row(snap, "thief_star")["status"].lower())
    check("market not busiest at night",
          "busiest" not in _row(snap, "market")["status"].lower())
    check("market not opening at night",
          "opens with" not in _row(snap, "market")["status"].lower())

    print("== Veiled sky (Month of Evernight, Lucid Hour) ==")
    ws = _ws(period=1, month=3)
    ws.ambient["weather"]["Okhema"] = "veiled and grey, sunlight weak as Oronyx's curtain hangs"
    snap = le.snapshot(ws, place="Okhema")
    faults = le.logic_faults(snap)
    check("no faults veiled day", faults == [], str(faults))
    dawn = _row(snap, "dawn_device")["status"].lower()
    check("device behind veil", "veil" in dawn)
    check("not blazing under veil", "stands high and hot" not in dawn)

    print("== Grove: no sea, no forge ==")
    ws = _ws(period=1, month=9)
    snap = le.snapshot(ws, place="Grove of Epiphany")
    faults = le.logic_faults(snap)
    check("no faults Grove", faults == [], str(faults))
    check("grove HERE", _row(snap, "grove")["presence"] == "here")
    check("sea distant in Grove", _row(snap, "sea")["presence"] == "distant")
    check("forge distant in Grove", _row(snap, "forge")["presence"] == "distant")
    check("teaching HERE in Grove", _row(snap, "teaching")["presence"] == "here")
    inj = " ".join(r["id"] for r in le.here_entities(snap, limit=16))
    check("prompt set has no sea", "sea" not in inj)
    check("prompt set has no forge", "forge" not in inj)

    print("== Styxia shore ==")
    ws = _ws(period=2, month=5)
    snap = le.snapshot(ws, place="Styxia")
    check("sea HERE in Styxia", _row(snap, "sea")["presence"] == "here")
    check("harbor HERE in Styxia", _row(snap, "harbor")["presence"] == "here")
    check("river HERE in Styxia", _row(snap, "river_of_souls")["presence"] == "here")
    check("no Styxia faults", le.logic_faults(snap) == [], str(le.logic_faults(snap)))

    print("== Cultivation vs Reaping ==")
    ws = _ws(period=2, month=4)
    snap = le.snapshot(ws, place="Aedes Elysiae")
    check("sowing in Cultivation", "sowing" in _row(snap, "harvest")["status"].lower())
    check("fields HERE at Aedes", _row(snap, "fields")["presence"] == "here")
    check("no Cultivation harvest fault", le.logic_faults(snap) == [],
          str(le.logic_faults(snap)))
    ws = _ws(period=2, month=8)
    snap = le.snapshot(ws, place="Aedes Elysiae")
    check("reaping comes in", "comes in" in _row(snap, "harvest")["status"].lower())
    check("no Reaping faults", le.logic_faults(snap) == [], str(le.logic_faults(snap)))

    print("== Road vs house ==")
    ws = _ws(period=2, month=9)
    ws.visitor_travel = {"to": "Styxia", "from": "Okhema", "remaining": 2}
    snap = le.snapshot(ws)
    check("traveling flag", snap["traveling"] is True)
    check("dwelling not indoor-on-road",
          "keep this hour's weather off you" not in _row(snap, "dwelling")["status"].lower())
    check("road underfoot", "underfoot" in _row(snap, "road")["status"].lower())
    check("market distant on road", _row(snap, "market")["presence"] == "distant")
    check("no travel faults", le.logic_faults(snap) == [], str(le.logic_faults(snap)))

    print("== Surge thins market, does not invent famine ==")
    ws = _ws(period=2, month=9)
    ws.black_tide_enabled = True
    ws.surge = {"active": True, "remaining": 2, "cities": ["Okhema"]}
    snap = le.snapshot(ws, place="Okhema")
    m = _row(snap, "market")["status"].lower()
    check("surge market not busiest", "busiest" not in m)
    check("surge market thinner", "thinner" in m or "keep close" in m)
    harvest = _row(snap, "harvest")["status"].lower()
    check("no famine word", "famine" not in harvest)
    check("no surge faults", le.logic_faults(snap) == [], str(le.logic_faults(snap)))

    print("== Place-hour frame wires entities ==")
    ws = _ws(period=2, month=9)
    ws.set_location("aglaea", "Okhema")
    frame = v2.place_hour_frame(ws, "aglaea", name_of=lambda c: c)
    check("frame has entities", bool(frame.get("entities")))
    check("frame reports no faults", not frame.get("entity_faults"),
          str(frame.get("entity_faults")))
    md = v2.place_hour_markdown(frame, "Aglaea")
    check("markdown names place", "Okhema" in md)
    check("markdown has this-hour stage", "Hour" in md)
    check("markdown is not an entity dump", "Lived world —" not in md)
    pb = v2.place_hour_prompt_block(frame)
    check("prompt has stage", "hour you stand in" in pb.lower() or "Okhema" in pb)
    check("prompt forbids second weather", "second weather" in pb)

    print("== UI renderer import ==")
    from src.ui_world_stage import render_world_stage
    check("renderer exported", callable(render_world_stage))

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILED:", FAILED)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
