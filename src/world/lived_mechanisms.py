"""Lived day mechanisms — 17 ways the world *does* a day.

Entities in lived_entities.py are the furniture. These mechanisms are the
verbs: they mutate `world.vivid["lived"]` on an engine tick so Control Panel,
Gazette, and Visit can show facts the clock produced — not Heir hearsay.

Sanctuary: no dying, burying, starving, infecting, campaigning, or
storm-wreck. Night withdraws the Dawn Device even after a blazing day.
Rest = `clock.is_rest_time()` (Curtain-Fall or Entry Hour).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import lived_entities as le

# --------------------------------------------------------------------------- #
# Catalog — 17 mechanisms (id order is the visitor's list)
# --------------------------------------------------------------------------- #
CATALOG: List[Dict[str, str]] = [
    {"id": "keeping_time", "name": "Keeping time",
     "verb": "Many people keep the same Light Calendar hour."},
    {"id": "lighting", "name": "Lighting and withdrawing",
     "verb": "The Dawn Device lights the waking world and withdraws at night."},
    {"id": "sheltering", "name": "Sheltering",
     "verb": "A house keeps weather and night off the body; the road does not."},
    {"id": "feeding", "name": "Feeding",
     "verb": "Hearths take a meal from what harvest and bakers already hold."},
    {"id": "growing", "name": "Growing",
     "verb": "Fields sow or reap by the month — never both at once."},
    {"id": "carrying", "name": "Carrying",
     "verb": "Roads, dromases, ships, and letters move what does not walk itself."},
    {"id": "trading", "name": "Trading",
     "verb": "The square trades in waking hours; night and rest pack the stalls."},
    {"id": "making", "name": "Making",
     "verb": "Workshop, forge, and loom work by day and bank at night."},
    {"id": "gathering", "name": "Gathering",
     "verb": "A city is awake, or it quiets toward sleep."},
    {"id": "crossing", "name": "Crossing",
     "verb": "Gates and harbors take arrivals and farewells, especially at Parting."},
    {"id": "washing", "name": "Washing and drinking",
     "verb": "Wells, baths, and cisterns hold the day's water."},
    {"id": "cooling", "name": "Cooling and drying",
     "verb": "Wind cools labor and dries cloth — weather, not catastrophe."},
    {"id": "teaching", "name": "Teaching",
     "verb": "The Grove hands a craft or a canon on, strongest at Lucid Hour."},
    {"id": "tending", "name": "Tending",
     "verb": "A healer's house offers rest and balm — comfort in a life that goes on."},
    {"id": "offering", "name": "Offering",
     "verb": "Shrines take thanks and prayers. They are not grave-work."},
    {"id": "remembering", "name": "Remembering without burying",
     "verb": "Scroll, letter, and weaving keep a voice without a burial."},
    {"id": "resting", "name": "Resting",
     "verb": "Curtain-Fall and Entry Hour: the city rests; the Thief Star keeps watch."},
]

_MECH_IDS = [c["id"] for c in CATALOG]

_PRESENT_CITIES = (
    "Okhema", "Dawncloud", "Janusopolis", "Grove of Epiphany", "Great Tomb",
    "Castrum Kremnos", "Styxia", "Aidonia", "Aedes Elysiae", "Vortex of Genesis",
    "Eye of Twilight",
)

_FEED_CITIES = [c for c in _PRESENT_CITIES if c in le.CITYISH]


def clock_key(world) -> str:
    c = world.clock
    u = getattr(c, "uncounted", None) or ""
    if u:
        return f"{int(c.year)}-{u}-{int(c.period)}"
    return f"{int(c.year)}-{int(c.month)}-{int(c.week)}-{int(c.day)}-{int(c.period)}"


def date_key(world) -> str:
    c = world.clock
    u = getattr(c, "uncounted", None) or ""
    if u:
        return f"{int(c.year)}-{u}"
    return f"{int(c.year)}-{int(c.month)}-{int(c.week)}-{int(c.day)}"


def lived_bucket(world) -> dict:
    from .vivid_stage2 import vivid_bucket
    v = vivid_bucket(world)
    bucket = v.get("lived")
    if not isinstance(bucket, dict):
        bucket = {}
        v["lived"] = bucket
    return bucket


def letter_chance(flags: Optional[dict], period: int) -> float:
    """Engine letter rate. Rest is quieter; Parting carrying is busier.

    Does not itself send a letter — that stays the engine's existing compose.
    """
    flags = flags or {}
    if not flags:
        return 0.3
    if flags.get("resting"):
        return 0.08
    if flags.get("carrying") and int(period) == 3:
        return 0.55
    if flags.get("carrying"):
        return 0.40
    return 0.30


def _anyone_traveling(world) -> bool:
    try:
        if world.agent_travel:
            return True
    except Exception:
        pass
    try:
        return world.visitor_place().get("kind") == "traveling"
    except Exception:
        return False


def _travelers(world) -> List[str]:
    out: List[str] = []
    try:
        for cid, info in (world.agent_travel or {}).items():
            dest = (info or {}).get("to") or "another city"
            try:
                nm = world.name_of(cid)
            except Exception:
                nm = cid
            out.append(f"{nm} → {dest}")
    except Exception:
        pass
    try:
        vp = world.visitor_place()
        if vp.get("kind") == "traveling":
            out.append(f"the star-stranger → {vp.get('to')}")
    except Exception:
        pass
    return out


def _harvest_phase(month: int) -> str:
    if month == 4:
        return "sowing"
    if month in (5, 6):
        return "growing"
    if month == 8:
        return "reaping"
    if month == 9:
        return "granary"
    return "fallow"


def _lighting_state(world, night: bool, tags: set, period: int, month: int) -> str:
    if night:
        return "withdrawn"
    if "veiled" in tags or month == 3:
        return "veiled"
    if "blazing" in tags or month == 6:
        return "blazing"
    if period == 0:
        return "kindling"
    return "ordinary"


def derive(world, place: Optional[str] = None,
           character_id: Optional[str] = None,
           *, as_world_pulse: bool = False) -> Dict[str, Any]:
    """Pure snapshot of flags / active mechanisms / facts for this clock+place.

    Safe when the engine is stopped — no writes.
    `as_world_pulse` ignores the visitor's road so Gazette / persist flags
    describe the day's civic pulse (Okhema), not one body's stretch of path.
    """
    if as_world_pulse:
        traveling = False
        if not place:
            place = "Okhema"
    else:
        traveling = le._traveling(world, character_id)
        if not place:
            place = le.resolve_place(world, character_id)
    weather = le._weather_at(world, place)
    tags = le._sky_tags(weather)
    surged = le._surged_here(world, place)
    night = le._is_night(world)
    period = le._period_idx(world)
    month = le._month(world)
    try:
        rest = bool(world.clock.is_rest_time())
    except Exception:
        rest = period in (0, 4)
    pname = le._period_name(world)
    lighting = _lighting_state(world, night, tags, period, month)
    device_withdrawn = lighting == "withdrawn"
    harvest = _harvest_phase(month)
    anyone = _anyone_traveling(world)
    working = period in (1, 2)
    parting = period == 3
    # A Grove teaching-hall is not Okhema's square. Pulse ticks pass
    # as_world_pulse so a visitor on the road does not shut every market.
    market_here = (not traveling) and (place in le.CITYISH) and (place not in le.GROVE)
    market_open = (not rest) and working and market_here
    market_thin = bool(surged) and (market_open or (parting and market_here))
    market_packing = parting and not rest and not traveling
    gathering = (not rest) and (working or parting) and not traveling
    making = working and not rest
    teaching = working and not rest
    crossing = parting and not rest
    carrying = anyone or (parting and not rest)
    washing = (not traveling) and (place in le.CITYISH)
    cooling = ("windy" in tags) or ("wild" in tags) or month == 10
    tending = (not traveling) and (place in le.HEALER)
    offering = (not traveling) and (place in le.SHRINE) and (period == 0 or working)
    remembering = (period == 1) or (month == 9) or (place in le.SCROLL)
    sheltering = "road" if traveling else "inside"

    flags: Dict[str, Any] = {
        "keeping_time": True,
        "market_open": bool(market_open),
        "market_thin": bool(market_thin),
        "market_packing": bool(market_packing),
        "device_withdrawn": bool(device_withdrawn),
        "resting": bool(rest),
        "harvest_phase": harvest,
        "npc_abroad": bool(gathering),
        "gathering": bool(gathering),
        "carrying": bool(carrying),
        "making": bool(making),
        "teaching": bool(teaching),
        "crossing": bool(crossing),
        "sheltering": sheltering,
        "washing": bool(washing and not rest),
        "cooling": bool(cooling),
        "tending": bool(tending),
        "offering": bool(offering),
        "remembering": bool(remembering),
        "lighting": lighting,
        "forge_ringing": bool(making and period == 2 and place in le.FORGE),
        "night": bool(night),
        "surged": bool(surged),
        "traveling": bool(traveling),
    }

    rows, facts, active = _facts_for(
        flags, place, traveling, pname, weather, tags, month, period, anyone, world)

    return {
        "place": place,
        "traveling": traveling,
        "period": pname,
        "period_idx": period,
        "month": month,
        "night": night,
        "weather": weather,
        "surged": surged,
        "clock_key": clock_key(world),
        "date_key": date_key(world),
        "flags": flags,
        "mechanisms": rows,
        "active": active,
        "facts": facts,
        "travelers": _travelers(world),
    }


def _facts_for(flags: dict, place: str, traveling: bool, pname: str,
               weather: str, tags: set, month: int, period: int,
               anyone: bool, world) -> tuple:
    rows: List[dict] = []
    facts: List[str] = []
    active: List[dict] = []

    def add(mid: str, doing: bool, fact: str, here: bool = True) -> None:
        spec = next(c for c in CATALOG if c["id"] == mid)
        row = {"id": mid, "name": spec["name"], "verb": spec["verb"],
               "active": doing, "fact": fact, "here": here}
        rows.append(row)
        if doing and here:
            active.append(row)
            if fact:
                facts.append(fact)

    add("keeping_time", True, f"The Light Calendar keeps {pname}.")

    lit = flags["lighting"]
    if lit == "withdrawn":
        add("lighting", True,
            "The Dawn Device has withdrawn; lamps and the Thief Star take the watch.")
    elif lit == "veiled":
        add("lighting", True, "The Device burns behind a veil — day, but a dim one.")
    elif lit == "blazing":
        add("lighting", True, "The Device stands high and hot; work is done in its glare.")
    elif lit == "kindling":
        add("lighting", True,
            "The Device kindles Entry Hour — doors and prayers open with it.")
    else:
        add("lighting", True, "The Dawn Device holds ordinary day-light.")

    if traveling:
        add("sheltering", True,
            "On the road — the house is the city left behind or the one ahead.")
    else:
        add("sheltering", True, "Walls and a roof keep this hour's weather off the body.")

    # Feeding / growing facts are date-keyed; derive shows the phase, apply_tick
    # records which hearths actually took a meal.
    fed = {}
    try:
        fed = (lived_bucket(world).get("hearths_fed") or {}).get(date_key(world)) or []
    except Exception:
        fed = []
    if fed:
        shown = ", ".join(fed[:3])
        extra = " and other hearths" if len(fed) > 3 else ""
        add("feeding", True, f"Hearths took today's meal in {shown}{extra}.")
    elif not traveling and place in le.CITYISH:
        add("feeding", False, "Hearths will take today's meal when the day is lived.",
            here=True)
    else:
        add("feeding", False, "The road eats what you carry.", here=traveling)

    phase = flags["harvest_phase"]
    if phase == "sowing":
        add("growing", True,
            "Sowing, not reaping — Cultivation's hands are in the soil.")
    elif phase == "growing":
        add("growing", True, "Crops drink the light; brewing and swelling, not yet the full reaping.")
    elif phase == "reaping":
        add("growing", True, "The harvest comes in; granaries fill.")
    elif phase == "granary":
        add("growing", True,
            "Granaries hold what was reaped; this month remembers grain more than it cuts it.")
    else:
        add("growing", False,
            "The fields rest from this month's main work; only the calendar's turn.")

    if flags["carrying"]:
        named = _travelers(world)
        if named:
            add("carrying", True, "Carrying is underway: " + "; ".join(named[:3]) + ".")
        elif period == 3:
            add("carrying", True, "Parting Hour — wheels, dromases, and letters find the gates.")
        else:
            add("carrying", True, "The roads carry what must move.")
    else:
        add("carrying", False, "No long haul this hour.", here=False)

    if traveling:
        add("trading", False, "The market is in the city, not on this stretch of road.")
    elif flags["resting"]:
        add("trading", False, "Stalls are down; the square belongs to lamps and stray cats.")
    elif place in le.GROVE:
        add("trading", False,
            "The Grove keeps no market square; trade lives in the cities.", here=False)
    elif flags["market_thin"]:
        add("trading", True, "A thinner market — people buy what they need and keep close.")
    elif flags["market_packing"]:
        add("trading", True, "Stalls are packing; Parting Hour thins the square.")
    elif flags["market_open"] and period == 2:
        add("trading", True, "Action Hour: the square trades at its fullest.")
    elif flags["market_open"]:
        add("trading", True, "The market trades at an ordinary pace.")
    else:
        add("trading", False, "Trade waits for a waking square.")

    forge_here = place in le.FORGE
    shop_here = place in le.WORKSHOP
    if flags["resting"] or flags.get("night"):
        add("making", False, "The workshop is banked for the night; iron waits for Action Hour.",
            here=forge_here or shop_here)
    elif flags["making"] and forge_here and month == 10:
        add("making", True, "Kremnos' forges ring — iron for walls and tools in Strife's month.")
    elif flags["making"] and (forge_here or shop_here):
        add("making", True, "Hammers and benches — material becoming tools.")
    elif flags["making"]:
        add("making", True, "Somewhere a loom or a bench is at work.", here=False)
    else:
        add("making", False, "Making waits for Lucid and Action.", here=False)

    if traveling:
        add("gathering", False, "The city is ahead or behind; the road is what you have.")
    elif flags["gathering"]:
        add("gathering", True, f"{place} is awake around you.")
    else:
        add("gathering", False, f"{place} quiets toward sleep.")

    sea_here = place in le.SEA
    gate_here = place in le.GATES
    if flags["crossing"] and sea_here:
        add("crossing", True, "The harbor and the gates take the hour's farewells.")
    elif flags["crossing"] and gate_here:
        add("crossing", True, "The gates take farewells this hour.")
    elif flags["crossing"]:
        add("crossing", True, "Parting Hour — thresholds work.", here=gate_here or sea_here)
    elif period == 0 and gate_here:
        add("crossing", False, "The gates take the morning's first steps, quietly.")
    else:
        add("crossing", False, "Thresholds stand without a rush.", here=False)

    if traveling:
        add("washing", False, "Road water is what you carry; the city's baths wait at the next gate.")
    elif flags["washing"]:
        if place in {"Okhema", "Eternal Holy City"}:
            add("washing", True, "The Marmoreal baths and the city's wells — drink and wash.")
        else:
            add("washing", True, "Wells and cisterns of this place; the day's drink.")
    else:
        add("washing", False, "Cisterns hold the night's drink.", here=place in le.CITYISH)

    if flags["cooling"]:
        if "wild" in tags or "windy" in tags:
            add("cooling", True, "The wind has an edge; cloth snaps and a sleeve dries.")
        else:
            add("cooling", True, "A restless air cools a walk — enough to dry cloth, not a storm.")
    else:
        add("cooling", False, "A mild air moves; enough to dry a sleeve.")

    grove_here = place in le.GROVE or place in le.TEACHING
    if flags["teaching"] and grove_here and period == 1:
        add("teaching", True, "Lucid Hour in the Grove: pages, leaves, and quiet study.")
    elif flags["teaching"] and grove_here:
        add("teaching", True, "The teaching hall is at work.")
    elif grove_here and flags["resting"]:
        add("teaching", False, "The teaching hall is dark; lessons resume with Lucid Hour.")
    else:
        add("teaching", bool(flags["teaching"] and grove_here),
            "The Grove's teaching waits between hours.", here=grove_here)

    if flags["tending"]:
        add("tending", True,
            "The healer's house is open — rest, balm, and a body that will see another hour.")
    else:
        add("tending", False, "Comfort waits at a healer's door in another city.", here=False)

    if flags["offering"] and period == 0:
        add("offering", True, "Entry Hour prayers at the shrine — thanks, not grave-work.")
    elif flags["offering"]:
        add("offering", True, "The shrine holds offerings from those who already passed.")
    else:
        add("offering", False, "Shrines keep their quiet.", here=place in le.SHRINE)

    if flags["remembering"] and month == 9:
        add("remembering", True, "Looms and tongues both carry memory — Weaving's month.")
    elif flags["remembering"] and period == 1:
        add("remembering", True, "Lucid Hour — a good hour for a scroll or a letter.")
    elif flags["remembering"]:
        add("remembering", True, "Scrolls, letters, and thread keep what speech would drop.")
    else:
        add("remembering", False, "Memory sleeps on the shelf until a hand opens it.", here=False)

    if flags["resting"] and flags.get("night"):
        add("resting", True,
            "Curtain-Fall: the city rests. Only the Thief Star wanders the sky.")
    elif flags["resting"]:
        add("resting", True,
            "Entry Hour: the city is not yet at work; hearths and prayers hold the hour.")
    else:
        add("resting", False, "This is a working hour of the Light Calendar.")

    # Deduplicate facts while keeping order (growing may append twice).
    seen = set()
    uniq = []
    for f in facts:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return rows, uniq, active


def logic_faults(snap: Dict[str, Any]) -> List[str]:
    """Contradiction table. Empty = this hour is internally consistent."""
    faults: List[str] = []
    flags = snap.get("flags") or {}
    facts = " ".join(snap.get("facts") or []).lower()
    place = str(snap.get("place") or "")
    period = str(snap.get("period") or "")
    traveling = bool(snap.get("traveling") or flags.get("traveling"))
    night = bool(snap.get("night") or flags.get("night"))
    month = int(snap.get("month") or 0)
    weather = str(snap.get("weather") or "").lower()
    surged = bool(snap.get("surged") or flags.get("surged"))

    if flags.get("resting") and flags.get("market_open"):
        faults.append("Resting but market open")
    if flags.get("resting") and "busiest" in facts:
        faults.append("Market busiest while resting")
    if period.startswith("Curtain-Fall"):
        if flags.get("lighting") in ("blazing", "kindling"):
            faults.append("Curtain-Fall lighting high and hot")
        if "stands high and hot" in facts:
            faults.append("Lighting high and hot at Curtain-Fall")
        if "busiest" in facts or "square trades at its fullest" in facts:
            faults.append("Market busiest at Curtain-Fall")
        if "forges ring" in facts or flags.get("forge_ringing"):
            faults.append("Forge in full ring at Curtain-Fall")
        if flags.get("market_open"):
            faults.append("Market open at Curtain-Fall")
    if traveling and flags.get("sheltering") == "inside":
        faults.append("Inside a house while on the road")
    if traveling and ("square is yours" in facts or "square trades at its fullest" in facts):
        faults.append("Trading the square while on the road")
    if place in le.GROVE:
        if flags.get("market_open"):
            faults.append("Grove market open as a city square")
        if "square trades" in facts or "square trades at its fullest" in facts:
            faults.append("Busy square at the Grove")
        if any(k in facts for k in ("the sea is at", "harbor take", "ships meet")):
            faults.append("Sea/harbor here at the Grove")
        for row in snap.get("active") or []:
            if row.get("id") in ("crossing",) and "harbor" in (row.get("fact") or "").lower():
                if "gates" not in (row.get("fact") or "").lower():
                    faults.append("Harbor crossing at the Grove")
    if flags.get("harvest_phase") == "sowing" and "comes in" in facts and "sowing" not in facts:
        faults.append("Reaping during Cultivation")
    if month == 4 and "comes in" in facts and "sowing" not in facts:
        faults.append("Harvest coming in during Cultivation")
    if "veil" in weather and flags.get("lighting") == "blazing" and not night:
        faults.append("Blazing Device under a veiled sky")
    if flags.get("lighting") == "blazing" and flags.get("device_withdrawn"):
        faults.append("Blazing while the Device is withdrawn")
    if night and flags.get("lighting") != "withdrawn":
        faults.append("Night without Device withdrawn")
    if surged and ("busiest" in facts or "square trades at its fullest" in facts):
        faults.append("Feast-busy market under a tide surge")
    if flags.get("device_withdrawn") and "stands high and hot" in facts:
        faults.append("Withdrawn Device still high and hot")
    return faults


def apply_tick(world) -> Dict[str, Any]:
    """Persist + mutate lived state for this clock key. Idempotent per key.

    Feeding and growing mutate once per *date*. Returns flags, facts, and
    chronicle `lines` (empty on a repeated key).
    """
    bucket = lived_bucket(world)
    key = clock_key(world)
    dkey = date_key(world)
    snap = derive(world, place="Okhema", as_world_pulse=True)
    flags = dict(snap["flags"])

    if bucket.get("last_key") == key:
        return {
            "flags": bucket.get("flags") or flags,
            "facts": list(bucket.get("facts") or snap["facts"]),
            "active": list(bucket.get("active") or snap["active"]),
            "lines": [],
            "idempotent": True,
            "clock_key": key,
            "date_key": dkey,
        }

    lines: List[str] = []
    hearths = dict(bucket.get("hearths_fed") or {})
    growing = dict(bucket.get("growing_log") or {})

    if dkey not in hearths:
        hearths[dkey] = list(_FEED_CITIES)
        shown = ", ".join(_FEED_CITIES[:3])
        lines.append(f"Hearths took today's meal in {shown} and the other settlements.")
        flags["feeding"] = True
    else:
        flags["feeding"] = True
    if dkey not in growing:
        phase = flags["harvest_phase"]
        growing[dkey] = {"phase": phase, "fields": sorted(le.FIELDS)}
        if phase == "sowing":
            lines.append("Cultivation: the fields at Aedes Elysiae take seed, not the sickle.")
        elif phase == "reaping":
            lines.append("Reaping: the harvest comes in at the coastal fields.")
        elif phase == "growing":
            lines.append("The fields drink the light; swelling, not yet the full reaping.")
        else:
            lines.append(
                "The fields rest from this month's main work; granaries remember, they do not starve."
            )
    flags["hearths_fed"] = list(hearths.get(dkey) or [])
    flags["fed_today"] = True

    facts = list(snap["facts"])
    # Refresh feeding fact now that the date has been written.
    feed_fact = (
        f"Hearths took today's meal in {', '.join((hearths.get(dkey) or [])[:3])}"
        " and other hearths."
    )
    facts = [f for f in facts if "Hearths took today's meal" not in f and "will take today's meal" not in f]
    facts.insert(min(3, len(facts)), feed_fact)

    # Salient chronicle lines: lighting, civic, feeding/growing (already in lines).
    for row in snap["active"]:
        if row["id"] in {"lighting", "trading", "resting", "carrying", "gathering"}:
            if row.get("fact") and row["fact"] not in lines:
                lines.append(row["fact"])
    # Cap so the chronicle is a gazette, not a spec.
    lines = lines[:8]

    bucket["last_key"] = key
    bucket["date_key"] = dkey
    bucket["flags"] = flags
    bucket["gazette"] = list(lines)
    bucket["facts"] = facts
    bucket["active"] = [{"id": r["id"], "name": r["name"], "fact": r["fact"]}
                        for r in snap["active"]]
    bucket["hearths_fed"] = hearths
    bucket["growing_log"] = growing
    bucket["place"] = snap["place"]
    bucket["period"] = snap["period"]
    bucket["clock"] = ""
    try:
        bucket["clock"] = world.clock.format()
    except Exception:
        pass
    # Keep a handful of dates only.
    while len(hearths) > 10:
        hearths.pop(next(iter(hearths)))
    while len(growing) > 10:
        growing.pop(next(iter(growing)))

    snap["flags"] = flags
    snap["facts"] = facts
    faults = logic_faults(snap)
    bucket["faults"] = faults

    return {
        "flags": flags,
        "facts": facts,
        "active": snap["active"],
        "lines": lines,
        "idempotent": False,
        "clock_key": key,
        "date_key": dkey,
        "faults": faults,
    }


def _named_resident(name: str, role: Optional[str] = None) -> str:
    """Avoid 'Bartholos the a merchant' when the role already has an article."""
    r = (role or "resident").strip()
    who = (name or "someone").strip()
    if r.lower().startswith(("a ", "an ", "the ")):
        return f"{who}, {r}"
    return f"{who} the {r}"


def visitor_stage_lines(world, place: Optional[str] = None,
                        character_id: Optional[str] = None) -> List[str]:
    """Curated 2–4 literary beats for Visit / Gazette. Never a catalog."""
    snap = derive(world, place=place, character_id=character_id)
    flags = snap["flags"]
    place = snap["place"]
    traveling = snap["traveling"]
    period = snap["period"]
    weather = (snap.get("weather") or "").strip().rstrip(".")
    out: List[str] = []

    if traveling:
        head = f"{period} on the road from {place}."
    else:
        head = f"{period} in {place}."
    lit = flags.get("lighting")
    if lit == "withdrawn":
        light = "The Dawn Device is withdrawn"
    elif lit == "veiled":
        light = "The Device burns behind a veil"
    elif lit == "blazing":
        light = "The Device stands high and hot"
    elif lit == "kindling":
        light = "The Dawn Device kindles"
    else:
        light = "The Dawn Device holds ordinary day-light"
    if weather:
        out.append(f"{head} {light}; {weather}.")
    else:
        out.append(f"{head} {light}.")

    civic = ""
    if traveling:
        civic = "The house is behind or ahead; the road is what you have."
    elif flags.get("resting") and flags.get("device_withdrawn"):
        civic = "Hearths hold the houses. Stalls are down."
    elif flags.get("resting"):
        civic = "The city is not yet at work; hearths and prayers hold the hour."
    elif place in le.TEACHING and flags.get("teaching"):
        civic = "The teaching hall is at work."
    elif place in le.FORGE and flags.get("making") and not flags.get("resting"):
        civic = "The forge keeps the hour."
    elif flags.get("market_thin"):
        civic = "The square trades thinly; people buy what they need and keep close."
    elif flags.get("market_packing"):
        civic = "Stalls are packing; wheels find the gates."
    elif flags.get("market_open") and place in le.CITYISH and place not in le.GROVE:
        civic = "The square trades."
    elif flags.get("crossing") and place in le.GATES:
        civic = "The gates take farewells this hour."
    elif flags.get("making") and place in le.WORKSHOP:
        civic = "Hammers and benches keep the hour."
    elif flags.get("gathering"):
        civic = f"{place} is awake around you."
    if civic:
        out.append(civic)

    if not traveling and place in le.FIELDS:
        phase = flags.get("harvest_phase")
        if phase == "sowing":
            out.append("Hands are in the soil — Cultivation, not the reaping.")
        elif phase == "reaping":
            out.append("The coastal fields give; the harvest comes in.")
        elif phase == "growing":
            out.append("Crops drink the light along the shore fields.")
    elif not traveling and place in le.SEA:
        out.append("The sea is at the shore.")

    # 1–2 named residents actually here (lazy; no circular import at module load).
    try:
        from . import resident_npcs as _rn
        here = _rn.visible_in_city(world, place, flags=flags)[:2]
        if here and not traveling:
            if len(here) == 1:
                r = here[0]
                out.append(
                    f"{_named_resident(r['name'], r['role'])} is here this hour."
                )
            else:
                a, b = here[0], here[1]
                out.append(
                    f"{_named_resident(a['name'], a['role'])} and "
                    f"{_named_resident(b['name'], b['role'])} are here."
                )
        enc = _rn.last_encounter_for(world, place)
        if enc and not traveling:
            line = (enc.get("line") or "").strip()
            if line and len(out) < 4:
                out.append(line)
    except Exception:
        pass

    # Hard caps and contradiction trims.
    text = " ".join(out).lower()
    if flags.get("resting") or period.startswith("Curtain-Fall"):
        out = [ln for ln in out if "busiest" not in ln.lower()
               and "square trades at its fullest" not in ln.lower()]
    if place in le.GROVE:
        out = [ln for ln in out if "sea" not in ln.lower() and "harbor" not in ln.lower()]
    return out[:4]


def visitor_stage_paragraph(world, place: Optional[str] = None,
                            character_id: Optional[str] = None) -> str:
    return " ".join(visitor_stage_lines(world, place=place, character_id=character_id))


def gazette_world_items(world, fact_limit: int = 6,
                        encounter_limit: int = 3) -> Dict[str, List]:
    """Literary tick news for the Gazette — a handful, not a census."""
    bucket = {}
    try:
        bucket = lived_bucket(world)
    except Exception:
        bucket = {}
    facts = list(bucket.get("gazette") or [])
    if not facts:
        # Engine idle: a few live stage beats, never the full mechanism list.
        facts = visitor_stage_lines(world)[:3]
    encounters = []
    try:
        res = (getattr(world, "vivid") or {}).get("residents") or {}
        encounters = list(res.get("encounters") or [])
    except Exception:
        encounters = []
    return {
        "facts": facts[:fact_limit],
        "encounters": encounters[:encounter_limit],
        "period": bucket.get("period") or "",
        "clock": bucket.get("clock") or "",
    }


def road_stage_clause(world) -> str:
    """One extra road sentence: carrying / sheltering. No second weather."""
    try:
        flags = derive(world)["flags"]
    except Exception:
        return ""
    if flags.get("sheltering") == "road" or flags.get("traveling"):
        if flags.get("device_withdrawn"):
            return "Night holds the miles; the house waits in the next city."
        return "The road is the shelter; houses wait in the cities."
    return ""
