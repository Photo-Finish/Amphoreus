# -*- coding: utf-8 -*-
"""Sanctuary Light Calendar: overlay, Uncounted days, 1x GMT+8 vs sim clock."""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.sanctuary_clock import (
    GMT8,
    MONTHS,
    PERIODS_PER_DAY,
    UNC_ASTRORUM,
    UNC_SCARLET,
    WorldClock,
    is_light_leap,
    period_from_civil_hours,
)
from src.world.world_state import WorldState

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def main():
    print("== Kephale twelve + Membrance ==")
    check("13 months", len(MONTHS) == 13)
    check("month 9 still Weaving", MONTHS[8][0] == "Month of Weaving")
    check("month 12 still Fortune", MONTHS[11][0] == "Month of Fortune")
    check("month 13 Membrance", MONTHS[12][0] == "Month of Membrance")
    check("default sim is 4932 Weaving w1d1",
          WorldClock().year == 4932 and WorldClock().month == 9
          and WorldClock().week == 1 and WorldClock().day == 1)

    print("== Hours from midnight ==")
    check("00:00 Entry", period_from_civil_hours(0) == 0)
    check("04:48 Lucid", period_from_civil_hours(4.8) == 1)
    check("12:00 Action", period_from_civil_hours(12) == 2)
    check("19:12 Curtain-Fall", period_from_civil_hours(19.2) == 4)

    print("== Civil overlay (common 2026) ==")
    c = WorldClock.from_civil_date(date(2026, 8, 18))
    check("2026 = 4933", c.year == 4933)
    check("18 Aug is Weaving", c.month_name == "Month of Weaving")
    check("18 Aug is week 1 day 6", c.week == 1 and c.day == 6, f"w{c.week}d{c.day}")
    a = WorldClock.from_civil_date(date(2026, 12, 31))
    check("31 Dec Dies Astrorum", a.uncounted == UNC_ASTRORUM)
    m = WorldClock.from_civil_date(date(2026, 12, 30))
    check("30 Dec Membrance last day",
          m.month == 13 and m.week == 4 and m.day == 7 and not m.uncounted)

    print("== Leap overlay (2028) ==")
    check("4935 is leap", is_light_leap(4935))
    check("4933 is not leap", not is_light_leap(4933))
    e = WorldClock.from_civil_date(date(2028, 2, 29))
    check("29 Feb is Evernight, not Scarlet",
          e.month == 3 and e.uncounted is None, e.format_short())
    s = WorldClock.from_civil_date(date(2028, 12, 2))
    check("2 Dec 2028 is Scarlet Day", s.uncounted == UNC_SCARLET)
    mem = WorldClock.from_civil_date(date(2028, 12, 3))
    check("3 Dec 2028 is Membrance 1",
          mem.month == 13 and mem.week == 1 and mem.day == 1 and not mem.uncounted)

    noon = WorldClock.from_gmt8(datetime(2026, 8, 18, 12, 0, tzinfo=GMT8))
    check("GMT+8 noon is Action Hour", noon.period == 2, noon.format_short())

    print("== Advance: common Fortune → Membrance → Astrorum → Gate ==")
    clk = WorldClock(year=4933, month=12, week=4, day=7, period=4)
    clk.advance(1)
    check("common year: Fortune ends into Membrance",
          clk.month == 13 and clk.week == 1 and clk.day == 1 and clk.uncounted is None)
    clk = WorldClock(year=4933, month=13, week=4, day=7, period=4)
    clk.advance(1)
    check("Membrance ends into Dies Astrorum", clk.uncounted == UNC_ASTRORUM)
    clk.advance(PERIODS_PER_DAY)
    check("Dies Astrorum ends into next Gate",
          clk.year == 4934 and clk.month == 1 and clk.week == 1 and clk.day == 1
          and clk.uncounted is None, clk.format_short())

    print("== Advance: leap Fortune → Scarlet → Membrance ==")
    clk = WorldClock(year=4935, month=12, week=4, day=7, period=4)
    clk.advance(1)
    check("leap: Fortune ends into Scarlet Day", clk.uncounted == UNC_SCARLET)
    clk.advance(PERIODS_PER_DAY)
    check("Scarlet Day ends into Membrance",
          clk.uncounted is None and clk.month == 13 and clk.week == 1 and clk.day == 1)

    print("== 1x GMT+8 does not overwrite sim timestamp ==")
    tmp = Path(tempfile.mkdtemp(prefix="amp-cal-"))
    path = str(tmp / "world_state.json")
    ws = WorldState(path)
    check("fresh sim clock is 4932 Weaving",
          ws._sim_clock.year == 4932 and ws._sim_clock.month == 9)
    ws.time_scale = 1.0
    overlay = ws.clock
    check("1x clock is not the 4932 default year or is overlay object",
          overlay is not ws._sim_clock)
    check("1x year is civil+2907", overlay.year == datetime.now(GMT8).year + 2907)
    ws.save()
    ws2 = WorldState(path)
    check("reload keeps 4932 sim timestamp",
          ws2._sim_clock.year == 4932 and ws2._sim_clock.month == 9
          and ws2._sim_clock.week == 1 and ws2._sim_clock.day == 1)
    ws2.time_scale = 2.0
    check("2x still shows 4932 Weaving",
          ws2.clock.year == 4932 and ws2.clock.month_name == "Month of Weaving")

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILED:", ", ".join(FAILED))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
