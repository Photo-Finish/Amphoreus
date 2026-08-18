# -*- coding: utf-8 -*-
"""Live experiments: sanctuary clock against a COPY of the running world.

Never writes world_runtime/world_state.json. Repeatable; isolate per round.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.sanctuary_clock import (
    GMT8,
    PERIODS_PER_DAY,
    UNC_ASTRORUM,
    UNC_SCARLET,
    WorldClock,
    is_light_leap,
)
from src.world.world_state import WorldState, guest_is_present
from src.world import lived_entities as le
from src.world import lived_mechanisms as lm
from src.world.ambient import AmbientDirector
from src.world.world_engine import WorldEngine

PASSED, FAILED = [], []
LIVE = ROOT / "world_runtime" / "world_state.json"


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def _copy_live(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if LIVE.is_file():
        shutil.copy2(LIVE, dest)
    return dest


def _sim_tuple(ws: WorldState):
    c = ws._sim_clock
    return (c.year, c.month, c.week, c.day, c.period, c.uncounted)


def exp_live_store_read_only():
    print("== A. Production store (read-only) ==")
    raw = json.loads(LIVE.read_text(encoding="utf-8"))
    clock = raw.get("clock") or {}
    check("live JSON is 4932", clock.get("year") == 4932, str(clock))
    check("live JSON is Strife (month 10)", clock.get("month") == 10, str(clock))
    scale = raw.get("time_scale", 1.0)
    check("live store is at 1x (overlay mode)",
          float(scale or 1.0) <= 1.0, str(scale))
    ws = WorldState(str(LIVE))
    check("1x overlay year is civil+2907",
          ws.clock.year == datetime.now(GMT8).year + 2907)
    check("1x overlay is not Strife-on-disk",
          not (ws.clock.year == 4932 and ws.clock.month == 10))
    check("sim clock still 4932 Strife under the overlay",
          ws._sim_clock.year == 4932 and ws._sim_clock.month == 10)
    before = json.dumps(raw["clock"], sort_keys=True)
    after = json.dumps(json.loads(LIVE.read_text(encoding="utf-8"))["clock"],
                       sort_keys=True)
    check("read-only load did not rewrite live clock", before == after)


def exp_scale_switch(path: Path, round_id: int):
    print(f"== B. Scale switch 1x↔2x–60x (round {round_id}) ==")
    ws = WorldState(str(path))
    origin = _sim_tuple(ws)
    check(f"r{round_id} copy starts at live sim 4932 Strife",
          origin[0] == 4932 and origin[1] == 10, str(origin))
    seen = []
    for scale in (1, 2, 5, 10, 30, 60, 1, 60, 1):
        ws.time_scale = float(scale)
        if scale <= 1:
            seen.append(("1x", ws.clock.year, ws.clock.month_name))
            check(f"r{round_id} 1x uses GMT+8 year",
                  ws.clock.year == datetime.now(GMT8).year + 2907)
        else:
            seen.append((f"{scale}x", ws.clock.year, ws.clock.month_name))
            check(f"r{round_id} {scale}x is sim 4932",
                  ws.clock.year == 4932 and ws.clock.month == origin[1])
        ws.save()
        check(f"r{round_id} save@{scale}x left sim tuple",
              _sim_tuple(ws) == origin, str(_sim_tuple(ws)))
    reloaded = WorldState(str(path))
    check(f"r{round_id} reload sim timestamp intact",
          _sim_tuple(reloaded) == origin)
    two = {s[0] for s in seen}
    check(f"r{round_id} both faces appeared", "1x" in two and "60x" in two)


def exp_engine_rest_ticks(path: Path, round_id: int, scale: float):
    print(f"== C. Engine ticks @ {scale:g}x (round {round_id}) ==")
    origin_ws = WorldState(str(path))
    origin = _sim_tuple(origin_ws)
    eng = WorldEngine(
        state_path=str(path),
        memory_root=str(path.parent / f"memory-{scale:g}"),
        chronicle_path=str(path.parent / f"chronicle-{scale:g}"),
    )
    eng.world.time_scale = float(scale)
    if scale > 1:
        # Curtain-Fall on the sim clock: run_day returns before Heir LLM calls.
        eng.world._sim_clock.period = 4
        eng.world.save()
    before = _sim_tuple(eng.world)
    overlay_rest = bool(eng.world.clock.is_rest_time())
    if scale <= 1 and not overlay_rest:
        # 1x follows GMT+8; do not enter the Heir-decision path in Parting/Action.
        from src.world import lived_mechanisms as _lm
        _lm.apply_tick(eng.world)
        eng.world.save()
        after = _sim_tuple(eng.world)
        check(f"r{round_id} 1x lived tick did not move sim clock",
              before == after, f"{before} -> {after}")
        check(f"r{round_id} 1x skipped Heir LLM (not rest on GMT+8)",
              not overlay_rest)
    else:
        lines = eng.run_day()
        after = _sim_tuple(eng.world)
        if scale <= 1:
            check(f"r{round_id} 1x engine did not move sim clock",
                  before == after, f"{before} -> {after}")
        else:
            check(f"r{round_id} {scale:g}x engine advanced sim clock",
                  after != before, f"{before} -> {after}")
            check(f"r{round_id} {scale:g}x still year 4932 after one rest tick",
                  after[0] == 4932)
        check(f"r{round_id} {scale:g}x run_day returned lines",
              isinstance(lines, list))
    snap = le.snapshot(eng.world, place="Okhema")
    faults = le.logic_faults(snap)
    check(f"r{round_id} {scale:g}x Okhema entities have no faults",
          faults == [], str(faults))
    return origin


def exp_year_lengths():
    print("== D. Counted+Uncounted length of common vs leap years ==")
    for year, expect in ((4933, 365), (4935, 366)):
        clk = WorldClock(year=year, month=1, week=1, day=1, period=0)
        days = 0
        scarlet = 0
        astrorum = 0
        membrance = 0
        while clk.year == year:
            if clk.uncounted == UNC_SCARLET:
                scarlet += 1
            elif clk.uncounted == UNC_ASTRORUM:
                astrorum += 1
            elif clk.month == 13:
                membrance += 1
            clk.advance(PERIODS_PER_DAY)
            days += 1
            if days > 400:
                break
        check(f"{year} has {expect} SI days", days == expect, str(days))
        check(f"{year} has one Dies Astrorum", astrorum == 1, str(astrorum))
        check(f"{year} Membrance 28 days", membrance == 28, str(membrance))
        want_scarlet = 1 if is_light_leap(year) else 0
        check(f"{year} Scarlet days={want_scarlet}",
              scarlet == want_scarlet, str(scarlet))
        check(f"{year} next year Gate",
              clk.year == year + 1 and clk.month == 1 and clk.week == 1
              and clk.day == 1 and clk.uncounted is None)


def exp_lived_and_ambient(path: Path):
    print("== E. Lived ticks + Keeper fallback on overlay and sim ==")
    ws = WorldState(str(path))
    ws.ambient = {
        "weather": {"Okhema": "clear and bright, the Dawn Device steady"},
        "news": "The Dawn Device holds.",
    }
    ws.visitor_location = "Okhema"
    for scale, label in ((1.0, "1x-overlay"), (60.0, "60x-sim")):
        ws.time_scale = scale
        tick = lm.apply_tick(ws)
        check(f"{label} mechanisms wrote flags",
              isinstance(tick.get("flags"), dict) and bool(tick.get("flags")))
        snap = le.snapshot(ws, place="Okhema")
        check(f"{label} no entity faults",
              le.logic_faults(snap) == [], str(le.logic_faults(snap)))
        check(f"{label} hours entity names a period",
              any("Hour" in r["status"] for r in snap["entities"]
                  if r["id"] == "hours"))
    for kind, clock in (
        ("membrance", WorldClock(year=4933, month=13, week=1, day=1, period=2)),
        ("scarlet", WorldClock(year=4935, month=12, week=4, day=7,
                               period=2, uncounted=UNC_SCARLET)),
        ("astrorum", WorldClock(year=4933, month=13, week=4, day=7,
                                period=2, uncounted=UNC_ASTRORUM)),
    ):
        amb = AmbientDirector(model="offline-fallback")._fallback(
            clock, {"phainon": {"name": "Phainon", "home": "Okhema"}})
        check(f"Keeper fallback {kind} has Okhema weather",
              "Okhema" in (amb.get("weather") or {}))
        check(f"Keeper fallback {kind} has news", bool(amb.get("news")))
    for cid in ("dan-heng-permansor-terrae", "evernight", "phainon"):
        guest_is_present(cid, ws.clock)
    check("guest_is_present survives overlay clock", True)


def exp_hour_grid():
    print("== F. Hour grid (repeated civil midnights and rims) ==")
    samples = [
        (datetime(2026, 8, 18, 0, 0, tzinfo=GMT8), 0, "Entry Hour"),
        (datetime(2026, 8, 18, 4, 47, tzinfo=GMT8), 0, "Entry Hour"),
        (datetime(2026, 8, 18, 4, 48, tzinfo=GMT8), 1, "Lucid Hour"),
        (datetime(2026, 8, 18, 9, 36, tzinfo=GMT8), 2, "Action Hour"),
        (datetime(2026, 8, 18, 14, 24, tzinfo=GMT8), 3, "Parting Hour"),
        (datetime(2026, 8, 18, 19, 12, tzinfo=GMT8), 4, "Curtain-Fall Hour"),
        (datetime(2026, 8, 18, 23, 59, tzinfo=GMT8), 4, "Curtain-Fall Hour"),
        (datetime(2028, 2, 29, 12, 0, tzinfo=GMT8), 2, "Action Hour"),
        (datetime(2028, 12, 2, 0, 0, tzinfo=GMT8), 0, "Entry Hour"),
    ]
    for dt, period, name in samples:
        clk = WorldClock.from_gmt8(dt)
        check(f"{dt.isoformat()} -> {name}",
              clk.period == period and clk.period_name == name,
              clk.format_short())
    leap_eve = WorldClock.from_gmt8(datetime(2028, 2, 29, 12, 0, tzinfo=GMT8))
    check("29 Feb 2028 is Evernight", leap_eve.month == 3 and not leap_eve.uncounted)
    scarlet = WorldClock.from_gmt8(datetime(2028, 12, 2, 8, 0, tzinfo=GMT8))
    check("2 Dec 2028 is Scarlet Day", scarlet.uncounted == UNC_SCARLET)


def one_round(round_id: int):
    tmp = Path(tempfile.mkdtemp(prefix=f"amp-live-{round_id}-"))
    copy = _copy_live(tmp / "world_state.json")
    exp_scale_switch(copy, round_id)
    for scale in (1.0, 2.0, 60.0):
        # fresh copy each scale so ticks do not stack
        p = tmp / f"eng-{scale:g}.json"
        _copy_live(p)
        exp_engine_rest_ticks(p, round_id, scale)
    exp_lived_and_ambient(copy)


def main() -> int:
    print("LIVE", LIVE, "exists" if LIVE.is_file() else "MISSING")
    exp_live_store_read_only()
    exp_hour_grid()
    exp_year_lengths()
    for n in (1, 2, 3):
        print(f"\n######## round {n} ########")
        one_round(n)
    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILED:", ", ".join(FAILED))
        return 1
    after = json.loads(LIVE.read_text(encoding="utf-8"))["clock"]
    print("production clock still", after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
