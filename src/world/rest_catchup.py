"""1x rest catch-up — sync the Light Calendar and offer missed days.

When Amphoreus starts operating at 1x after a rest, the overlay already
follows GMT+8, but the engine wrote no chronicle for the days that passed.
This module:

1. Copies the GMT+8 overlay onto the persisted sim clock (so 2x later does
   not jump back to a frozen 4932 stamp).
2. Counts complete civil days between rest and now.
3. Generates those days through the world engine if the operator says yes.

Never infers missed days from the frozen sim stamp — that would try to
replay months. Rest is marked when the engine is asked to stop.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, List, Optional

from .sanctuary_clock import GMT8, WorldClock

BUCKET = "rest_catchup"
MAX_CATCHUP_DAYS = 7
# A lived day in catch-up, not the sleep tick (Curtain-Fall / Entry).
CATCHUP_PERIOD = 2  # Action Hour


def _bucket(world) -> dict:
    vivid = world.vivid if isinstance(getattr(world, "vivid", None), dict) else {}
    world.vivid = vivid
    b = vivid.get(BUCKET)
    if not isinstance(b, dict):
        b = {}
        vivid[BUCKET] = b
    return b


def _parse_iso(text: str) -> Optional[datetime]:
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=GMT8)
    else:
        dt = dt.astimezone(GMT8)
    return dt


def record_rest(world, when: Optional[datetime] = None) -> bool:
    """Stamp the moment the world went to rest. Idempotent while still resting."""
    b = _bucket(world)
    if b.get("rest_since"):
        return False
    dt = when if when is not None else datetime.now(GMT8)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=GMT8)
    else:
        dt = dt.astimezone(GMT8)
    b["rest_since"] = dt.isoformat(timespec="seconds")
    world.save()
    return True


def clear_rest(world) -> None:
    """The rest has been accounted for (lived, skipped, or nothing missed)."""
    b = _bucket(world)
    b.pop("rest_since", None)
    b.pop("offer", None)
    world.save()


def mark_lived(world, clock: Optional[WorldClock] = None) -> None:
    """Remember the last Light-Calendar day the engine actually wrote."""
    c = clock if clock is not None else world.clock
    b = _bucket(world)
    b["last_lived"] = c.to_dict() if hasattr(c, "to_dict") else {}
    world.save()


def sync_calendar_to_gmt8(world, when: Optional[datetime] = None) -> WorldClock:
    """Align the persisted sim clock with the 1x GMT+8 overlay."""
    now = WorldClock.from_gmt8(when)
    world._sim_clock = WorldClock.from_dict(now.to_dict())
    world.save()
    return now


def missed_civil_dates(world, now: Optional[datetime] = None) -> List:
    """Complete civil dates after rest_since and before today (GMT+8)."""
    b = _bucket(world)
    rest = _parse_iso(b.get("rest_since") or "")
    if rest is None:
        return []
    end = now if now is not None else datetime.now(GMT8)
    if end.tzinfo is None:
        end = end.replace(tzinfo=GMT8)
    else:
        end = end.astimezone(GMT8)
    start = rest.date() + timedelta(days=1)
    last = end.date()  # exclusive — today will be lived by the running engine
    out = []
    d = start
    while d < last:
        out.append(d)
        d += timedelta(days=1)
    return out


def clocks_for_dates(dates) -> List[WorldClock]:
    clocks = []
    for d in dates:
        c = WorldClock.from_civil_date(d)
        c.period = CATCHUP_PERIOD
        clocks.append(c)
    return clocks


def make_offer(world, now: Optional[datetime] = None) -> dict:
    """What the operator is asked when 1x operation begins after a rest."""
    dates = missed_civil_dates(world, now=now)
    total = len(dates)
    skipped = 0
    if total > MAX_CATCHUP_DAYS:
        skipped = total - MAX_CATCHUP_DAYS
        dates = dates[-MAX_CATCHUP_DAYS:]
    clocks = clocks_for_dates(dates)
    labels = [c.format_short() for c in clocks]
    return {
        "days": total,
        "generate": len(clocks),
        "skipped": skipped,
        "from_label": labels[0] if labels else "",
        "to_label": labels[-1] if labels else "",
        "clocks": clocks,
    }


def decline_missed(world) -> None:
    """Operator chose not to generate the rest days. Calendar stays synced."""
    clear_rest(world)


def note_skipped_rest(engine, skipped: int, clock: WorldClock) -> None:
    """A brief chronicle line for days beyond the catch-up cap."""
    if skipped <= 0:
        return
    text = (
        f"{clock.format_short()} — While the world rested, {skipped} quieter "
        "day(s) passed before this record picks up."
    )
    engine.chronicle.append({
        "time": clock.format_short(),
        "text": text,
        "kind": "rest",
    })
    engine.world.add_event(text)


def generate_missed_days(engine, clocks: List[WorldClock],
                         on_day: Optional[Callable] = None,
                         skipped: int = 0) -> dict:
    """Play each missed day through the engine (stories, ambient, encounters)."""
    world = engine.world
    engine._catchup = True
    written = []
    ok = False
    try:
        if skipped and clocks:
            note_skipped_rest(engine, skipped, clocks[0])
        for i, clock in enumerate(clocks):
            if on_day:
                on_day(i + 1, len(clocks), clock)
            world._clock_override = clock
            lines = engine.run_day()
            mark_lived(world, clock)
            written.append({
                "time": clock.format_short(),
                "lines": len(lines or []),
            })
        ok = True
    finally:
        world._clock_override = None
        engine._catchup = False
        if ok:
            clear_rest(world)
        else:
            world.save()
    return {"days": len(written), "written": written}
