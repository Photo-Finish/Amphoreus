# -*- coding: utf-8 -*-
"""Seasonal eco density + tide-edge land weather (official Light Calendar months)."""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.world.world_state import WorldState
from src.world.sanctuary_clock import MONTHS, WorldClock
from src.world import ecosystem as eco
from src.world import lived_mechanisms as lm

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def mk(period, place, *, month=9, day=3, year=4933):
    tmp = Path(tempfile.mkdtemp(prefix="amp-eco-s-"))
    ws = WorldState(str(tmp / "world_state.json"))
    ws._clock_override = WorldClock(year=year, month=month, day=day, period=period)
    ws.visitor_location = place
    # Park Heirs elsewhere so companion slots do not crowd seasonal texture.
    for cid in list(ws.agent_location.keys()):
        ws.set_location(cid, "Aidonia" if place != "Aidonia" else "Okhema")
    ws.vivid = dict(ws.vivid or {})
    ws.vivid["eco"] = {
        "beings": {}, "scene": [], "audit": [], "last_key": "", "gazette": [],
    }
    ws.vivid["lived"] = {
        "flags": {"market_open": True, "resting": False},
    }
    try:
        lm.apply_tick(ws)
    except Exception:
        pass
    # Re-assert outdoor day flags after lived tick.
    lived = dict(ws.vivid.get("lived") or {})
    f = dict(lived.get("flags") or {})
    f["market_open"] = True
    f["resting"] = False
    lived["flags"] = f
    ws.vivid["lived"] = lived
    return ws


def kinds_at(ws, place):
    return {b["kind"] for b in eco.derive_scene(ws, place=place)}


def count_kind(ws, place, kind):
    return sum(1 for b in eco.derive_scene(ws, place=place) if b.get("kind") == kind)


print("== Month of Cultivation (4): more dromases ==")
ws_cult = mk(2, "Okhema", month=4)
n_cult = count_kind(ws_cult, "Okhema", "dromas")
ws_base = mk(2, "Okhema", month=9)
n_base = count_kind(ws_base, "Okhema", "dromas")
check("Cultivation month has dromas", n_cult >= 1, str(n_cult))
check(
    "Cultivation denser than Weaving baseline",
    n_cult >= n_base,
    f"cult={n_cult} base={n_base}",
)
check(
    "Cultivation can spawn 2+ dromases (Action Hour)",
    n_cult >= 2,
    str(n_cult),
)
drom = next(b for b in eco.derive_scene(ws_cult, place="Okhema") if b["kind"] == "dromas")
check(
    "Cultivation dromas doing uses official month name",
    "Month of Cultivation" in (drom.get("doing") or ""),
    drom.get("doing"),
)

print("== Month of Reaping (8): wheat gold ==")
ws_reap = mk(1, "Aedes Elysiae", month=8)
wheat = next(
    (b for b in eco.derive_scene(ws_reap, place="Aedes Elysiae") if b["kind"] == "wheat"),
    None,
)
check("Reaping wheat present", wheat is not None)
check("Reaping wheat status gold", wheat is not None and wheat.get("status") == "gold")
check(
    "Reaping wheat doing fuller / Month of Reaping",
    wheat is not None
    and "Month of Reaping" in (wheat.get("doing") or "")
    and "fuller" in (wheat.get("doing") or "").lower(),
    (wheat or {}).get("doing"),
)

print("== Month of Joy (5): fuller shore/nets ==")
ws_joy = mk(2, "Styxia", month=5)
ws_joy_off = mk(2, "Styxia", month=9)
nets_joy = count_kind(ws_joy, "Styxia", "net")
nets_off = count_kind(ws_joy_off, "Styxia", "net")
check("Joy month has nets", nets_joy >= 1)
check("Joy nets denser than Weaving", nets_joy >= nets_off, f"{nets_joy} vs {nets_off}")
siren = next(
    (b for b in eco.derive_scene(ws_joy, place="Styxia") if b["kind"] == "siren"),
    None,
)
check(
    "Joy siren status full / Month of Joy",
    siren is not None
    and siren.get("status") == "full"
    and "Month of Joy" in (siren.get("doing") or ""),
    (siren or {}).get("doing"),
)

print("== Month of Weaving (9): cloth/loom in Okhema ==")
ws_weav = mk(2, "Okhema", month=9)
k_weav = kinds_at(ws_weav, "Okhema")
check("Weaving Okhema has laundry", "laundry" in k_weav, str(k_weav))
check("Weaving Okhema has loom or ribbon", "loom" in k_weav or "ribbon" in k_weav, str(k_weav))
laundry = next(
    (b for b in eco.derive_scene(ws_weav, place="Okhema") if b["kind"] == "laundry"),
    None,
)
check(
    "Weaving laundry doing mentions Month of Weaving",
    laundry is not None and "Month of Weaving" in (laundry.get("doing") or ""),
    (laundry or {}).get("doing"),
)
if "loom" in k_weav:
    loom = next(b for b in eco.derive_scene(ws_weav, place="Okhema") if b["kind"] == "loom")
    check(
        "Weaving loom status weaving",
        loom.get("status") == "weaving",
        str(loom.get("status")),
    )
else:
    check("Weaving loom status weaving", False, "loom missing")

print("== Month of Membrance (13): maze fairy kept ==")
ws_mem = mk(1, "Aedes Elysiae", month=13)
check(
    "Membrance maze fairy at Aedes",
    "maze_fairy" in kinds_at(ws_mem, "Aedes Elysiae"),
)

print("== Month of Strife (10): forge/banner denser at Kremnos ==")
ws_strife = mk(2, "Castrum Kremnos", month=10)
ws_strife_off = mk(2, "Castrum Kremnos", month=9)
banners_s = count_kind(ws_strife, "Castrum Kremnos", "banner")
banners_o = count_kind(ws_strife_off, "Castrum Kremnos", "banner")
check("Strife Kremnos has banners", banners_s >= 1)
check(
    "Strife banners denser than Weaving",
    banners_s >= banners_o,
    f"{banners_s} vs {banners_o}",
)
forge = next(
    (b for b in eco.derive_scene(ws_strife, place="Castrum Kremnos") if b["kind"] == "forge"),
    None,
)
check(
    "Strife forge ringing + Month of Strife",
    forge is not None
    and forge.get("status") == "ringing"
    and "Month of Strife" in (forge.get("doing") or ""),
    (forge or {}).get("doing"),
)

print("== Tide edge thins density + weather flag ==")
ws_tide = mk(2, "Styxia", month=9)
ws_tide.surge = {"active": True, "remaining": 2, "cities": ["Styxia"]}
check("tide_edge_active at surged Styxia", eco.tide_edge_active(ws_tide, "Styxia"))
ws_quiet = mk(2, "Styxia", month=9)
ws_quiet.surge = {"active": False, "remaining": 0, "cities": []}
check(
    "tide_edge inactive when surge off",
    not eco.tide_edge_active(ws_quiet, "Styxia"),
)
ws_ok_surge = mk(2, "Okhema", month=9)
ws_ok_surge.surge = {"active": True, "remaining": 2, "cities": ["Styxia"]}
check(
    "tide_edge false for Okhema when only Styxia surged",
    not eco.tide_edge_active(ws_ok_surge, "Okhema"),
)

# Market thin: Styxia market stalls under tide vs calm
ws_mkt_tide = mk(2, "Styxia", month=9)
ws_mkt_tide.surge = {"active": True, "remaining": 2, "cities": ["Styxia"]}
# Ensure market_open via lived flags if apply_tick set them
flags = (ws_mkt_tide.vivid.get("lived") or {}).get("flags") or {}
if not flags.get("market_open"):
    lived = dict(ws_mkt_tide.vivid.get("lived") or {})
    f = dict(lived.get("flags") or {})
    f["market_open"] = True
    lived["flags"] = f
    ws_mkt_tide.vivid["lived"] = lived
ws_mkt_calm = mk(2, "Styxia", month=9)
flags_c = (ws_mkt_calm.vivid.get("lived") or {}).get("flags") or {}
if not flags_c.get("market_open"):
    lived = dict(ws_mkt_calm.vivid.get("lived") or {})
    f = dict(lived.get("flags") or {})
    f["market_open"] = True
    lived["flags"] = f
    ws_mkt_calm.vivid["lived"] = lived
stalls_tide = count_kind(ws_mkt_tide, "Styxia", "market_stall")
stalls_calm = count_kind(ws_mkt_calm, "Styxia", "market_stall")
check(
    "tide edge thins market stalls at Styxia",
    stalls_tide <= stalls_calm,
    f"tide={stalls_tide} calm={stalls_calm}",
)

tick = eco.apply_tick(ws_tide)
check("apply_tick sets tide_edge true", tick.get("tide_edge") is True)
check(
    "eco bucket / vivid flag tide_edge",
    bool(eco.eco_bucket(ws_tide).get("tide_edge"))
    or bool((ws_tide.vivid or {}).get("tide_edge")),
)

# Walk/Visit land weather contract: tide_edge → blacktide effect key
wx_src = (ROOT / "src" / "ui_weather.py").read_text(encoding="utf-8")
walk_src = (ROOT / "src" / "ui_walk_land.py").read_text(encoding="utf-8")
check('ui_weather defines "blacktide" effect', '"blacktide"' in wx_src)
check(
    "ui_weather effect_for accepts world / tide_edge",
    "tide_edge_active" in wx_src and "world" in wx_src,
)
check(
    "ui_walk_land forces blacktide on tide_edge",
    "tide_edge_active" in walk_src and "blacktide" in walk_src,
)
from src.world import world_events as wev
check("Styxia is an EDGE_CITY", "Styxia" in wev.EDGE_CITIES)

# No invented festival titles — official Light Calendar months only (MONTHS).
official_months = {m[0] for m in MONTHS}
banned_fragments = (
    "Harvest Festival",
    "Strife Festival",
    "Joy Festival",
    "Weaving Fair",
    "Festival of",
    "festival of",
    "Weaving Festival",
    "Reaping Festival",
    "Cultivation Festival",
    "Membrance Festival",
    "Phagousa Festival",
    "Festival of Phagousa",
)
seasonal_doings = []
for ws, place in (
    (ws_cult, "Okhema"),
    (ws_reap, "Aedes Elysiae"),
    (ws_joy, "Styxia"),
    (ws_weav, "Okhema"),
    (ws_strife, "Castrum Kremnos"),
    (ws_mem, "Aedes Elysiae"),
):
    for b in eco.derive_scene(ws, place=place):
        seasonal_doings.append(b.get("doing") or "")

hit_banned = [
    d for d in seasonal_doings
    if any(bad in d for bad in banned_fragments) or ("Festival" in d) or ("festival" in d)
]
check(
    "no unofficial festival titles in seasonal doing",
    not hit_banned,
    "; ".join(hit_banned[:3]),
)

# Any "Month of …" phrase in seasonal doing must be an official calendar month.
month_mentions = []
for d in seasonal_doings:
    month_mentions.extend(re.findall(r"Month of [A-Za-z]+", d))
unofficial = sorted({m for m in month_mentions if m not in official_months})
check(
    "seasonal Month-of phrases are official only",
    not unofficial,
    str(unofficial),
)

# Static source guard: ecosystem.py must not invent Festival titles.
eco_src = (ROOT / "src" / "world" / "ecosystem.py").read_text(encoding="utf-8")
check(
    "ecosystem.py source has no Festival titles",
    "Festival" not in eco_src and "festival" not in eco_src,
)

print()
print(f"{len(PASSED)} passed, {len(FAILED)} failed")
if FAILED:
    sys.exit(1)
if len(PASSED) < 15:
    print(f"NEED ≥15 checks, got {len(PASSED)}")
    sys.exit(1)
