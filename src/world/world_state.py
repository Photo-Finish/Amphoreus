"""
World State — the little Amphoreus: the Light Calendar clock and the
persistent state of the world the Heirs live in.

The clock follows the canon Light Calendar (databank/world/calendar.md):
12 months in 4 seasons, 4 weeks/month, 7 days/week, 5 periods/day.
The world begins in the Month of Weaving — the month of memory and
storytelling — in the year after the long war ended.
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .map_data import travel_days as _travel_days
from .map_data import travel_days_for as _travel_days_for
from .map_data import can_cross_to as _map_can_cross_to
from .map_data import is_cross_era as _map_is_cross_era
from .map_data import TIME_FORMS as _TIME_FORMS, NETHER as _NETHER
from .schedules import scheduled_place, home_of as _sched_home

# --------------------------------------------------------------------- #
# Light Calendar
# --------------------------------------------------------------------- #
MONTHS = [
    # (name, season, patron titan)
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
]

PERIODS = [
    "Entry Hour",       # awakening, morning market, prayers
    "Lucid Hour",       # mental peak, conversation, scholarship
    "Action Hour",      # physical labor, exercise, revelry
    "Parting Hour",     # work ends, farewells, departures
    "Curtain-Fall Hour",  # rest and sleep
]

WEEKS_PER_MONTH = 4
DAYS_PER_WEEK = 7
PERIODS_PER_DAY = len(PERIODS)

# Where each Heir makes their home in the sanctuary (from their cards).
# NOTE: Hysilens is a knight commander serving Cerydra — she lives in Okhema,
# not in the ruined Styxia where she was born.
HOME_LOCATIONS: Dict[str, str] = {
    "tribbie": "Janusopolis",
    "cerydra": "Okhema",
    "evernight": "Okhema",
    "dan-heng-permansor-terrae": "Okhema",
    "hysilens": "Okhema",
    "hyacine": "Grove of Epiphany",
    "phainon": "Aedes Elysiae",
    "anaxa": "Grove of Epiphany",
    "aglaea": "Okhema",
    "mydei": "Castrum Kremnos",
    "castorice": "Aidonia",
    "cipher": "Okhema",
    "cyrene": "Aedes Elysiae",
}

# --------------------------------------------------------------------- #
# Guest companions — the Trailblazer's own, NOT residents of Amphoreus
# --------------------------------------------------------------------- #
# Dan Heng • Permansor Terrae and Evernight ride the Trailblaze path with
# the star-stranger; they are not residents of the sanctuary. Their presence
# in Amphoreus is a chance event: the Express drops in from time to time,
# stays a few days, and leaves again. The whole world keys off
# `guest_is_present()` so nothing ever treats them as constant Heirs.
GUEST_HEIRS: Dict[str, str] = {
    "dan-heng-permansor-terrae": "Dan Heng",
    "evernight": "Evernight",
}


def _stable_seed(text: str) -> int:
    """A stable per-key integer (independent of Python's hash randomization)."""
    s = 0
    for ch in text:
        s = (s * 31 + ord(ch)) & 0x7FFFFFFF
    return s


def _day_index(clock) -> int:
    """Total days since Year 4932, Month 1, Week 1, Day 1."""
    return ((clock.year - 4932) * 12 + (clock.month - 1)) * 28 \
        + (clock.week - 1) * 7 + (clock.day - 1)


def guest_is_present(cid: str, clock=None) -> bool:
    """Whether a guest companion is currently IN Amphoreus.

    Residents are always present. Guests follow a deterministic calendar
    pattern (stable within a single day, drifting across days): a visit of
    a few days, then a gap of a week or two, and occasionally a whole cycle
    without a visit. This is what makes their appearance "a chance event
    that happens from time to time" rather than a fixed residence. It is a
    pure function of the Light Calendar, so every process (world engine, UI,
    gazette) agrees on who is here today.
    """
    if cid not in GUEST_HEIRS:
        return True
    if clock is None:
        return True
    seed = _stable_seed(cid)
    day = _day_index(clock)
    cycle = 9 + (seed % 5)                # a visit-cycle lasts 9..13 days
    off = (seed >> 6) % cycle             # the visit starts at a hashed offset
    rel = (day - off) % cycle
    cidx = (day - off) // cycle
    visit = 4 + ((seed >> 3) + cidx) % 4  # a visit lasts 4..7 days (varies)
    skip = ((seed >> 9) + cidx * 3) % 12 == 0  # ~1 in 12 cycles: a longer leave
    return rel < visit and not skip


LOCATIONS: Dict[str, str] = {
    "Okhema": "the holy city beneath Kephale's gaze, where the Council of Elders once deliberated",
    "Janusopolis": "the twin city of gates and thresholds, home of the Holy Maiden",
    "Castrum Kremnos": "the fortress city of the spear, forever scarred by the God of Strife",
    "Grove of Epiphany": "the Grove of Reason, where scholars and prophets once walked",
    "Styxia": "the pale city of the afterlife, where death is a quiet neighbor",
    "Aidonia": "the city of the dead and the dawning, where Thanatos was honored",
    "Dawncloud": "the city of the Sunborn, bright under the Dawn Device",
    "Aedes Elysiae": "the ruined village of the Deliverer's childhood, now at peace",
    "Vortex of Genesis": "the sacred nexus where Coreflames were gathered to remake the world",
    "Great Tomb": "the resting place beneath the earth, solemn and still",
    # --- alternate forms: the Dawn-era echoes and the Nether (see map_data) ---
    "Eternal Holy City": "Okhema as it stood in the era of Dawn — the sunlit holy city beneath the Dawn Device",
    "Demigod Council": "Dawncloud's council seat shining under the Dawn Device, before the Veil fell",
    "Sanctum of Prophecy": "Janusopolis before the ruin — the Sanctum of Prophecy behind the Gates of Destiny",
    "Radiant Scarwood": "the Grove of Epiphany in sunlight, before the Murmuring Woods grew dark",
    "Bloodbathed Battlefront": "Castrum Kremnos in the Dawn — the battlefront before the Strife Ruins",
    "Warbling Shores": "Styxia before the River of Souls rose — the pearly shores of the dragon city",
    "Fortress of Dome": "the Eye of Twilight intact — the sky fortress before it fell",
    "Universal Matrix": "the Great Tomb in order — the Universal Matrix of the Nameless Titan",
    "Aedes Elysiae, of old": "the village before the flames — Phainon and Cyrene's Aedes Elysiae as it was",
    "The Nether": "the death-realm beneath Styxia — Thanatos's sea of flowers",
}


class WorldClock:
    """The Light Calendar clock of Amphoreus."""

    def __init__(self, year: int = 4932, month: int = 9, week: int = 1,
                 day: int = 1, period: int = 0):
        self.year = year
        self.month = month   # 1..12
        self.week = week     # 1..4
        self.day = day       # 1..7
        self.period = period  # 0..4

    def advance(self, periods: int = 1):
        """Advance the clock by a number of daily periods."""
        for _ in range(periods):
            self.period += 1
            if self.period >= PERIODS_PER_DAY:
                self.period = 0
                self.day += 1
                if self.day > DAYS_PER_WEEK:
                    self.day = 1
                    self.week += 1
                    if self.week > WEEKS_PER_MONTH:
                        self.week = 1
                        self.month += 1
                        if self.month > 12:
                            self.month = 1
                            self.year += 1

    @property
    def month_name(self) -> str:
        return MONTHS[self.month - 1][0]

    @property
    def season(self) -> str:
        return MONTHS[self.month - 1][1]

    @property
    def patron_titan(self) -> str:
        return MONTHS[self.month - 1][2]

    @property
    def period_name(self) -> str:
        return PERIODS[self.period]

    def is_rest_time(self) -> bool:
        """Whether most would be asleep (Curtain-Fall Hour or first Entry Hour)."""
        return self.period == 4 or self.period == 0

    def format(self) -> str:
        return (
            f"Year {self.year}, {self.month_name} ({self.season} Season, "
            f"patron {self.patron_titan}), Week {self.week}, Day {self.day} — "
            f"{self.period_name}"
        )

    def format_short(self) -> str:
        return f"Year {self.year} · {self.month_name} · Week {self.week} · Day {self.day} · {self.period_name}"

    def to_dict(self) -> dict:
        return {
            "year": self.year, "month": self.month, "week": self.week,
            "day": self.day, "period": self.period,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorldClock":
        return cls(
            year=data.get("year", 4932),
            month=data.get("month", 9),
            week=data.get("week", 1),
            day=data.get("day", 1),
            period=data.get("period", 0),
        )


class WorldState:
    """Persistent state of the little Amphoreus."""

    def __init__(self, state_path: Optional[str] = None):
        # A test / tool may redirect every WorldState() to a temp file via
        # AMPHOREUS_STATE_PATH (production never sets it).
        if state_path is None:
            state_path = os.environ.get(
                "AMPHOREUS_STATE_PATH", "world_runtime/world_state.json")
            # The default must be project-absolute: a relative path would
            # silently resolve against the process's working directory, so the
            # UI launched from elsewhere would read/write a DIFFERENT file than
            # the world engine (a real, subtle split-brain we hit on 2026-08-15).
            if not os.path.isabs(state_path):
                state_path = str(Path(__file__).resolve().parents[2] / state_path)
        self.state_path = state_path
        self._lock = threading.Lock()
        self.clock = WorldClock()
        self.agent_location: Dict[str, str] = dict(HOME_LOCATIONS)
        self.agent_travel: Dict[str, dict] = {}  # cid -> {"to": loc, "remaining_days": int, "from": loc}
        self.recent_events: List[str] = []
        self.ambient: Dict = {}  # the Keeper's day: {"weather": {city:...}, "errands": {cid:...}, "news": ...}
        # --- living texture (see src/world/world_events.py) ---
        self.rumors: Dict[str, list] = {}          # cid -> [rumor dicts]
        self.relationship_delta: Dict[str, int] = {}  # "a|b" -> drift -3..3
        self.letters: List[dict] = []              # letters between Heirs
        self.project_progress: Dict[str, int] = {} # cid -> steps done
        self.surge: Dict = {"active": False, "remaining": 0, "cities": []}
        self.companions: Dict[str, bool] = {}  # cid -> the star-stranger travels with them
        self.learned: Dict[str, list] = {}     # cid -> [things taught/told of beyond the stars]
        self.visitor_echo_ts: Dict[str, str] = {}  # cid -> last day the world gossiped of a visit
        # --- the second layer of life (see src/world/living_world.py) ---
        self.black_tide_enabled: bool = True   # A2 — the live tide is an OPTIONAL toggle
        self.mailbox: List[dict] = []          # A4 — letters & notices to/from the visitor
        self.npc_states: Dict[str, dict] = {}  # A5 — the residents' small arcs
        self.mood: Dict[str, dict] = {}        # B1 — each Heir's emotional weather
        self.play_mode: Optional[str] = None   # the visitor's UI-chosen experience (journey/aftermath); None = env default
        self.heir_voice: Optional[str] = None  # the visitor's chosen Heir voice model; None = the app default (gemma3:27b)
        self.realization: Dict[str, dict] = {}  # the witness ledger: cid -> {stage, quotes, since} (see src/core/realization.py)
        self.curiosity: Dict[str, dict] = {}    # the Heirs' minds: cid -> {questions, inferences} (see src/core/curiosity.py)
        self.horizons: Dict[str, list] = {}     # the changeable knowledge bank: cid -> [what they have come to know] (see src/core/horizons.py)
        self._load()

    # ------------------------------------------------------------------ #
    def _load(self):
        if not os.path.exists(self.state_path):
            return
        try:
            with self._lock:  # guard against torn reads while the engine writes
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.clock = WorldClock.from_dict(data.get("clock", {}))
                self.agent_location = {
                    **HOME_LOCATIONS,
                    **data.get("agent_location", {}),
                }
                self.agent_travel = data.get("agent_travel", {}) or {}
                self.recent_events = data.get("recent_events", [])[-20:]
                self.ambient = data.get("ambient", {}) or {}
                self.rumors = data.get("rumors", {}) or {}
                self.relationship_delta = data.get("relationship_delta", {}) or {}
                self.letters = data.get("letters", []) or []
                self.project_progress = data.get("project_progress", {}) or {}
                self.surge = data.get("surge", {"active": False, "remaining": 0, "cities": []})
                self.companions = data.get("companions", {}) or {}
                self.learned = data.get("learned", {}) or {}
                self.visitor_echo_ts = data.get("visitor_echo_ts", {}) or {}
                self.black_tide_enabled = data.get("black_tide_enabled", True)
                self.mailbox = data.get("mailbox", []) or []
                self.npc_states = data.get("npc_states", {}) or {}
                self.mood = data.get("mood", {}) or {}
                _pm = data.get("play_mode")
                self.play_mode = _pm if _pm in ("journey", "aftermath") else None
                _hv = data.get("heir_voice")
                self.heir_voice = _hv if isinstance(_hv, str) and _hv else None
                self.realization = data.get("realization", {}) or {}
                self.curiosity = data.get("curiosity", {}) or {}
                self.horizons = data.get("horizons", {}) or {}
        except Exception:
            pass

    def save(self):
        with self._lock:
            os.makedirs(os.path.dirname(os.path.abspath(self.state_path)), exist_ok=True)
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "clock": self.clock.to_dict(),
                        "agent_location": self.agent_location,
                        "agent_travel": self.agent_travel,
                        "recent_events": self.recent_events[-20:],
                        "ambient": self.ambient,
                        "rumors": self.rumors,
                        "relationship_delta": self.relationship_delta,
                        "letters": self.letters,
                        "project_progress": self.project_progress,
                        "surge": self.surge,
                        "companions": self.companions,
                        "learned": self.learned,
                        "visitor_echo_ts": self.visitor_echo_ts,
                        "black_tide_enabled": self.black_tide_enabled,
                        "mailbox": self.mailbox,
                        "npc_states": self.npc_states,
                        "mood": self.mood,
                        "play_mode": self.play_mode,
                        "heir_voice": self.heir_voice,
                        "realization": self.realization,
                        "curiosity": self.curiosity,
                        "horizons": self.horizons,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

    # ------------------------------------------------------------------ #
    def location_name(self, character_id: str) -> str:
        return self.agent_location.get(character_id, "Okhema")

    def name_of(self, character_id: str) -> str:
        """The Heir's display name (lazily loaded from the cards, cached)."""
        if character_id in getattr(self, "_names", {}):
            return self._names[character_id]
        try:
            from src.core.character_loader import CharacterLoader
            name = CharacterLoader("src/characters").load(character_id)["meta"]["name"]
        except Exception:
            name = character_id
        if not hasattr(self, "_names"):
            self._names = {}
        self._names[character_id] = name
        return name

    def location_desc(self, name: str) -> str:
        return LOCATIONS.get(name, "a quiet corner of Amphoreus")

    def set_location(self, character_id: str, location: str):
        if location in LOCATIONS:
            with self._lock:
                self.agent_location[character_id] = location
                self.agent_travel.pop(character_id, None)

    # ------------------------------------------------------------------ #
    def guest_status(self, character_id: str) -> str:
        """'present' | 'away' — where a guest companion stands today."""
        if character_id not in GUEST_HEIRS:
            return "resident"
        return "present" if guest_is_present(character_id, self.clock) else "away"

    def present_locations(self) -> Dict[str, str]:
        """agent_location minus the guest companions who are currently beyond
        Amphoreus (Dan Heng-PT & Evernight only drop in from time to time).
        Travelers are kept — someone on the road is still in Amphoreus."""
        return {
            cid: loc for cid, loc in self.agent_location.items()
            if guest_is_present(cid, self.clock)
        }

    # ------------------------------------------------------------------ #
    # Travel — moving between cities takes commuting time (map_data).
    # ------------------------------------------------------------------ #
    def begin_travel(self, character_id: str, destination: str,
                     blessed_as: Optional[str] = None):
        """Set a Heir on the road to `destination`. If the two places are the
        same city (travel_days == 0), the Heir simply moves there.

        A unique Titan border — the Veil of Evernight (Oronyx), the Gates of
        Destiny (Janus), the Nether (Thanatos) — stays closed unless the
        traveler is blessed for it. `blessed_as` lets one act on another's
        blessing (the Trailblazer carrying an Heir across time).
        """
        if destination not in LOCATIONS:
            return
        current = self.agent_location.get(character_id, "Okhema")
        traveler = blessed_as or character_id
        days = _travel_days_for(current, destination, traveler)
        if days >= 999:
            return  # the border does not open for this traveler
        if 0 < days:
            # A live black tide makes the road into a surged city one day longer.
            try:
                from .living_world import surge_travel_penalty
                days += surge_travel_penalty(self, destination)
            except Exception:
                pass
        if days <= 0:
            self.set_location(character_id, destination)
            return
        with self._lock:
            self.agent_travel[character_id] = {
                "to": destination,
                "remaining_days": days,
                "from": current,
            }

    def reachable_locations(self, character_id: str) -> List[str]:
        """The locations this Heir can actually reach (the Titan borders are
        closed to the unblessed), in LOCATIONS order."""
        current = self.agent_location.get(character_id, "Okhema")
        out = []
        for loc in LOCATIONS:
            if _travel_days_for(current, loc, character_id) < 999:
                out.append(loc)
        return out

    def carry_across(self, carrier_cid: str, destination: str) -> List[str]:
        """A blessed traveler crossing a Titan border (the Veil of Evernight or
        the Nether) carries any companion who shares their departure city
        across the borderline of time. Returns the ids carried."""
        carried: List[str] = []
        if destination not in LOCATIONS:
            return carried
        if not _map_can_cross_to(carrier_cid, destination):
            return carried
        origin = self.agent_location.get(carrier_cid)
        for cid in list(self.agent_location):
            if cid == carrier_cid or cid in self.agent_travel:
                continue
            if self.agent_location.get(cid) == origin and \
                    _travel_days_for(origin, destination, carrier_cid) < 999:
                self.begin_travel(cid, destination, blessed_as=carrier_cid)
                carried.append(cid)
        return carried

    def is_traveling(self, character_id: str) -> bool:
        return character_id in self.agent_travel

    def is_accompanied(self, character_id: str) -> bool:
        return bool(self.companions.get(character_id))

    def travel_info(self, character_id: str) -> Optional[dict]:
        return self.agent_travel.get(character_id)

    def advance_travel(self) -> List[tuple]:
        """Advance all in-transit Heirs by one day. Returns (cid, dest,
        accompanied) arrival records. A Heir who arrives is placed at their
        destination, and any shared journey with the star-stranger ends there."""
        arrivals: List[tuple] = []
        if not self.agent_travel:
            return arrivals
        with self._lock:
            for cid, info in list(self.agent_travel.items()):
                info["remaining_days"] -= 1
                if info["remaining_days"] <= 0:
                    dest = info["to"]
                    self.agent_location[cid] = dest
                    self.agent_travel.pop(cid, None)
                    accompanied = self.companions.pop(cid, False)
                    arrivals.append((cid, dest, accompanied))
        return arrivals

    # ------------------------------------------------------------------ #
    # Schedules — the Heirs' weekly routines (where they usually are).
    # ------------------------------------------------------------------ #
    def scheduled_place(self, character_id: str) -> str:
        """Where the Heir's weekly routine places them right now."""
        try:
            return scheduled_place(
                character_id, self.clock.day, self.clock.period
            )
        except Exception:
            return self.agent_location.get(character_id, "Okhema")

    def schedule_home(self, character_id: str) -> str:
        try:
            return _sched_home(character_id)
        except Exception:
            return self.agent_location.get(character_id, "Okhema")

    def agents_at(self, location: str) -> List[str]:
        # Only Heirs physically present — those on the road are counted nowhere.
        return [
            cid for cid, loc in self.agent_location.items()
            if loc == location and cid not in self.agent_travel
        ]

    def travelers(self) -> List[str]:
        return list(self.agent_travel.keys())

    def add_event(self, text: str):
        with self._lock:
            self.recent_events.append(text)
            self.recent_events = self.recent_events[-20:]

    def recent_events_text(self, limit: int = 5) -> str:
        return "\n".join(self.recent_events[-limit:])

    # ------------------------------------------------------------------ #
    # Ambient — the Keeper's stage (weather, errands, news)
    # ------------------------------------------------------------------ #
    def set_ambient(self, ambient: dict):
        with self._lock:
            self.ambient = ambient or {}

    def ambient_weather(self, location: str) -> str:
        try:
            return ((self.ambient.get("weather") or {}).get(location) or "").strip()
        except Exception:
            return ""

    def ambient_errand(self, character_id: str) -> str:
        """The day's request at this Heir's door, WITH its concrete cause."""
        try:
            v = (self.ambient.get("errands") or {}).get(character_id)
        except Exception:
            return ""
        if isinstance(v, dict):
            ask = str(v.get("ask", "") or "").strip()
            cause = str(v.get("cause", "") or "").strip()
            if ask and cause:
                return f"{ask} — the cause: {cause}"
            return ask
        return str(v or "").strip()

    def ambient_errand_cause(self, character_id: str) -> str:
        """Just the concrete cause/original impetus of today's errand."""
        try:
            v = (self.ambient.get("errands") or {}).get(character_id)
            if isinstance(v, dict):
                return str(v.get("cause", "") or "").strip()
        except Exception:
            pass
        return ""

    def ambient_news(self) -> str:
        try:
            return (self.ambient.get("news") or "").strip()
        except Exception:
            return ""

    # ------------------------------------------------------------------ #
    # The live black tide — an OPTIONAL toggle (A2, visitor mode)
    # ------------------------------------------------------------------ #
    def set_black_tide(self, enabled: bool):
        with self._lock:
            self.black_tide_enabled = bool(enabled)
            if not enabled:
                # winding the tide down also clears any active surge and the
                # darkened skies it left, so the world visibly returns to peace.
                try:
                    from .living_world import wind_down_surge
                    wind_down_surge(self)
                except Exception:
                    pass
        self.save()

    def set_play_mode(self, mode: Optional[str]):
        """Persist the visitor's chosen experience (journey/aftermath). None
        restores the env-var default."""
        mode = mode if mode in ("journey", "aftermath") else None
        with self._lock:
            self.play_mode = mode
        self.save()

    def set_heir_voice(self, voice: Optional[str]):
        """Persist the visitor's chosen Heir voice model. None restores the
        app default."""
        with self._lock:
            self.heir_voice = voice if isinstance(voice, str) and voice else None
        self.save()

    # ------------------------------------------------------------------ #
    # Senses — what the Heirs see and hear in the world right now
    # ------------------------------------------------------------------ #
    def sensory_text(self, location: str) -> str:
        """Describe the sights and sounds around a Heir at this moment."""
        period = self.clock.period_name
        month = self.clock.month_name
        season = self.clock.season

        # Sights & sounds of the hour
        hour_sense = {
            "Entry Hour": "The morning market stirs below; voices call out over the smell of bread; the light is gentle and new.",
            "Lucid Hour": "The streets are clear and bright; scholars converse, footsteps echo on the stone, and the day feels sharp and open.",
            "Action Hour": "Work and revelry sound around you — hammers, laughter, the splash of water; the sun stands high.",
            "Parting Hour": "Farewells are spoken at the gates; wheels roll onto the roads; the light begins to slant and lengthen.",
            "Curtain-Fall Hour": "The city quiets toward sleep; lamps flicker one by one, and the Thief Star crosses the darkening sky.",
        }.get(period, "The day moves around you, quietly.")

        # Weather cast by the season
        season_sense = {
            "Fate": f"The air of {month} carries the weight of doors opening and closing — renewal and farewell.",
            "Pillar": f"{month} makes the world feel rooted and alive; the earth is warm and generous.",
            "Creation": f"{month} is a season of memory and harvest — golden light, quiet storytelling, ripening fields.",
            "Calamity": f"{month} brings an edge to the wind — sharper moods, longer shadows, a hush before what comes.",
        }.get(season, "The weather is mild and unremarkable.")

        # Today's sky, set by the Keeper (the Ambient World Director)
        today = self.ambient_weather(location)
        if today:
            season_sense = f"Today, {today}."

        # Local character
        local = {
            "Okhema": "The murmur of the holy city, the chime of offerings, the vast stillness of Kephale's mountain above.",
            "Janusopolis": "Twin gates and the sound of thresholds creaking; pilgrims' footsteps; the soft churn of the river of doors.",
            "Castrum Kremnos": "The ring of the forge and the clatter of spears; stone walls that still remember war.",
            "Grove of Epiphany": "Leaves shifting in the breeze; pages turning; the quiet hum of scholarship and prayer.",
            "Styxia": "A pale hush; the distant toll of a bell; the sense of many presences just beyond sight.",
            "Aidonia": "Stillness and candlelight; the murmur of the dead remembered; soft earth underfoot.",
            "Dawncloud": "Bright, warm, and orderly; the hum of the Dawn Device; the chatter of the Sunborn.",
            "Aedes Elysiae": "The wind through a ruined village at peace; birdsong where silence used to reign; the smell of wild grass.",
            "Vortex of Genesis": "The deep hum of sacred machinery; light folding on itself; an overwhelming sense of beginning.",
            "Great Tomb": "Profound quiet; the whisper of stone; the weight of ages resting beneath you.",
        }.get(location, "The sounds of this place are soft and familiar.")

        return (
            f"You see and hear right now: {hour_sense} {local} {season_sense}"
        )

    # ------------------------------------------------------------------ #
    # Visitor presence (shared with the chat UI)
    # ------------------------------------------------------------------ #
    @property
    def visitor_flag_path(self) -> str:
        return os.path.join(os.path.dirname(self.state_path), "visitor_active")

    def mark_visitor_present(self):
        """The UI calls this on each chat turn."""
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.visitor_flag_path, "w") as f:
                f.write(datetime.now().isoformat())
        except Exception:
            pass

    def visitor_present(self, window_seconds: int = 600) -> bool:
        """Whether the visitor has been active recently."""
        try:
            mtime = os.path.getmtime(self.visitor_flag_path)
            return (datetime.now().timestamp() - mtime) < window_seconds
        except Exception:
            return False
