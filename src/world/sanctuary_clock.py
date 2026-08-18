"""
Sanctuary Light Calendar clock.

Kephale's twelve Titan-months stay as in `databank/world/calendar.md`.
The sanctuary reform (Membrance, Uncounted, Earth overlay) is
`databank/world/sanctuary-calendar.md`.

Default sim timestamp remains Year 4932, Month of Weaving, week 1, day 1.
"""
from __future__ import annotations

import calendar
from datetime import datetime, timedelta, timezone
from typing import Optional

# Civil year G ↔ Light year A = G + 2907 (2026 = 4933).
LIGHT_YEAR_OFFSET = 2907
GMT8 = timezone(timedelta(hours=8))

UNC_SCARLET = "scarlet"
UNC_ASTRORUM = "astrorum"

# First twelve tuples are Kephale's Titan-months (unchanged).
MONTHS = [
    ("Month of Gate", "Fate", "Janus"),
    ("Month of Balance", "Fate", "Talanton"),
    ("Month of Evernight", "Fate", "Oronyx"),
    ("Month of Cultivation", "Pillar", "Georios"),
    ("Month of Joy", "Pillar", "Phagousa"),
    ("Month of Everday", "Pillar", "Aquila"),
    ("Month of Freedom", "Creation", "Kephale"),
    ("Month of Reaping", "Creation", "Cerces"),
    ("Month of Weaving", "Creation", "Mnestia"),
    ("Month of Strife", "Calamity", "Nikador"),
    ("Month of Mourning", "Calamity", "Thanatos"),
    ("Month of Fortune", "Calamity", "Zagreus"),
    ("Month of Membrance", "outside the four seasons", "Cyrene"),
]

PERIODS = [
    "Entry Hour",
    "Lucid Hour",
    "Action Hour",
    "Parting Hour",
    "Curtain-Fall Hour",
]

WEEKS_PER_MONTH = 4
DAYS_PER_WEEK = 7
PERIODS_PER_DAY = len(PERIODS)
MONTHS_PER_YEAR = len(MONTHS)  # 13


def is_light_leap(year: int) -> bool:
    """Leap Light years are those whose paired Gregorian year is a leap year."""
    return calendar.isleap(int(year) - LIGHT_YEAR_OFFSET)


def period_from_civil_hours(h: float) -> int:
    """Linear Hours: p = (5/24) h, Entry at midnight. h in [0, 24)."""
    if h < 0:
        h = 0.0
    p = (5.0 / 24.0) * float(h)
    idx = int(p)
    if idx >= PERIODS_PER_DAY:
        return PERIODS_PER_DAY - 1
    return max(0, idx)


def _day_index(clock) -> int:
    """Days since Year 4932, Gate week 1 day 1, counting Uncounted dates."""
    year = int(getattr(clock, "year", 4932) or 4932)
    days = 0
    for y in range(4932, year):
        days += 366 if is_light_leap(y) else 365
    return days + _ordinal_in_year(clock)


def _ordinal_in_year(clock) -> int:
    """0-based day within the Light year (Uncounted included)."""
    year = int(getattr(clock, "year", 4932) or 4932)
    leap = is_light_leap(year)
    u = getattr(clock, "uncounted", None) or None
    if u == UNC_SCARLET:
        return 12 * 28
    if u == UNC_ASTRORUM:
        return 13 * 28 + (1 if leap else 0)
    month = max(1, int(getattr(clock, "month", 1) or 1))
    week = max(1, int(getattr(clock, "week", 1) or 1))
    day = max(1, int(getattr(clock, "day", 1) or 1))
    base = (month - 1) * 28 + (week - 1) * 7 + (day - 1)
    if leap and month >= 13:
        base += 1
    return base


class WorldClock:
    """The Light Calendar clock of Amphoreus (sanctuary reform)."""

    def __init__(
        self,
        year: int = 4932,
        month: int = 9,
        week: int = 1,
        day: int = 1,
        period: int = 0,
        uncounted: Optional[str] = None,
    ):
        self.year = year
        self.month = month  # 1..13 when counted
        self.week = week  # 1..4
        self.day = day  # 1..7
        self.period = period  # 0..4
        self.uncounted = uncounted if uncounted in (UNC_SCARLET, UNC_ASTRORUM) else None

    def advance(self, periods: int = 1):
        """Advance the clock by a number of daily periods."""
        for _ in range(max(0, int(periods))):
            self.period += 1
            if self.period >= PERIODS_PER_DAY:
                self.period = 0
                self._next_civil_day()

    def _next_civil_day(self) -> None:
        if self.uncounted == UNC_SCARLET:
            self.uncounted = None
            self.month, self.week, self.day = 13, 1, 1
            return
        if self.uncounted == UNC_ASTRORUM:
            self.uncounted = None
            self.year += 1
            self.month, self.week, self.day = 1, 1, 1
            return
        self.day += 1
        if self.day <= DAYS_PER_WEEK:
            return
        self.day = 1
        self.week += 1
        if self.week <= WEEKS_PER_MONTH:
            return
        self.week = 1
        if self.month == 12 and is_light_leap(self.year):
            self.uncounted = UNC_SCARLET
            return
        if self.month == 13:
            self.uncounted = UNC_ASTRORUM
            return
        if self.month >= 13:
            self.month = 1
            self.year += 1
            return
        self.month += 1

    @property
    def month_name(self) -> str:
        if self.uncounted == UNC_SCARLET:
            return "Scarlet Day"
        if self.uncounted == UNC_ASTRORUM:
            return "Dies Astrorum"
        idx = int(self.month) - 1
        if 0 <= idx < len(MONTHS):
            return MONTHS[idx][0]
        return MONTHS[8][0]

    @property
    def season(self) -> str:
        if self.uncounted == UNC_SCARLET:
            return "Calamity"
        if self.uncounted == UNC_ASTRORUM:
            return "Uncounted"
        idx = int(self.month) - 1
        if 0 <= idx < len(MONTHS):
            return MONTHS[idx][1]
        return MONTHS[8][1]

    @property
    def patron_titan(self) -> str:
        if self.uncounted == UNC_SCARLET:
            return "Zagreus"
        if self.uncounted == UNC_ASTRORUM:
            return "the Astral Express"
        idx = int(self.month) - 1
        if 0 <= idx < len(MONTHS):
            return MONTHS[idx][2]
        return MONTHS[8][2]

    @property
    def period_name(self) -> str:
        p = int(self.period)
        if 0 <= p < len(PERIODS):
            return PERIODS[p]
        return PERIODS[0]

    def is_rest_time(self) -> bool:
        """Whether most would be asleep (Curtain-Fall Hour or Entry Hour)."""
        return self.period == 4 or self.period == 0

    def format(self) -> str:
        if self.uncounted == UNC_SCARLET:
            return (
                f"Year {self.year}, Scarlet Day (Uncounted, patron Zagreus) — "
                f"{self.period_name}"
            )
        if self.uncounted == UNC_ASTRORUM:
            return (
                f"Year {self.year}, Dies Astrorum (Uncounted) — {self.period_name}"
            )
        if int(self.month) == 13:
            return (
                f"Year {self.year}, {self.month_name} (outside the four seasons, "
                f"patron {self.patron_titan}), Week {self.week}, Day {self.day} — "
                f"{self.period_name}"
            )
        return (
            f"Year {self.year}, {self.month_name} ({self.season} Season, "
            f"patron {self.patron_titan}), Week {self.week}, Day {self.day} — "
            f"{self.period_name}"
        )

    def format_short(self) -> str:
        if self.uncounted:
            return f"Year {self.year} · {self.month_name} · {self.period_name}"
        return (
            f"Year {self.year} · {self.month_name} · Week {self.week} · "
            f"Day {self.day} · {self.period_name}"
        )

    def to_dict(self) -> dict:
        d = {
            "year": self.year,
            "month": self.month,
            "week": self.week,
            "day": self.day,
            "period": self.period,
        }
        if self.uncounted:
            d["uncounted"] = self.uncounted
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "WorldClock":
        data = data or {}
        return cls(
            year=data.get("year", 4932),
            month=data.get("month", 9),
            week=data.get("week", 1),
            day=data.get("day", 1),
            period=data.get("period", 0),
            uncounted=data.get("uncounted"),
        )

    @classmethod
    def from_gmt8(cls, when: Optional[datetime] = None) -> "WorldClock":
        """1x overlay: now in GMT+8 mapped through the sanctuary civil table."""
        dt = when if when is not None else datetime.now(GMT8)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=GMT8)
        else:
            dt = dt.astimezone(GMT8)
        clock = cls.from_civil_date(dt.date())
        h = dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3.6e9
        clock.period = period_from_civil_hours(h)
        return clock

    @classmethod
    def from_civil_date(cls, d) -> "WorldClock":
        """Map a Gregorian date (Gate = 1 January) to a counted or Uncounted day."""
        y, doy = d.year, d.timetuple().tm_yday
        leap = calendar.isleap(y)
        lc_year = y + LIGHT_YEAR_OFFSET
        if leap:
            if doy == 366:
                return cls(year=lc_year, month=13, week=4, day=7, uncounted=UNC_ASTRORUM)
            if doy == 337:
                return cls(year=lc_year, month=12, week=4, day=7, uncounted=UNC_SCARLET)
            if doy >= 338:
                md = doy - 337
                month = 13
            else:
                md = doy
                month = (md - 1) // 28 + 1
                md = (md - 1) % 28 + 1
        else:
            if doy >= 365:
                return cls(year=lc_year, month=13, week=4, day=7, uncounted=UNC_ASTRORUM)
            md = doy
            month = (md - 1) // 28 + 1
            md = (md - 1) % 28 + 1
        week = (md - 1) // 7 + 1
        day = (md - 1) % 7 + 1
        return cls(year=lc_year, month=month, week=week, day=day)
