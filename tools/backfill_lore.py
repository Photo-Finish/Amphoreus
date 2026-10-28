# -*- coding: utf-8 -*-
"""Write the lore for days the world spent at rest, beyond the 7-day catch-up.

    python tools/backfill_lore.py --dry-run
    python tools/backfill_lore.py --from 2026-09-17 --to 2026-10-21

`rest_catchup` caps a catch-up at seven days so a restart cannot replay months.
The world was designed to run unattended, so an operator may decide that the
earlier weeks should exist after all — this writes them, a day at a time, with the
engine that generates every other day.

Stop the running engine first: two writers share one chronicle and one clock.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default="")
    ap.add_argument("--to", dest="end", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model", default="qwen2.5:14b-instruct")
    args = ap.parse_args()

    from src.world import rest_catchup as rc
    from src.world.sanctuary_clock import GMT8
    from src.world.world_state import WorldState
    from src.world.world_engine import WorldEngine

    world = WorldState()
    missed = rc.missed_civil_dates(world)
    if not missed:
        print("no missed days recorded — the rest marker is current")
        # Fall back to an explicit range so a decision to backfill history is
        # still possible after a catch-up has already moved the marker.
        if not (args.start and args.end):
            return 0
    start = (datetime.fromisoformat(args.start).date() if args.start
             else (missed[0] if missed else None))
    end = (datetime.fromisoformat(args.end).date() if args.end
           else (missed[-1] if missed else None))
    if not start or not end:
        print("nothing to do")
        return 0

    dates = []
    d = start
    while d <= end:
        dates.append(d)
        d += timedelta(days=1)
    # the days already written (7-day catch-up) must not be written twice
    last_lived = ((world.vivid.get("rest_catchup") or {}).get("last_lived") or {})
    already = set()
    if last_lived:
        try:
            already.add(rc.WorldClock.from_dict(last_lived).civil_date())
        except Exception:
            pass
    todo = [x for x in dates if x not in already]

    print(f"range {start} -> {end}: {len(dates)} day(s), {len(todo)} to write")
    for x in todo[:5]:
        print("  ", x)
    if len(todo) > 5:
        print(f"   ... and {len(todo) - 5} more")
    if args.dry_run:
        return 0

    engine = WorldEngine(llm_model=args.model)
    clocks = rc.clocks_for_dates(todo)
    started = datetime.now(GMT8)
    print(f"writing {len(clocks)} day(s) with {args.model}; start {started:%H:%M:%S}", flush=True)
    rc.generate_missed_days(engine, clocks, skipped=0)
    print(f"done at {datetime.now(GMT8):%H:%M:%S}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
