# -*- coding: utf-8 -*-
"""Canon companions in the ecosystem — Pollux, Maze fairies, Mountain Dwellers.

Grounded in databank/world/fauna.md, major-locations.md, sanctuary-calendar.md.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.world.world_state import WorldState
from src.world.sanctuary_clock import WorldClock
from src.world import ecosystem as eco

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def mk(period, place, *, month=9, day=3, year=4933):
    tmp = Path(tempfile.mkdtemp(prefix="amp-eco-c-"))
    ws = WorldState(str(tmp / "world_state.json"))
    # 1x scale returns GMT+8; override so month/period tests stick (like test_ecosystem).
    ws._clock_override = WorldClock(year=year, month=month, day=day, period=period)
    ws.visitor_location = place
    for cid in list(ws.agent_location.keys()):
        ws.set_location(cid, "Okhema")
    return ws

def kinds_at(ws, place):
    return {b["kind"] for b in eco.derive_scene(ws, place=place)}


print("== Pollux (Castorice's dragon companion) ==")
ws = mk(2, "Aidonia")
ws.set_location("castorice", "Aidonia")
k_aid = kinds_at(ws, "Aidonia")
check("Pollux with Castorice at Aidonia", "pollux" in k_aid, str(k_aid))
pollux = next(
    (b for b in eco.derive_scene(ws, place="Aidonia") if b["kind"] == "pollux"),
    None,
)
check("Pollux named Pollux", pollux is not None and pollux.get("name") == "Pollux")
check(
    "Pollux not dead/starving",
    pollux is not None and pollux.get("status") not in {"dead", "starving", "plague"},
    str(pollux.get("status") if pollux else None),
)
doing = (pollux or {}).get("doing") or ""
check(
    "Pollux framed as dragon companion (not dragonling)",
    "dragon" in doing.lower() and "dragonling" not in doing.lower(),
    doing,
)
inter = eco.interact(ws, pollux["id"], place="Aidonia") if pollux else {}
check("Pollux interact ok", inter.get("ok") is True, str(inter))
line = inter.get("line") or ""
check(
    "Pollux interact distinguishes Workshop dromas",
    "Workshop" in line or "dromas" in line.lower(),
    line,
)

ws_g = mk(2, "Grove of Epiphany")
ws_g.set_location("castorice", "Aidonia")
k_grove = kinds_at(ws_g, "Grove of Epiphany")
check("No Pollux in Grove without Castorice", "pollux" not in k_grove, str(k_grove))

ws_ok = mk(2, "Okhema")
ws_ok.set_location("castorice", "Aidonia")
k_ok = kinds_at(ws_ok, "Okhema")
check("No Pollux in Okhema when Castorice is elsewhere", "pollux" not in k_ok, str(k_ok))

ws_ok2 = mk(2, "Okhema")
ws_ok2.set_location("castorice", "Okhema")
k_ok2 = kinds_at(ws_ok2, "Okhema")
check("Pollux follows Castorice to Okhema", "pollux" in k_ok2, str(k_ok2))

print("== Membrance Maze fairy at Aedes ==")
ws_m = mk(1, "Aedes Elysiae", month=13, day=2)
k_mem = kinds_at(ws_m, "Aedes Elysiae")
check("Maze fairy in Membrance month at Aedes", "maze_fairy" in k_mem, str(k_mem))
check("No invented 'membrance_shade' kind", "membrance_shade" not in k_mem, str(k_mem))

ws_old = mk(1, "Aedes Elysiae, of old", month=13, day=2)
k_old = kinds_at(ws_old, "Aedes Elysiae, of old")
check("Maze fairy at Aedes of old", "maze_fairy" in k_old, str(k_old))

ws_strife = mk(1, "Aedes Elysiae", month=9, day=2)  # Month of Strife-ish
k_strife = kinds_at(ws_strife, "Aedes Elysiae")
check("No Maze fairy in Strife month", "maze_fairy" not in k_strife, str(k_strife))

fairy = next(
    (b for b in eco.derive_scene(ws_m, place="Aedes Elysiae") if b["kind"] == "maze_fairy"),
    None,
)
check(
    "Maze fairy alive and named as fairy",
    fairy is not None
    and fairy.get("status") in {"alive", "quiet", "open", "well", "present"}
    and "fairy" in (fairy.get("name") or "").lower(),
    str(fairy),
)

print("== Mountain Dwellers (Okhema home; not Aidonia) ==")
check(
    "Okhema is mountain-dweller place",
    "Okhema" in eco.MOUNTAIN_DWELLER_PLACES,
)
check(
    "Eternal Holy City is mountain-dweller place",
    "Eternal Holy City" in eco.MOUNTAIN_DWELLER_PLACES,
)
check(
    "Castrum Kremnos is mountain-dweller place (historical forge echo)",
    "Castrum Kremnos" in eco.MOUNTAIN_DWELLER_PLACES,
)
check(
    "Aidonia is NOT mountain-dweller place",
    "Aidonia" not in eco.MOUNTAIN_DWELLER_PLACES,
)
check(
    "Grove is NOT mountain-dweller place",
    "Grove of Epiphany" not in eco.MOUNTAIN_DWELLER_PLACES,
)

found_md = False
md = None
ws_md = None
for day in range(1, 29):
    ws_md = mk(1, "Okhema", month=9, day=day)  # Lucid Hour
    if "mountain_dweller" in kinds_at(ws_md, "Okhema"):
        md = next(
            (
                b for b in eco.derive_scene(ws_md, place="Okhema")
                if b["kind"] == "mountain_dweller"
            ),
            None,
        )
        found_md = md is not None
        if found_md:
            inter_md = eco.interact(ws_md, md["id"], place="Okhema")
            check("Mountain Dweller interact ok", inter_md.get("ok") is True)
            md_line = inter_md.get("line") or ""
            check(
                "Mountain Dweller smith/mason flavor (not grave-work)",
                ("smith" in md_line.lower() or "mason" in md_line.lower()
                 or "Georios" in md_line)
                and "grave" not in md_line.lower(),
                md_line,
            )
            break
check("Mountain Dweller can appear at Okhema Lucid (thin presence)", found_md)

# Aidonia must never grow Mountain Dwellers across day seeds.
aidonia_md = False
for day in range(1, 29):
    ws_a = mk(1, "Aidonia", month=9, day=day)
    if "mountain_dweller" in kinds_at(ws_a, "Aidonia"):
        aidonia_md = True
        break
check("No Mountain Dweller at Aidonia across day seeds", not aidonia_md)

grove_md = False
for day in range(1, 15):
    ws_g2 = mk(1, "Grove of Epiphany", month=9, day=day)
    if "mountain_dweller" in kinds_at(ws_g2, "Grove of Epiphany"):
        grove_md = True
        break
check("No mountain dweller in Grove across day seeds", not grove_md)

ws_rest = mk(4, "Okhema", month=9, day=3)  # Curtain-Fall
k_rest = kinds_at(ws_rest, "Okhema")
check("No mountain dweller at rest hour", "mountain_dweller" not in k_rest, str(k_rest))

# logic_faults: MD at Aidonia is illegal
fake_md = [{"kind": "mountain_dweller", "status": "alive", "id": "x"}]
faults = eco.logic_faults(fake_md, "Aidonia")
check(
    "logic_faults rejects Mountain Dweller at Aidonia",
    any("Aidonia" in f or "Okhema" in f for f in faults),
    str(faults),
)

print("== Little Ica (Hyacine's winged pony companion) ==")
ws_ica = mk(2, "Okhema")
ws_ica.set_location("hyacine", "Okhema")
k_ica = kinds_at(ws_ica, "Okhema")
check("Little Ica with Hyacine at Okhema", "little_ica" in k_ica, str(k_ica))
ica = next(
    (b for b in eco.derive_scene(ws_ica, place="Okhema") if b["kind"] == "little_ica"),
    None,
)
check("Little Ica named Little Ica", ica is not None and ica.get("name") == "Little Ica")
check(
    "Little Ica not dead/starving",
    ica is not None and ica.get("status") not in {"dead", "starving", "plague"},
    str(ica.get("status") if ica else None),
)
ica_doing = (ica or {}).get("doing") or ""
check(
    "Little Ica framed as winged pony (not dragonling)",
    ("pony" in ica_doing.lower() or "winged" in ica_doing.lower())
    and "dragonling" not in ica_doing.lower(),
    ica_doing,
)
inter_ica = eco.interact(ws_ica, ica["id"], place="Okhema") if ica else {}
check("Little Ica interact ok", inter_ica.get("ok") is True, str(inter_ica))
ica_line = inter_ica.get("line") or ""
check(
    "Little Ica interact soft presence / not dragonling",
    ("pony" in ica_line.lower() or "Hyacine" in ica_line)
    and "dragonling" not in ica_line.lower().replace("not a dragonling", ""),
    ica_line,
)
check(
    "Little Ica pet allowed",
    "little_ica" in eco.VISITOR_ACT["pet"]["kinds"],
)

ws_ica_away = mk(2, "Okhema")
ws_ica_away.set_location("hyacine", "Aidonia")
k_away = kinds_at(ws_ica_away, "Okhema")
check(
    "No Little Ica in Okhema when Hyacine is elsewhere",
    "little_ica" not in k_away,
    str(k_away),
)

ws_ica_grove = mk(2, "Grove of Epiphany")
ws_ica_grove.set_location("hyacine", "Okhema")
k_grove_ica = kinds_at(ws_ica_grove, "Grove of Epiphany")
check(
    "No Little Ica in Grove without Hyacine",
    "little_ica" not in k_grove_ica,
    str(k_grove_ica),
)

ws_ica_grove2 = mk(2, "Grove of Epiphany")
ws_ica_grove2.set_location("hyacine", "Grove of Epiphany")
k_grove_hy = kinds_at(ws_ica_grove2, "Grove of Epiphany")
check(
    "Little Ica follows Hyacine into Grove",
    "little_ica" in k_grove_hy,
    str(k_grove_hy),
)

fake_ica = [{"kind": "little_ica", "status": "present", "id": "ica-x"}]
faults_ica = eco.logic_faults(fake_ica, "Okhema", world=ws_ica_away)
check(
    "logic_faults rejects Little Ica without Hyacine",
    any("Little Ica" in f or "Hyacine" in f for f in faults_ica),
    str(faults_ica),
)
faults_grove = eco.logic_faults(fake_ica, "Grove of Epiphany", world=ws_ica_grove)
check(
    "logic_faults rejects Little Ica in Grove without Hyacine",
    any("Grove" in f or "Hyacine" in f for f in faults_grove),
    str(faults_grove),
)

print()
print(f"{len(PASSED)} passed, {len(FAILED)} failed")
if FAILED:
    sys.exit(1)
