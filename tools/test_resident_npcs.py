# -*- coding: utf-8 -*-
"""Stage-2 resident NPCs — roster, hour visibility, tick encounters. No LLM."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.world_state import WorldState
from src.world import resident_npcs as rn
from src.world import lived_mechanisms as lm
from src.world import lived_entities as le
from src.world import world_events as wev
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
    tmp = Path(tempfile.mkdtemp(prefix="amp-npc-"))
    ws = WorldState(str(tmp / "world_state.json"))
    for k, v in clock.items():
        setattr(ws.clock, k, v)
    ws.ambient = {
        "weather": {
            "Okhema": "clear and bright, the Dawn Device steady",
            "Grove of Epiphany": "leaves and a mild air",
            "Styxia": "pale hush over the drowned quays",
            "Aedes Elysiae": "a mild shore breeze",
        },
        "news": "The Dawn Device holds.",
    }
    ws.visitor_location = "Okhema"
    ws.surge = {"active": False, "remaining": 0, "cities": []}
    ws.save()
    return ws


def main():
    print("== Roster ==")
    gen = rn.generated_roster()
    living = rn.living_roster()
    check("roster 80–150", 80 <= len(gen) <= 150, str(len(gen)))
    cities = {n["city"] for n in gen}
    check("covers Okhema", "Okhema" in cities)
    check("covers Grove", "Grove of Epiphany" in cities)
    check("covers Styxia", "Styxia" in cities)
    check("covers Aedes", "Aedes Elysiae" in cities)
    grove_roles = {n["role"] for n in gen if n["city"] == "Grove of Epiphany"}
    check("Grove has no harbor-fishers",
          not (grove_roles & rn._SEA_ROLES), str(grove_roles))
    names = [n["name"].lower() for n in gen]
    check("no John/Sarah", "john" not in names and "sarah" not in names)
    fields = {"id", "name", "city", "role", "habitual_place",
              "temperament", "period_habit"}
    check("template fields present",
          all(fields <= set(n) for n in gen[:5]))

    print("== Copilot NPCS untouched + merge ==")
    copilot_names = [n["name"] for n in wev.NPCS]
    check("Copilot roster still six",
          copilot_names == [
              "Bartholos", "Seliose", "Noldus",
              "Researcher Eikura Shuu", "Mem", "Theodosia",
          ], str(copilot_names))
    living_names = {n["name"] for n in living}
    check("Bartholos in merged roster", "Bartholos" in living_names)
    src = (ROOT / "src" / "world" / "world_events.py").read_text(encoding="utf-8")
    check("world_events.NPCS still Bartholos block",
          '{"name": "Bartholos", "city": "Okhema"' in src)

    print("== Resting hour: no feast-square ==")
    ws = _ws(period=4, month=9)
    flags = lm.derive(ws, place="Okhema")["flags"]
    vis = rn.visible_in_city(ws, "Okhema", flags=flags)
    spots = {r.get("spot") for r in vis}
    blob = " ".join(
        (r.get("name") or "") + " " + (r.get("spot") or "") for r in vis
    ).lower()
    check("Curtain-Fall people exist", len(vis) >= 1, str(len(vis)))
    check("Curtain-Fall not at market square",
          "market" not in spots, str(spots))
    check("no square-is-yours on rest roster",
          "square is yours" not in blob)

    print("== Grove visible: no fishers here ==")
    ws = _ws(period=1, month=9)
    flags = lm.derive(ws, place="Grove of Epiphany")["flags"]
    gvis = rn.visible_in_city(ws, "Grove of Epiphany", flags=flags)
    groles = {r["role"] for r in gvis}
    check("Grove Lucid has students or scholars",
          bool(groles & {"grove-student", "scribe", "quiet scholar",
                         "healer's aide", "timber-warden", "leaf-binder"}),
          str(groles))
    check("Grove visible has no sea roles",
          not (groles & rn._SEA_ROLES), str(groles))

    print("== Tick writes encounters ==")
    ws = _ws(period=2, month=9)
    ws.set_location("aglaea", "Okhema")
    lm.apply_tick(ws)
    res = rn.apply_tick(ws, flags=ws.vivid["lived"]["flags"])
    check("encounters written", len(res.get("encounters") or []) >= 1,
          str(res.get("encounters")))
    check("visible_by_city persisted",
          "Okhema" in (res.get("visible_by_city") or {}))
    check("vivid.residents last_key",
          bool((ws.vivid.get("residents") or {}).get("last_key")))
    line = (res["encounters"][0].get("line") or "")
    enc0 = res["encounters"][0]
    check("encounter names a person and a place",
          bool(enc0.get("resident") and enc0.get("heir") and enc0.get("city")
               and enc0.get("line")), line)
    check("encounter is not a death",
          "die" not in line and "grave" not in line and "bury" not in line)

    res2 = rn.apply_tick(ws, flags=ws.vivid["lived"]["flags"])
    check("resident tick idempotent", res2.get("idempotent") is True)
    check("idempotent no new lines", res2.get("lines") == [])

    print("== Resting tick: no feast claim ==")
    ws = _ws(period=4, month=9)
    ws.set_location("aglaea", "Okhema")
    lm.apply_tick(ws)
    resn = rn.apply_tick(ws, flags=ws.vivid["lived"]["flags"])
    elines = " ".join(e.get("line") or "" for e in resn.get("encounters") or []).lower()
    check("rest encounter not square-is-yours",
          "square is yours" not in elines and "busiest" not in elines, elines)

    print("== talk_to_npc merge + hour ==")
    ws = _ws(period=4, month=9)
    good = v2.talk_to_npc(ws, "Okhema", "Bartholos")
    check("Bartholos still speaks", good.get("ok") is True, str(good))
    check("Bartholos rest does not feast",
          "square is yours" not in (good.get("line") or "").lower())
    check("Bartholos rest notes rest or doorway or withdrawn or lamps",
          any(k in (good.get("line") or "").lower()
              for k in ("rest", "doorway", "lamp", "withdrawn", "hearth")),
          good.get("line"))
    bad = v2.talk_to_npc(ws, "Okhema", "Gorgo")
    check("Gorgo still rejected", bad.get("ok") is False)
    gen_one = next(n for n in rn.roster_in_city("Okhema") if n.get("source") == "stage2")
    spoken = v2.talk_to_npc(ws, "Okhema", gen_one["name"])
    check("generated resident speaks", spoken.get("ok") is True, str(spoken))

    ws = _ws(period=2, month=9)
    ws.black_tide_enabled = True
    ws.surge = {"active": True, "remaining": 1, "cities": ["Styxia"]}
    sty = v2.talk_to_npc(ws, "Styxia", "Theodosia")
    check("Theodosia under surge still lowers voice",
          sty.get("ok") is True and (
              "edge" in (sty.get("line") or "").lower()
              or "lower" in (sty.get("line") or "").lower()
              or "dark" in (sty.get("line") or "").lower()
              or "thinner" in (sty.get("line") or "").lower()),
          sty.get("line"))

    print("== Visit greet cap ==")
    ws = _ws(period=2, month=9)
    greet = rn.greet_here(ws, "Okhema", limit=4)
    check("greet_here is 1–4 people", 1 <= len(greet) <= 4, str(len(greet)))

    print("== Visitor on the road does not empty Okhema's square ==")
    ws = _ws(period=2, month=9)
    ws.visitor_travel = {"to": "Styxia", "from": "Okhema", "remaining": 1}
    flags = lm.derive(ws)["flags"]
    check("visitor-on-road has no square", flags.get("market_open") is False)
    vis = rn.visible_in_city(ws, "Okhema", flags={"resting": False})
    spots = {r.get("spot") for r in vis}
    check("Okhema merchants still at market while visitor walks",
          "market" in spots, str(spots))

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILED:", FAILED)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
