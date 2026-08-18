# -*- coding: utf-8 -*-
"""Lived day mechanisms — tick facts, contradictions, visitor vignette. No LLM."""
from __future__ import annotations

import inspect
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.world_state import WorldState
from src.world import lived_mechanisms as lm
from src.world import lived_entities as le
from src.world import vivid_stage2 as v2
from src.world.world_engine import WorldEngine

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def _ws(**clock):
    tmp = Path(tempfile.mkdtemp(prefix="amp-mech-"))
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
        "errands": {},
        "news": "The Dawn Device holds.",
    }
    ws.visitor_location = "Okhema"
    ws.visitor_travel = {}
    ws.surge = {"active": False, "remaining": 0, "cities": []}
    ws.save()
    return ws


def main():
    print("== Catalog ==")
    ids = [c["id"] for c in lm.CATALOG]
    check("seventeen mechanisms", len(lm.CATALOG) == 17, str(len(lm.CATALOG)))
    check("keeping time", "keeping_time" in ids)
    check("resting present", "resting" in ids)
    check("no burial mechanism", "burial" not in ids and "grave" not in ids)

    print("== Contradiction table ==")
    ws = _ws(period=4, month=6)
    ws.ambient["weather"]["Okhema"] = (
        "blazing and bright; the Dawn Device shines its strongest")
    snap = lm.derive(ws, place="Okhema")
    faults = lm.logic_faults(snap)
    check("no faults Curtain-Fall+blazing-weather", faults == [], str(faults))
    check("device withdrawn at Curtain-Fall", snap["flags"]["device_withdrawn"] is True)
    check("lighting not blazing at night", snap["flags"]["lighting"] == "withdrawn")
    check("market closed at Curtain-Fall", snap["flags"]["market_open"] is False)
    check("resting at Curtain-Fall", snap["flags"]["resting"] is True)
    check("forge not ringing at night", snap["flags"]["forge_ringing"] is False)
    joined = " ".join(snap["facts"]).lower()
    check("facts not high-and-hot at night", "stands high and hot" not in joined)
    check("facts not busiest at night", "busiest" not in joined)

    ws = _ws(period=0, month=9)
    snap = lm.derive(ws, place="Okhema")
    check("Entry is rest", snap["flags"]["resting"] is True)
    check("Entry does not open the market", snap["flags"]["market_open"] is False)
    check("Entry may kindle", snap["flags"]["lighting"] == "kindling")
    check("Entry not withdrawn (ordinary month)",
          snap["flags"]["device_withdrawn"] is False)
    check("no Entry faults", lm.logic_faults(snap) == [], str(lm.logic_faults(snap)))

    ws = _ws(period=2, month=9)
    ws.visitor_travel = {"to": "Styxia", "from": "Okhema", "remaining": 2}
    snap = lm.derive(ws)
    check("road sheltering", snap["flags"]["sheltering"] == "road")
    check("road not inside", snap["flags"]["sheltering"] != "inside")
    check("road market not open as square", snap["flags"]["market_open"] is False)
    check("no road faults", lm.logic_faults(snap) == [], str(lm.logic_faults(snap)))

    ws = _ws(period=1, month=9)
    snap = lm.derive(ws, place="Grove of Epiphany")
    facts = " ".join(snap["facts"]).lower()
    check("Grove no sea in facts", "the sea is at" not in facts and "harbor take" not in facts)
    check("Grove teaching at Lucid", snap["flags"]["teaching"] is True)
    check("Grove market is not a city square", snap["flags"]["market_open"] is False)
    check("Grove facts not a trading square",
          "square trades" not in facts, facts)
    check("no Grove faults", lm.logic_faults(snap) == [], str(lm.logic_faults(snap)))

    ws = _ws(period=2, month=4)
    snap = lm.derive(ws, place="Aedes Elysiae")
    check("Cultivation sows", snap["flags"]["harvest_phase"] == "sowing")
    check("Cultivation facts not reaping",
          "comes in" not in " ".join(snap["facts"]).lower()
          or "sowing" in " ".join(snap["facts"]).lower())
    check("no Cultivation faults", lm.logic_faults(snap) == [],
          str(lm.logic_faults(snap)))

    ws = _ws(period=2, month=8)
    snap = lm.derive(ws, place="Aedes Elysiae")
    check("Reaping phase", snap["flags"]["harvest_phase"] == "reaping")

    ws = _ws(period=1, month=3)
    ws.ambient["weather"]["Okhema"] = (
        "veiled and grey, sunlight weak as Oronyx's curtain hangs")
    snap = lm.derive(ws, place="Okhema")
    check("veiled not blazing", snap["flags"]["lighting"] == "veiled")
    check("no veiled-blaze faults", lm.logic_faults(snap) == [],
          str(lm.logic_faults(snap)))

    ws = _ws(period=2, month=9)
    ws.black_tide_enabled = True
    ws.surge = {"active": True, "remaining": 2, "cities": ["Okhema"]}
    snap = lm.derive(ws, place="Okhema")
    check("surge thins market", snap["flags"]["market_thin"] is True)
    check("surge not fullest square",
          "square trades at its fullest" not in " ".join(snap["facts"]).lower())
    check("no surge feast faults", lm.logic_faults(snap) == [],
          str(lm.logic_faults(snap)))

    print("== Tick mutates vivid.lived ==")
    ws = _ws(period=2, month=9)
    r1 = lm.apply_tick(ws)
    check("apply_tick flags present", bool(r1.get("flags")))
    check("apply_tick wrote facts", bool(r1.get("facts")))
    check("apply_tick wrote lines", bool(r1.get("lines")))
    check("vivid.lived exists", isinstance((ws.vivid or {}).get("lived"), dict))
    check("flags persisted", bool(ws.vivid["lived"].get("flags")))
    check("hearths fed this date",
          bool((ws.vivid["lived"].get("hearths_fed") or {}).get(lm.date_key(ws))))
    check("not idempotent first tick", r1.get("idempotent") is False)

    r2 = lm.apply_tick(ws)
    check("idempotent same clock key", r2.get("idempotent") is True)
    check("idempotent adds no lines", r2.get("lines") == [])
    n_dates = len(ws.vivid["lived"].get("hearths_fed") or {})
    check("feeding one date key so far", n_dates == 1, str(n_dates))

    ws.clock.period = 3
    r3 = lm.apply_tick(ws)
    check("new period not idempotent", r3.get("idempotent") is False)
    check("still one feeding date",
          len(ws.vivid["lived"]["hearths_fed"]) == 1)

    print("== Engine hook ==")
    src = inspect.getsource(WorldEngine.run_day)
    check("run_day calls lived apply_tick",
          "lived_mechanisms" in src and "apply_tick" in src)
    check("run_day calls resident apply_tick", "resident_npcs" in src)
    check("tick before rest return",
          src.find("apply_tick") < src.find("is_rest_time"))
    tsrc = inspect.getsource(WorldEngine._world_texture)
    check("texture gated by flags", "resting" in tsrc and "gathering" in tsrc)

    print("== Visitor vignette (not a catalog) ==")
    ws = _ws(period=4, month=9)
    lines = lm.visitor_stage_lines(ws, place="Okhema")
    blob = " ".join(lines).lower()
    check("vignette few lines", 1 <= len(lines) <= 4, str(len(lines)))
    check("Curtain-Fall vignette not busiest", "busiest" not in blob)
    check("Curtain-Fall mentions withdrawn or hearths or stalls",
          "withdrawn" in blob or "hearth" in blob or "stall" in blob, blob[:180])
    ws = _ws(period=1, month=9)
    gblob = " ".join(lm.visitor_stage_lines(ws, place="Grove of Epiphany")).lower()
    check("Grove vignette has no sea", "sea" not in gblob and "harbor" not in gblob,
          gblob)
    check("Grove vignette few lines",
          len(lm.visitor_stage_lines(ws, place="Grove of Epiphany")) <= 4)
    ws = _ws(period=2, month=9)
    para = lm.visitor_stage_paragraph(ws, place="Okhema")
    check("Action vignette names Okhema", "Okhema" in para)
    check("vignette is not 17-mechanism dump",
          para.count("Keeping time") + para.count("Washing") < 3)

    items = lm.gazette_world_items(ws)
    check("gazette handful not a catalog",
          1 <= len(items.get("facts") or []) <= 6,
          str(len(items.get("facts") or [])))
    gjoin = " ".join(items.get("facts") or [])
    check("gazette not 17 names", "Keeping time" not in gjoin)

    print("== Place-hour uses stage, not census ==")
    ws = _ws(period=2, month=9)
    ws.set_location("aglaea", "Okhema")
    frame = v2.place_hour_frame(ws, "aglaea", name_of=lambda c: c)
    check("frame has stage paragraph", bool(frame.get("stage_paragraph")))
    md = v2.place_hour_markdown(frame, "Aglaea")
    check("markdown has no entity dump header", "Lived world —" not in md)
    pb = v2.place_hour_prompt_block(frame)
    check("prompt forbids inventory weather", "second weather" in pb)

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILED:", FAILED)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
