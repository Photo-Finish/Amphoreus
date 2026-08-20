"""Ecosystem — living non-human presence that ticks with the day.

Sits beside lived entities (furniture) and mechanisms (day-verbs). This layer
is *who lives here besides people*: chimeras, dromas herds, wheat, shore life,
grove leaf, grass and wind. Status is derived from Light Calendar + place +
mechanism flags, with a few **gated** care mutations (Heir tends an ailing
chimera). Never authors Heir speech. Never opens the knowledge wall.

Sanctuary: no famine, plague, war, death-as-mechanic. Ailing is temporary and
curable; care restores *well*, it does not invent a grave.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Tuple

from . import lived_entities as le
from . import eco_voice as voice

# --------------------------------------------------------------------------- #
# Place families for living kinds
# --------------------------------------------------------------------------- #
CHIMERA_CITIES = {"Okhema", "Eternal Holy City", "Dawncloud"}
# Road beasts on inhabited roads — not sky forts, tombs, or sacred nexuses.
DROMAS_ROADS = {
    "Okhema", "Eternal Holy City", "Dawncloud", "Janusopolis",
    "Castrum Kremnos", "Bloodbathed Battlefront", "Styxia", "Warbling Shores",
    "Aidonia", "Aedes Elysiae", "Aedes Elysiae, of old", "Sanctum of Prophecy",
    "Grove of Epiphany", "Radiant Scarwood",
}
DROMAS_STRONG = set(DROMAS_ROADS)
SHORE = set(le.SEA)
# Working seashore life (nets, sirens, tidepools) — Vortex is a Coreflame nexus, not a fishing quay.
WORKING_SHORE = {
    "Styxia", "Warbling Shores", "Aedes Elysiae", "Aedes Elysiae, of old",
}
GROVE = set(le.GROVE)
# Living timber vs underground matrix / tomb of the Nameless Titan.
LIVING_GROVE = {"Grove of Epiphany", "Radiant Scarwood"}
TOMB_PLACES = {"Great Tomb", "Universal Matrix"}
FIELDS = set(le.FIELDS)
# Ordinary civic markets — not council chambers, battlefronts, sky ruins, or death-snow.
MARKET_CITIES = {
    "Okhema", "Eternal Holy City", "Dawncloud", "Janusopolis",
    "Castrum Kremnos", "Styxia", "Warbling Shores",
    "Aedes Elysiae", "Aedes Elysiae, of old",
}
# Public wells / cisterns of settlement life.
WELL_CITIES = {
    "Okhema", "Eternal Holy City", "Dawncloud", "Janusopolis",
    "Castrum Kremnos", "Styxia", "Warbling Shores", "Aidonia",
    "Aedes Elysiae", "Aedes Elysiae, of old", "Sanctum of Prophecy",
}
# Sky castrum / battlefront / council chamber — sparse outdoor texture only.
SPARSE_CITIES = {
    "Eye of Twilight", "Fortress of Dome", "Bloodbathed Battlefront",
    "Demigod Council", "The Nether", "Beyond Time", "Vortex of Genesis",
}

# Indoor furniture lives in lore / mechanisms. The land UI is outdoors.
INDOOR_LAND = frozenset({"bath", "hearth", "loom", "scroll", "lamp"})

# Visual / interact kinds the Visit UI knows how to paint.
KIND_VISUAL = {
    "chimera": "chimera",
    "dromas": "dromas",
    "dromas_calf": "dromas_calf",
    "wheat": "wheat",
    "shore": "shore",
    "grove_leaf": "leaf",
    "grass": "grass",
    "wind": "wind",
    "resident": "resident",
    "hearth_cat": "cat",
    "dawn": "dawn",
    "thief_star": "star",
    "lamp": "lamp",
    "hearth": "hearth",
    "bath": "bath",
    "well": "well",
    "shrine": "shrine",
    "market_stall": "stall",
    "forge": "forge",
    "loom": "loom",
    "scroll": "scroll",
    "gate": "gate",
    "siren": "siren",
    "maze": "maze",
    "pebble": "pebble",
    "pearl": "pearl",
    "fountain": "fountain",
    "olive": "olive",
    "cicada": "cicada",
    "laundry": "laundry",
    "boat": "boat",
    "net": "net",
    "ribbon": "ribbon",
    "mosaic": "mosaic",
    "courier": "courier",
    "banner": "banner",
    "incense": "incense",
    "kite": "kite",
    "mill": "mill",
    "tidepool": "tidepool",
    "pillar": "pillar",
}

# Place-family art stems (Visit loads ``{stem}_{family}.png`` when present).
ART_FAMILY_OKHEMA = frozenset({"Okhema", "Eternal Holy City", "Dawncloud"})
ART_FAMILY_AEDES = frozenset({"Aedes Elysiae", "Aedes Elysiae, of old"})
ART_FAMILY_JANUS = frozenset({"Janusopolis", "Sanctum of Prophecy"})
ART_FAMILY_KREMNOS = frozenset({"Castrum Kremnos", "Bloodbathed Battlefront"})
ART_FAMILY_STYXIA = frozenset({"Styxia", "Warbling Shores"})
ART_FAMILY_GROVE = frozenset({"Grove of Epiphany", "Radiant Scarwood"})
ART_FAMILY_AIDONIA = frozenset({"Aidonia"})

# Kinds that meaningfully differ by place family → asset prefix (stall_okhema…).
_PLACE_ART_PREFIX = {
    "market_stall": "stall",
    "well": "well",
    "fountain": "fountain",
    "shrine": "shrine",
    "gate": "gate",
    "forge": "forge",
    "banner": "banner",
    "laundry": "laundry",
    "boat": "boat",
    "ribbon": "ribbon",
    "pillar": "pillar",
    "mosaic": "mosaic",
    "mill": "mill",
}


def art_family_for(place: str) -> str:
    """Map a location to a pictorial family for env sprites."""
    if place in ART_FAMILY_OKHEMA:
        return "okhema"
    if place in ART_FAMILY_AEDES:
        return "aedes"
    if place in ART_FAMILY_JANUS:
        return "janus"
    if place in ART_FAMILY_KREMNOS:
        return "kremnos"
    if place in ART_FAMILY_STYXIA:
        return "styxia"
    if place in ART_FAMILY_GROVE:
        return "grove"
    if place in ART_FAMILY_AIDONIA:
        return "aidonia"
    return "civic"


def place_visual_for(kind: str, place: str) -> str:
    """Sprite asset stem for a being — place family when art can differ."""
    base = KIND_VISUAL.get(kind, "life")
    prefix = _PLACE_ART_PREFIX.get(kind)
    if not prefix:
        return base
    family = art_family_for(place)
    if family == "civic":
        return base
    return f"{prefix}_{family}"

# Whitelist: only these Heir → action → kind transitions may mutate state.
# Anything else is refused. No clock, location, bond, or other Heir writes.
CARE_AUTH: Dict[str, Dict[str, dict]] = {
    "hyacine": {
        "tend_ailment": {
            "kinds": {"chimera", "dromas"},
            "from_status": {"ailing"},
            "to_status": "well",
            "note": "tended with balm and rest; the body will see another hour",
        },
        "bless_water": {
            "kinds": {"well", "bath"},
            "from_status": {"well", "open", "resting"},
            "to_status": "blessed",
            "note": "a healer's thanks over the day's water — still only water",
        },
    },
    "phainon": {
        "calm_beast": {
            "kinds": {"dromas"},
            "from_status": {"restless"},
            "to_status": "well",
            "note": "a familiar hand and a quiet word; the beast settles",
        },
    },
    "cyrene": {
        "soothe_maze": {
            "kinds": {"grove_leaf", "wheat", "maze", "cicada", "olive"},
            "from_status": {"uneasy", "singing"},
            "to_status": "well",
            "note": "a remembered song; the small life softens",
        },
    },
    "aglaea": {
        "thread_notice": {
            "kinds": {"chimera", "resident", "loom", "mosaic", "laundry", "ribbon"},
            "from_status": {
                "ailing", "well", "wandering", "resting", "here", "weaving",
                "hanging", "quiet", "open",
            },
            "to_status": None,
            "note": "golden threads mark the life as seen; nothing is forced",
            "mutate": False,
        },
    },
    "hysilens": {
        "hush_shore": {
            "kinds": {"shore", "siren", "tidepool", "boat", "net"},
            "from_status": {"uneasy", "full", "well", "resting", "moored"},
            "to_status": "hushed",
            "note": "a low song; the water keeps its own counsel",
        },
    },
    "mydei": {
        "still_anvil": {
            "kinds": {"forge"},
            "from_status": {"ringing", "banked"},
            "to_status": "steady",
            "note": "a Kremnoan hand on the hammer; the iron waits, it is not a weapon-order",
        },
        "read_banner": {
            "kinds": {"banner"},
            "from_status": {"open", "furled", "well"},
            "to_status": None,
            "note": "the banner is read, not commanded",
            "mutate": False,
        },
    },
    "cipher": {
        "watch_stall": {
            "kinds": {"market_stall", "courier"},
            "from_status": {"open", "down", "well", "resting", "flying"},
            "to_status": None,
            "note": "a thief's eye counts the square; nothing is taken",
            "mutate": False,
        },
    },
    "tribbie": {
        "greet_gate": {
            "kinds": {"gate"},
            "from_status": {"open", "quiet", "well"},
            "to_status": None,
            "note": "a thousand-gated hello — the door is still a door",
            "mutate": False,
        },
    },
    "anaxa": {
        "open_scroll": {
            "kinds": {"scroll"},
            "from_status": {"open", "shelved", "well"},
            "to_status": None,
            "note": "a page turned; the Grove keeps its argument",
            "mutate": False,
        },
    },
    "evernight": {
        "name_star": {
            "kinds": {"thief_star"},
            "from_status": {"out", "well"},
            "to_status": None,
            "note": "the Thief Star is named, not commanded",
            "mutate": False,
        },
    },
    "dan-heng-permansor-terrae": {
        "listen_earth": {
            "kinds": {"grass", "dromas", "wheat", "olive", "mill", "pillar"},
            "from_status": {
                "well", "stirring", "sowing", "growing", "hauling", "vigorous",
                "resting", "quiet", "turning",
            },
            "to_status": None,
            "note": "the earth answers underfoot; nothing is taken",
            "mutate": False,
        },
    },
}

# Old act ids still accepted by visitor_touch.
_ACT_ALIASES = {
    "pet_cat": "pet",
    "scratch_ear": "pet",
}

# Visitor-only ambient acts (never Heir writes, never clock/bonds).
VISITOR_ACT: Dict[str, dict] = {
    "pick_keepsake": {
        "kinds": {"pebble", "pearl"},
        "note": "you pocket a small thing the land was already giving back",
    },
    "leave_offering": {
        "kinds": {"shrine"},
        "note": "thanks left at stone — not a grave, not a bargain",
    },
    "sit_hearth": {
        "kinds": {"hearth"},
        "note": "you sit a while; the hearth keeps the hour",
    },
    "wave": {
        "kinds": {"resident"},
        "note": "a passerby answers with a nod",
    },
    "drink": {
        "kinds": {"well", "bath", "fountain"},
        "note": "cool water; the day goes on",
    },
    "touch_air": {
        "kinds": {"wind", "grass", "kite"},
        "note": "the air of this hour moves through your fingers",
    },
    "pet": {
        "kinds": {"chimera", "hearth_cat", "dromas", "dromas_calf"},
        "note": "they lean into the touch, then remain themselves",
        "notes": {
            "chimera": "a small head under your fingers — Awoo, pleased, not a command",
            "hearth_cat": "the cat leans in, then remembers it is its own cat",
            "dromas": "the neck plates warm under your palm; the road-beast does not hurry",
            "dromas_calf": "the calf bumps your hand, soft plates still learning the road",
        },
    },
    "greet_dromas": {
        "kinds": {"dromas", "dromas_calf"},
        "note": "the dromas blows warm earth-scent at your sleeve",
    },
    "soak": {
        "kinds": {"bath", "tidepool"},
        "note": "you rest a hand in the water; it is only water",
    },
    "look_up": {
        "kinds": {"dawn", "thief_star"},
        "note": "you look up; the sky does not owe you an answer",
    },
    "step_through": {
        "kinds": {"gate"},
        "note": "a threshold underfoot — Janus's ordinary door",
    },
    "listen_iron": {
        "kinds": {"forge"},
        "note": "iron rings, then waits; you do not order a blade",
    },
    "watch_thread": {
        "kinds": {"loom"},
        "note": "the shuttle clicks; cloth remembers the month",
    },
    "trail_maze": {
        "kinds": {"maze"},
        "note": "you walk the maze-edge a little; it keeps its small ecology",
    },
    "brush_grain": {
        "kinds": {"wheat"},
        "note": "heads nod against your palm; this is not a harvest",
    },
    "rest_shade": {
        "kinds": {"olive", "grove_leaf", "pillar"},
        "note": "shade holds a minute; the place does not become yours",
    },
    "hang_ribbon": {
        "kinds": {"ribbon"},
        "note": "a scrap of thanks on the line — not a bargain, not a grave",
    },
    "watch_water": {
        "kinds": {"fountain", "shore", "tidepool"},
        "note": "you watch the water work; it was already working",
    },
    "follow_bird": {
        "kinds": {"courier"},
        "note": "the bird is already going; you only watch the line it cuts",
    },
    "read_cloth": {
        "kinds": {"banner", "laundry"},
        "note": "cloth speaks in dye and weather, not in orders",
    },
    "breathe_incense": {
        "kinds": {"incense"},
        "note": "a thin sweet smoke; thanks, not a summons",
    },
    "listen_cicada": {
        "kinds": {"cicada"},
        "note": "the grove's small brass — a season, not a message",
    },
    "glance_hull": {
        "kinds": {"boat", "net"},
        "note": "hull and mesh at rest; you do not take a boat",
    },
    "trace_mosaic": {
        "kinds": {"mosaic"},
        "note": "a thumb along gold and stone; the floor keeps the city",
    },
    "hum_mill": {
        "kinds": {"mill"},
        "note": "stone turns as it has turned; you do not take grain",
    },
    "linger_lamp": {
        "kinds": {"lamp"},
        "note": "you stand in the lamp's small day until your eyes adjust",
    },
    "read_page": {
        "kinds": {"scroll"},
        "note": "a line the Grove already wrote; you do not finish the argument",
    },
}


# Hard bans — never writable via care API.
_FORBIDDEN_KEYS = frozenset({
    "clock", "_sim_clock", "agent_location", "bonds", "mailbox", "rumors",
    "ambient", "surge", "play_mode", "heir_voice", "visitor_location",
})


def eco_bucket(world) -> dict:
    v = getattr(world, "vivid", None)
    if not isinstance(v, dict):
        v = {}
        world.vivid = v
    bucket = v.setdefault("eco", {})
    bucket.setdefault("beings", {})       # id -> mutable care overlay
    bucket.setdefault("scene", [])        # last derived scene objects
    bucket.setdefault("audit", [])        # gated care log
    bucket.setdefault("last_key", "")
    bucket.setdefault("gazette", [])
    return bucket


def _h(seed: str) -> int:
    return int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16)


def _period(world) -> int:
    try:
        return int(getattr(world.clock, "period", 0) or 0)
    except Exception:
        return 0


def _month(world) -> int:
    try:
        return int(getattr(world.clock, "month", 9) or 9)
    except Exception:
        return 9


def _date_seed(world) -> str:
    try:
        c = world.clock
        return f"{c.year}-{c.month}-{getattr(c, 'week', 1)}-{c.day}-p{c.period}"
    except Exception:
        return "seed"


def _place_of(world, character_id: Optional[str] = None) -> Tuple[str, bool]:
    traveling = False
    place = "Okhema"
    try:
        if character_id:
            traveling = bool(world.travel_info(character_id))
            place = world.location_name(character_id) or place
        else:
            vp = world.visitor_place()
            if vp.get("kind") == "traveling":
                traveling = True
                place = vp.get("from") or place
            else:
                place = vp.get("at") or world.visitor_location or place
    except Exception:
        pass
    return place, traveling


def _flags(world) -> dict:
    try:
        lived = (getattr(world, "vivid") or {}).get("lived") or {}
        return dict(lived.get("flags") or {})
    except Exception:
        return {}


def _overlay(world, oid: str) -> dict:
    return dict((eco_bucket(world).get("beings") or {}).get(oid) or {})


def _set_overlay(world, oid: str, patch: dict) -> None:
    bucket = eco_bucket(world)
    beings = dict(bucket.get("beings") or {})
    cur = dict(beings.get(oid) or {})
    cur.update(patch)
    beings[oid] = cur
    # Cap overlays so care history cannot grow without bound.
    if len(beings) > 80:
        # Keep most recently tended.
        items = sorted(
            beings.items(),
            key=lambda kv: str(kv[1].get("tended_at") or ""),
            reverse=True,
        )
        beings = dict(items[:60])
    bucket["beings"] = beings


def _base_status(kind: str, place: str, period: int, month: int,
                 flags: dict, seed: str, oid: str) -> Tuple[str, str]:
    """Return (status, doing) before care overlay."""
    resting = bool(flags.get("resting")) or period in (0, 4)
    night = period == 4 or bool(flags.get("device_withdrawn"))
    surged = bool(flags.get("surged") or flags.get("market_thin"))

    if kind == "chimera":
        if resting or night:
            return "resting", "curled near a hearth, quiet for the night"
        # Deterministic rare ailment — never a plague wave.
        if _h(seed + oid + "ail") % 17 == 0:
            return "ailing", "listless, needing a healer's gentle hand"
        if surged:
            return "wandering", "staying close to handlers; the square feels thin"
        return "wandering", "trotting the baths and stalls, howling soft Awoos"

    if kind == "dromas":
        if resting or night:
            return "resting", "in the yard, earth-scented and still"
        if month == 4:
            return "vigorous", "doubly vigorous on Cultivation's roads"
        if _h(seed + oid + "restless") % 23 == 0:
            return "restless", "refusing the sandpit, eyes wary"
        if period in (2, 3):
            return "hauling", "moving goods between cities this hour"
        return "well", "waiting at the workshop gates"

    if kind == "dromas_calf":
        if resting or night:
            return "resting", "a calf tucked near the yard fence"
        if month == 4:
            return "playful", "a calf learning Cultivation's busy roads"
        return "well", "a calf keeping near the adult beasts"

    if kind == "wheat":
        if month == 4:
            return "sowing", "seed in Georios' soil — Cultivation"
        if month == 8:
            return "reaping", "fields stripping toward gold — Reaping"
        if month in (5, 6):
            return "growing", "drinking the light along the shore fields"
        if _h(seed + oid + "uneasy") % 29 == 0:
            return "uneasy", "a dry hush in a corner of the maze-edge wheat"
        return "well", "coastal fields under this month's slower work"

    if kind == "shore":
        if resting or night:
            return "resting", "hulls at quay; the Ocean breathes in the dark"
        if month == 5:
            return "full", "nets fuller in the Month of Joy"
        return "well", "shore-trade and fish, not a storm"

    if kind == "grove_leaf":
        if resting or night:
            return "resting", "leaves hold the night's quiet"
        if period == 1:
            return "well", "shade for pages and quiet study"
        if _h(seed + oid + "uneasy") % 31 == 0:
            return "uneasy", "a restless rustle among Cerces' timber"
        return "well", "leaf and timber around the Grove"

    if kind == "grass":
        if resting or night:
            return "resting", "blades still under withdrawn light"
        if "windy" in str(flags.get("weather_tags") or "") or flags.get("cooling"):
            return "stirring", "grass bows and lifts with the cooling air"
        return "well", "soft ground-cover at the city's edge"

    if kind == "wind":
        if flags.get("cooling"):
            return "stirring", "a restless air cools a walk"
        return "mild", "a mild air moves; enough to dry a sleeve"

    if kind == "hearth_cat":
        if resting or night:
            return "resting", "a stray cat owns the quiet square"
        return "wandering", "weaving between stalls for crumbs"

    if kind == "dawn":
        if night or flags.get("device_withdrawn"):
            return "withdrawn", "the Dawn Device has withdrawn; night holds the miles"
        if flags.get("lighting") == "veiled":
            return "veiled", "the Device burns behind a veil"
        return "high", "the Device holds this hour's light"

    if kind == "thief_star":
        if night or flags.get("device_withdrawn"):
            return "out", "the Thief Star takes the night road"
        return "hidden", "hidden under ordinary day"

    if kind == "lamp":
        if night or resting:
            return "lit", "lamps take the watch the Device left"
        return "banked", "day-lamps wait for Curtain-Fall"

    if kind == "hearth":
        if resting or night:
            return "holding", "hearths hold the houses — meal and warmth"
        return "lit", "a working hearth; food and talk"

    if kind == "bath":
        if resting or night:
            return "quiet", "Marmoreal water holds the night"
        return "open", "baths and wells — drink and wash"

    if kind == "well":
        return "open" if not night else "resting", (
            "cisterns hold the night's drink" if night else "the day's drink at the well"
        )

    if kind == "shrine":
        if period == 0:
            return "open", "Entry Hour prayers — thanks, not grave-work"
        return "quiet", "offerings already given"

    if kind == "market_stall":
        if resting or night or not flags.get("market_open"):
            return "down", "stalls are down; the square belongs to lamps"
        if period == 2:
            return "open", "Action Hour: the square trades"
        return "open", "ordinary trade"

    if kind == "forge":
        if resting or night:
            return "banked", "iron waits for Action Hour"
        return "ringing", "hammers; ore becoming tools"

    if kind == "loom":
        if month == 9:
            return "weaving", "looms carry memory — Weaving's month"
        if resting:
            return "resting", "the loom is still for the night"
        return "well", "cloth on the body and on the beam"

    if kind == "scroll":
        if period == 1:
            return "open", "Lucid Hour — a good hour to open a page"
        if resting:
            return "shelved", "the hall is dark; pages wait"
        return "shelved", "speech that outlives the speaker, on a shelf"

    if kind == "gate":
        if period == 3:
            return "open", "Parting Hour — farewells at the threshold"
        if period == 0:
            return "quiet", "first steps, quietly"
        return "open", "Janus's door, ordinary"

    if kind == "siren":
        if resting or night:
            return "resting", "the Ocean breathes; song waits"
        if month == 5:
            return "full", "sirens fuller in the Month of Joy"
        if _h(seed + oid + "uneasy") % 19 == 0:
            return "uneasy", "a song a little off the usual tide"
        return "well", "a low shore-song, not a storm"

    if kind == "maze":
        if month == 13:
            return "open", "Membrance: the maze remembers as a place"
        if _h(seed + oid + "uneasy") % 31 == 0:
            return "uneasy", "a dry hush at the maze-edge"
        return "quiet", "the wheat-village maze keeps its small ecology"

    if kind == "pebble":
        return "well", "a road-stone the size of a thumb"

    if kind == "pearl":
        return "well", "a pale shore-pearl the sea keeps giving back"

    if kind == "fountain":
        if night or resting:
            return "quiet", "the fountain keeps a low night-voice"
        return "open", "water talking to stone in the square"

    if kind == "olive":
        if resting or night:
            return "quiet", "olives hold the Grove's dark"
        return "well", "silver leaves; shade for a page"

    if kind == "cicada":
        if resting or night:
            return "quiet", "the brass of the grove is still"
        if month in (5, 6, 7):
            return "singing", "cicadas keep the hot hours"
        return "well", "a thin seasonal note in the timber"

    if kind == "laundry":
        if night or resting:
            return "in", "lines empty; cloth sleeps indoors"
        if flags.get("cooling") or "windy" in str(flags.get("weather_tags") or ""):
            return "hanging", "wash taking the cooling air"
        return "hanging", "color on the line, ordinary as bread"

    if kind == "boat":
        if resting or night:
            return "moored", "hulls sleep against the quay"
        return "well", "a working hull; not yours to take"

    if kind == "net":
        if month == 5:
            return "full", "nets heavier in the Month of Joy"
        if resting or night:
            return "resting", "mesh drying in the withdrawn light"
        return "well", "shore-work, not a storm"

    if kind == "ribbon":
        if period == 0:
            return "open", "new thanks tied at Entry Hour"
        return "quiet", "old scraps of thanks still on the line"

    if kind == "mosaic":
        if night:
            return "quiet", "gold in the floor holds the lamps"
        return "well", "a public floor remembering a city's feet"

    if kind == "courier":
        if resting or night:
            return "resting", "the bird is in for the night"
        return "flying", "a line of errand across ordinary air"

    if kind == "banner":
        if resting or night:
            return "furled", "cloth waits for Action Hour"
        return "open", "Kremnoan color on the wind — a city, not a march"

    if kind == "incense":
        if period == 0:
            return "open", "a thin morning thanks"
        if resting or night:
            return "quiet", "the stick has gone to ash"
        return "well", "a household sweetness, not a summons"

    if kind == "kite":
        if night or resting:
            return "down", "kites sleep; the sky is the Device's"
        if flags.get("cooling") or period in (2, 3):
            return "up", "a child's color on the field-wind"
        return "down", "paper waiting for a kinder air"

    if kind == "mill":
        if resting or night:
            return "quiet", "the mill-stone waits"
        if month in (4, 8):
            return "turning", "stone turning with the year's grain-work"
        return "well", "a coastal mill at ordinary work"

    if kind == "tidepool":
        if resting or night:
            return "resting", "the pool holds the night's small sky"
        return "well", "anemone and clear water; a shore's pocket"

    if kind == "pillar":
        return "well", "a public column taking the hour's light"

    return "well", "present this hour"


def _caravan_this_hour(world, place: str, flags: dict, period: int, month: int) -> bool:
    """Sometimes a dromas is on the road as a trade caravan with people."""
    if flags.get("resting") or period in (0, 4):
        return False
    h = _h(_date_seed(world) + str(place) + "caravan")
    if month == 4 and period in (2, 3):
        return h % 2 == 0
    if period in (2, 3):
        return h % 3 == 0
    return h % 5 == 0


def _apply_trade_caravan(out: List[dict], world, place: str,
                         flags: dict, period: int, month: int, *,
                         traveling: bool = False) -> None:
    """Tag dromas + several people as one orderly trade caravan.

    A caravan is usually more than one beast and one walker — typically a
    pair of dromas (sometimes with a calf) and three or four people.
    """
    dromases = [b for b in out if b.get("kind") in {"dromas", "dromas_calf"}]
    adults = [b for b in dromases if b.get("kind") == "dromas"]
    calves = [b for b in dromases if b.get("kind") == "dromas_calf"]
    if not adults and not calves:
        return
    if not traveling and not _caravan_this_hour(world, place, flags, period, month):
        return
    # Ensure at least two adult mounts when the hour calls for a caravan.
    if len(adults) < 2:
        nxt = 1 + max(
            (int(str(b.get("id") or "").rsplit(":", 1)[-1])
             for b in adults if ":" in str(b.get("id") or "")),
            default=0,
        )
        while len(adults) < 2:
            extra = _mk_being("dromas", place, nxt, world, flags, None)
            out.append(extra)
            adults.append(extra)
            nxt += 1
    # A calf sometimes trails the train.
    if not calves and (_h(_date_seed(world) + str(place) + "calf") % 3 == 0):
        calf = _mk_being("dromas_calf", place, 1, world, flags, None)
        out.append(calf)
        calves.append(calf)

    cid = f"caravan:{place}:1"
    mounts = adults[:2] + calves[:1]
    for i, mount in enumerate(mounts):
        mount["caravan_id"] = cid
        mount["caravan_role"] = "mount" if mount.get("kind") == "dromas" else "calf"
        if mount.get("kind") == "dromas_calf":
            mount["doing"] = "a calf keeping pace with the trade caravan"
        else:
            mount["doing"] = "under harness with a trade caravan"

    def _score(b: dict) -> int:
        role = str(b.get("role") or "").lower()
        if "dromas" in role or "handler" in role:
            return 0
        if "merchant" in role or "courier" in role:
            return 1
        return 2

    residents = [b for b in out if b.get("kind") == "resident"]
    residents.sort(key=_score)
    mates = list(residents[:4])
    # Usually three or four walkers — never a lonely handler beside one beast.
    want = 3 + (_h(_date_seed(world) + str(place) + "crew") % 2)
    need = max(0, want - len(mates))
    roles = (
        ("dromas-handler", "a dromas-handler", "resident_handler"),
        ("merchant", "a merchant of the road", "resident_merchant"),
        ("courier", "a courier with the train", "resident"),
        ("field-hand", "a porter with the train", "resident_field"),
    )
    for j in range(need):
        role, label, visual = roles[j % len(roles)]
        handler = {
            "id": f"resident:{place}:caravan-{role}-{j + 1}",
            "kind": "resident",
            "name": label,
            "place": place,
            "status": "here",
            "doing": f"{role} with the trade caravan",
            "role": role,
            "spot": "road",
            "sound": None,
            "visual": visual,
            "clickable": True,
            "care_hint": "",
            "hotspot": hotspot_for("resident", j + 2),
            "visitor_acts": visitor_acts_for("resident"),
            "caravan_id": cid,
            "caravan_role": "handler" if j == 0 else "trader",
        }
        out.append(handler)
        mates.append(handler)
    for i, m in enumerate(mates[:4]):
        m["caravan_id"] = cid
        m["caravan_role"] = "handler" if i == 0 else "trader"
        role = m.get("role") or "a traveler"
        m["doing"] = f"{role} with the trade caravan"


def _mk_being(kind: str, place: str, idx: int, world, flags: dict,
              character_id: Optional[str] = None) -> dict:
    seed = _date_seed(world)
    oid = f"{kind}:{place}:{idx}"
    period = _period(world)
    month = _month(world)
    status, doing = _base_status(kind, place, period, month, flags, seed, oid)
    ov = _overlay(world, oid)
    if ov.get("status"):
        # Care overlay lasts only for the Light-Calendar date it was applied.
        tended_date = ov.get("tended_date")
        today = seed.rsplit("-p", 1)[0]
        if tended_date == today:
            status = ov["status"]
            if ov.get("doing"):
                doing = ov["doing"]

    name = {
        "chimera": "a little chimera",
        "dromas": "a dromas of the road",
        "dromas_calf": "a dromas calf",
        "wheat": "the coastal wheat",
        "shore": "the shore's living breath",
        "grove_leaf": "the Grove's leaf and timber",
        "grass": "the grass at the edge",
        "wind": "the air of this hour",
        "hearth_cat": "a square cat",
        "dawn": "the Dawn Device",
        "thief_star": "the Thief Star",
        "lamp": "a night lamp",
        "hearth": "a household hearth",
        "bath": "the Marmoreal baths",
        "well": "a city well",
        "shrine": "a shrine of thanks",
        "market_stall": "a market stall",
        "forge": "a forge",
        "loom": "a loom",
        "scroll": "an open scroll",
        "gate": "a city gate",
        "siren": "a sea-siren's song",
        "maze": "the Membrance maze-edge",
        "pebble": "a road pebble",
        "pearl": "a shore-pearl",
        "fountain": "a public fountain",
        "olive": "an olive of the Grove",
        "cicada": "a grove cicada",
        "laundry": "wash on the line",
        "boat": "a moored hull",
        "net": "a working net",
        "ribbon": "a ribbon of thanks",
        "mosaic": "a floor mosaic",
        "courier": "an errand-bird",
        "banner": "a city banner",
        "incense": "a stick of incense",
        "kite": "a field kite",
        "mill": "a coastal mill",
        "tidepool": "a tide pool",
        "pillar": "a public column",
    }.get(kind, kind)
    if kind == "chimera" and idx > 1:
        name = "another little chimera"
    if kind == "dromas" and idx > 1:
        name = "another dromas"
    elif kind == "dromas_calf":
        name = "a dromas calf"
    elif kind == "market_stall":
        stall_names = (
            "a fruit stall",
            "a cloth stall",
            "a sweet stall",
            "a pottery stall",
        )
        name = stall_names[(max(1, idx) - 1) % len(stall_names)]
        stall_doing = (
            "grapes and summer fruit under a gold awning",
            "cloth and dye for the square",
            "wrapped sweets and small honey cakes",
            "jars and bowls for the household",
        )
        if status == "open":
            doing = stall_doing[(max(1, idx) - 1) % len(stall_doing)]
            if period == 2:
                doing = f"Action Hour — {doing}"

    if place and kind != "dawn":
        name = voice.flavor_name(place, kind, idx, name)
        doing = voice.flavor_doing(place, kind, status, doing, period, idx)

    sound = None
    if kind == "chimera":
        sound = "Awoo"
    elif kind == "dromas":
        sound = "a low earth-rumble"
    elif kind == "hearth_cat":
        sound = "mrrrow"
    elif kind == "shore":
        sound = "a soft pull of tide"
    elif kind == "grove_leaf":
        sound = "a rustle of leaf"
    elif kind == "siren":
        sound = "a low shore-song"
    elif kind == "forge":
        sound = "a ring of iron"
    elif kind == "loom":
        sound = "a shuttle's click"
    elif kind == "gate":
        sound = "a hinge's breath"
    elif kind == "thief_star":
        sound = "a far crimson prick of light"
    elif kind == "fountain":
        sound = "water on stone"
    elif kind == "cicada":
        sound = "a thin brass of summer"
    elif kind == "laundry":
        sound = "cloth taking air"
    elif kind == "boat":
        sound = "hull against rope"
    elif kind == "net":
        sound = "mesh dripping"
    elif kind == "courier":
        sound = "a wing-cut of errand"
    elif kind == "banner":
        sound = "cloth on a dry wind"
    elif kind == "incense":
        sound = "a quiet sweetness"
    elif kind == "kite":
        sound = "paper against air"
    elif kind == "mill":
        sound = "stone turning"
    elif kind == "tidepool":
        sound = "a pocket of tide"
    elif kind == "olive":
        sound = "silver leaves"
    elif kind == "mosaic":
        sound = "a shoe on gold-and-stone"
    elif kind == "pillar":
        sound = "stone taking light"
    elif kind == "ribbon":
        sound = "scrap-cloth in a doorway"

    being = {
        "id": oid,
        "kind": kind,
        "name": name,
        "place": place,
        "status": status,
        "doing": doing,
        "sound": sound,
        "visual": place_visual_for(kind, place),
        "art_family": art_family_for(place),
        "clickable": True,
        "care_hint": _care_hint(status, kind),
        "hotspot": hotspot_for(kind, idx),
        "visitor_acts": visitor_acts_for(kind),
    }
    return being


def hotspot_for(kind: str, idx: int) -> dict:
    """Where to paint a clickable hotspot on the scene (percent CSS)."""
    table = {
        "chimera": ("22%", "16%"),
        "dromas": ("72%", "12%"),
        "dromas_calf": ("64%", "10%"),
        "wheat": ("40%", "6%"),
        "shore": ("50%", "4%"),
        "grove_leaf": ("30%", "48%"),
        "grass": ("18%", "3%"),
        "wind": ("80%", "68%"),
        "hearth_cat": ("58%", "12%"),
        "dawn": ("48%", "76%"),
        "thief_star": ("82%", "80%"),
        "well": ("64%", "12%"),
        "shrine": ("12%", "14%"),
        "market_stall": ("36%", "14%"),
        "forge": ("78%", "12%"),
        "gate": ("50%", "10%"),
        "siren": ("70%", "8%"),
        "maze": ("28%", "8%"),
        "pebble": ("16%", "5%"),
        "pearl": ("62%", "6%"),
        "fountain": ("46%", "12%"),
        "olive": ("20%", "16%"),
        "cicada": ("34%", "42%"),
        "laundry": ("86%", "28%"),
        "boat": ("78%", "6%"),
        "net": ("68%", "5%"),
        "ribbon": ("14%", "26%"),
        "mosaic": ("50%", "4%"),
        "courier": ("70%", "62%"),
        "banner": ("84%", "32%"),
        "incense": ("8%", "16%"),
        "kite": ("60%", "68%"),
        "mill": ("32%", "12%"),
        "tidepool": ("56%", "5%"),
        "pillar": ("28%", "12%"),
        "resident": ("40%", "14%"),
    }
    left, bottom = table.get(kind, ("50%", "20%"))
    if kind == "market_stall":
        # Dedicated vendor row across Okhema's square.
        stall_spots = (
            ("18%", "12%"),
            ("34%", "13%"),
            ("50%", "12%"),
            ("66%", "14%"),
        )
        left, bottom = stall_spots[(max(1, idx) - 1) % len(stall_spots)]
    elif idx > 1:
        # Nudge extras so two chimeras/dromases don't stack.
        try:
            lp = max(6, min(90, int(left.strip("%")) + (idx - 1) * 14))
            left = f"{lp}%"
        except Exception:
            pass
    return {"left": left, "bottom": bottom}


def visitor_acts_for(kind: str) -> list:
    return [aid for aid, spec in VISITOR_ACT.items() if kind in spec["kinds"]]


def _role_doing(role: Optional[str], spot: Optional[str]) -> str:
    r = (role or "a resident").strip()
    here = spot or "street"
    if r.lower().startswith(("a ", "an ")):
        return f"{r} at the {here}"
    return f"{r} at the {here}"


def _care_hint(status: str, kind: str) -> str:
    if status == "ailing" and kind in {"chimera", "dromas"}:
        return "Hyacine could tend this life."
    if status == "restless" and kind == "dromas":
        return "A familiar hand (Phainon) might calm them."
    if status == "uneasy" and kind in {"grove_leaf", "wheat", "maze"}:
        return "Cyrene's remembrance might soothe them."
    if kind in {"shore", "siren"}:
        return "Hysilens knows this water."
    if kind == "scroll":
        return "Anaxa would open this page."
    if kind == "forge":
        return "Mydei knows this iron."
    if kind in {"cicada", "olive"}:
        return "Cyrene's remembrance knows this shade."
    return ""


def derive_scene(world, place: Optional[str] = None,
                 character_id: Optional[str] = None,
                 include_residents: bool = True) -> List[dict]:
    """Interactive + visual beings for *this* place and hour."""
    if not place:
        place, traveling = _place_of(world, character_id)
    else:
        traveling = False
        try:
            if character_id and world.travel_info(character_id):
                traveling = True
        except Exception:
            pass

    flags = _flags(world)
    period = _period(world)
    month = _month(world)
    out: List[dict] = []

    if traveling:
        out.append(_mk_being("wind", place, 1, world, flags, character_id))
        out.append(_mk_being("grass", place, 1, world, flags, character_id))
        out.append(_mk_being("dromas", place, 1, world, flags, character_id))
        out.append(_mk_being("pebble", place, 1, world, flags, character_id))
        if flags.get("device_withdrawn") or period == 4:
            out.append(_mk_being("thief_star", place, 1, world, flags, character_id))
        _apply_trade_caravan(out, world, place, flags, period, month, traveling=True)
        return out[:8]

    # Sky / hour furniture (the Device and the Thief Star — not household lamps)
    out.append(_mk_being("dawn", place, 1, world, flags, character_id))
    if period == 4 or flags.get("device_withdrawn"):
        out.append(_mk_being("thief_star", place, 1, world, flags, character_id))

    # Place-bound life
    if place in CHIMERA_CITIES:
        n = 2 if period in (1, 2) and not flags.get("resting") else 1
        for i in range(1, n + 1):
            out.append(_mk_being("chimera", place, i, world, flags, character_id))
        if flags.get("resting") or period in (0, 4):
            out.append(_mk_being("hearth_cat", place, 1, world, flags, character_id))

    if place in DROMAS_ROADS:
        out.append(_mk_being("dromas", place, 1, world, flags, character_id))
        if month == 4 and period in (2, 3):
            out.append(_mk_being("dromas", place, 2, world, flags, character_id))
        # A calf sometimes keeps near the adult beasts (outside caravan hours too).
        if period in (1, 2, 3) and not flags.get("resting"):
            if _h(_date_seed(world) + str(place) + "baby-dromas") % 4 == 0:
                out.append(_mk_being("dromas_calf", place, 1, world, flags, character_id))

    if place in FIELDS:
        out.append(_mk_being("wheat", place, 1, world, flags, character_id))
        out.append(_mk_being("grass", place, 1, world, flags, character_id))
        out.append(_mk_being("maze", place, 1, world, flags, character_id))

    if place in WORKING_SHORE:
        out.append(_mk_being("shore", place, 1, world, flags, character_id))
        out.append(_mk_being("siren", place, 1, world, flags, character_id))
        out.append(_mk_being("pearl", place, 1, world, flags, character_id))

    if place in LIVING_GROVE:
        out.append(_mk_being("grove_leaf", place, 1, world, flags, character_id))
    elif place in TOMB_PLACES:
        # Nameless Titan matrix — solemn ruin texture, not a scholar's grove picnic.
        out.append(_mk_being("grove_leaf", place, 1, world, flags, character_id))
        out.append(_mk_being("pillar", place, 1, world, flags, character_id))

    if (
        place not in GROVE
        and place not in SPARSE_CITIES
        and place in le.CITYISH
    ):
        out.append(_mk_being("grass", place, 1, world, flags, character_id))
        out.append(_mk_being("wind", place, 1, world, flags, character_id))
        if place in WELL_CITIES:
            out.append(_mk_being("well", place, 1, world, flags, character_id))
        if flags.get("market_open") and place in MARKET_CITIES:
            # Okhema is the densest square; other living markets get a pair.
            if place == "Okhema":
                n_stalls = 4
            elif place in {"Eternal Holy City", "Dawncloud"}:
                n_stalls = 2
            elif place in ART_FAMILY_JANUS | ART_FAMILY_STYXIA:
                n_stalls = 2
            elif place in ART_FAMILY_AEDES | ART_FAMILY_KREMNOS:
                n_stalls = 2 if place in ART_FAMILY_AEDES else 1
            else:
                n_stalls = 1
            for i in range(1, n_stalls + 1):
                out.append(_mk_being(
                    "market_stall", place, i, world, flags, character_id,
                ))

    # Sparse / high / sacred places still feel air and ground underfoot.
    if place in {"Eye of Twilight", "Fortress of Dome", "Vortex of Genesis"}:
        out.append(_mk_being("wind", place, 1, world, flags, character_id))
        out.append(_mk_being("pebble", place, 1, world, flags, character_id))
    if place in {"Bloodbathed Battlefront", "Demigod Council"}:
        out.append(_mk_being("wind", place, 1, world, flags, character_id))
        out.append(_mk_being("grass", place, 1, world, flags, character_id))
    if place == "The Nether":
        out.append(_mk_being("wind", place, 1, world, flags, character_id))
    if place == "Beyond Time":
        out.append(_mk_being("wind", place, 1, world, flags, character_id))
    if place in TOMB_PLACES:
        out.append(_mk_being("wind", place, 1, world, flags, character_id))
        out.append(_mk_being("pebble", place, 1, world, flags, character_id))

    if place in le.SHRINE and place not in {"Demigod Council"}:
        # Demigod Council keeps incense without a street shrine booth.
        out.append(_mk_being("shrine", place, 1, world, flags, character_id))
        out.append(_mk_being("incense", place, 1, world, flags, character_id))
    elif place == "Demigod Council":
        out.append(_mk_being("incense", place, 1, world, flags, character_id))
        out.append(_mk_being("pillar", place, 1, world, flags, character_id))
        out.append(_mk_being("fountain", place, 1, world, flags, character_id))
    if place in le.FORGE:
        out.append(_mk_being("forge", place, 1, world, flags, character_id))
        out.append(_mk_being("banner", place, 1, world, flags, character_id))
    if place in le.GATES:
        out.append(_mk_being("gate", place, 1, world, flags, character_id))
    if (
        place in le.CITYISH
        and place not in GROVE
        and place not in SPARSE_CITIES
    ):
        out.append(_mk_being("pebble", place, 1, world, flags, character_id))
    if place == "Bloodbathed Battlefront":
        out.append(_mk_being("pebble", place, 1, world, flags, character_id))
        out.append(_mk_being("pillar", place, 1, world, flags, character_id))

    # Regional texture — different places, not the same Okhema list everywhere.
    if place in {"Okhema", "Eternal Holy City", "Dawncloud"}:
        out.append(_mk_being("mosaic", place, 1, world, flags, character_id))
        out.append(_mk_being("fountain", place, 1, world, flags, character_id))
        out.append(_mk_being("pillar", place, 1, world, flags, character_id))
        if not (flags.get("resting") or period in (0, 4)):
            out.append(_mk_being("laundry", place, 1, world, flags, character_id))
            out.append(_mk_being("courier", place, 1, world, flags, character_id))
    if place in ART_FAMILY_JANUS:
        out.append(_mk_being("fountain", place, 1, world, flags, character_id))
        out.append(_mk_being("incense", place, 1, world, flags, character_id))
        out.append(_mk_being("ribbon", place, 1, world, flags, character_id))
        if not (flags.get("resting") or period in (0, 4)):
            out.append(_mk_being("courier", place, 1, world, flags, character_id))
    if place == "Castrum Kremnos":
        out.append(_mk_being("pillar", place, 1, world, flags, character_id))
        if not (flags.get("resting") or period in (0, 4)):
            out.append(_mk_being("courier", place, 1, world, flags, character_id))
    if place in ART_FAMILY_STYXIA:
        out.append(_mk_being("fountain", place, 1, world, flags, character_id))
        out.append(_mk_being("incense", place, 1, world, flags, character_id))
        if not (flags.get("resting") or period in (0, 4)):
            out.append(_mk_being("courier", place, 1, world, flags, character_id))
    if place in ART_FAMILY_AIDONIA:
        out.append(_mk_being("incense", place, 1, world, flags, character_id))
        out.append(_mk_being("pillar", place, 1, world, flags, character_id))
        out.append(_mk_being("ribbon", place, 1, world, flags, character_id))
    if place in LIVING_GROVE:
        out.append(_mk_being("olive", place, 1, world, flags, character_id))
        out.append(_mk_being("cicada", place, 1, world, flags, character_id))
        out.append(_mk_being("fountain", place, 1, world, flags, character_id))
        out.append(_mk_being("wind", place, 1, world, flags, character_id))
        out.append(_mk_being("grass", place, 1, world, flags, character_id))
        out.append(_mk_being("pebble", place, 1, world, flags, character_id))
    if place in WORKING_SHORE:
        out.append(_mk_being("boat", place, 1, world, flags, character_id))
        out.append(_mk_being("net", place, 1, world, flags, character_id))
        out.append(_mk_being("tidepool", place, 1, world, flags, character_id))
    elif place in le.RIVER and place not in TOMB_PLACES:
        out.append(_mk_being("boat", place, 1, world, flags, character_id))
    if place in FIELDS:
        out.append(_mk_being("mill", place, 1, world, flags, character_id))
        out.append(_mk_being("kite", place, 1, world, flags, character_id))
        out.append(_mk_being("cicada", place, 1, world, flags, character_id))
    if place in {"Eye of Twilight", "Fortress of Dome"}:
        out.append(_mk_being("pillar", place, 1, world, flags, character_id))
        out.append(_mk_being("kite", place, 1, world, flags, character_id))
        out.append(_mk_being("grass", place, 1, world, flags, character_id))
    if place == "Vortex of Genesis":
        out.append(_mk_being("pillar", place, 1, world, flags, character_id))
    if place in {"Castrum Kremnos", "Bloodbathed Battlefront"} and place not in GROVE:
        out.append(_mk_being("banner", place, 1, world, flags, character_id))

    # Named residents as interactive ambient (cap 3) — identity on click.
    if include_residents and not traveling:
        try:
            from . import resident_npcs as rn
            for i, r in enumerate(rn.greet_here(world, place, limit=3), start=1):
                rid = f"resident:{place}:{r.get('name')}"
                out.append({
                    "id": rid,
                    "kind": "resident",
                    "name": r.get("name") or "a passerby",
                    "place": place,
                    "status": "here",
                    "doing": _role_doing(r.get("role"), r.get("spot")),
                    "role": r.get("role"),
                    "spot": r.get("spot"),
                    "sound": None,
                    "visual": rn.outfit_for_role(r.get("role")),
                    "clickable": True,
                    "care_hint": "",
                    "hotspot": hotspot_for("resident", i),
                    "visitor_acts": visitor_acts_for("resident"),
                })
        except Exception:
            pass

    _apply_trade_caravan(out, world, place, flags, period, month, traveling=False)

    # Contradiction: strip sea/chimera if somehow in Grove / tomb
    if place in GROVE:
        out = [b for b in out if b["kind"] not in {
            "chimera", "shore", "hearth_cat", "siren", "bath", "market_stall",
            "pearl", "forge", "laundry", "mosaic", "boat", "net", "tidepool",
            "banner", "well",
        }]
    if place in TOMB_PLACES:
        out = [b for b in out if b["kind"] not in {
            "olive", "cicada", "fountain", "market_stall", "well", "laundry",
            "chimera", "shore", "siren", "boat", "net", "tidepool", "dromas",
            "dromas_calf", "kite", "mill", "maze", "wheat", "banner", "forge",
        }]
    if place == "Vortex of Genesis":
        out = [b for b in out if b["kind"] not in {
            "shore", "siren", "pearl", "boat", "net", "tidepool", "market_stall",
            "well", "dromas", "dromas_calf", "laundry", "chimera",
        }]
    if place in {"Eye of Twilight", "Fortress of Dome"}:
        out = [b for b in out if b["kind"] not in {
            "market_stall", "well", "dromas", "dromas_calf", "laundry",
            "chimera", "shore", "siren", "boat", "net", "forge",
        }]
    if place == "Aidonia":
        out = [b for b in out if b["kind"] not in {
            "market_stall", "laundry", "chimera", "shore", "siren", "net",
            "tidepool", "mill", "kite", "maze", "wheat",
        }]
    if place in {"Bloodbathed Battlefront", "Demigod Council", "Sanctum of Prophecy"}:
        out = [b for b in out if b["kind"] not in {
            "market_stall", "laundry", "chimera", "shore", "siren", "net",
            "tidepool", "mill", "kite",
        }]
    if place in {"The Nether", "Beyond Time"}:
        out = [b for b in out if b["kind"] in {
            "dawn", "thief_star", "wind",
        }]

    out = [b for b in out if b.get("kind") not in INDOOR_LAND]

    # Prefer signature texture over generic duplicates when capping the stage.
    _SIGNATURE = {
        "chimera", "market_stall", "forge", "banner", "shore", "siren",
        "grove_leaf", "olive", "cicada", "wheat", "maze", "mill", "kite",
        "mosaic", "fountain", "pillar", "laundry", "courier", "gate",
        "ribbon", "incense", "shrine", "boat", "net", "tidepool", "pearl",
        "dromas", "dromas_calf", "pebble", "well", "grass", "wind",
    }

    def _rank(b: dict) -> Tuple[int, int]:
        k = b.get("kind") or ""
        if b.get("caravan_id"):
            return (0, 0)
        if k == "dawn":
            return (1, 0)
        if k in _SIGNATURE:
            return (2, 0)
        if k == "resident":
            return (3, 0)
        return (4, 0)

    out.sort(key=_rank)

    # Keep a readable stage, not a census — but never truncate a trade caravan.
    preferred = []
    seen_kinds = set()
    caravan = [b for b in out if b.get("caravan_id")]
    rest = [b for b in out if not b.get("caravan_id")]
    for b in caravan + rest:
        k = b.get("kind")
        # Always keep first of each kind; extras only for chimera/dromas/residents
        if k in seen_kinds and k not in {
            "chimera", "dromas", "dromas_calf", "resident", "market_stall",
        }:
            continue
        seen_kinds.add(k)
        preferred.append(b)
    # Cap ambient density after the caravan is secured.
    if len(caravan) >= 4:
        head = preferred[: len(caravan)]
        tail = [b for b in preferred[len(caravan):] if not b.get("caravan_id")]
        return head + tail[: max(0, 20 - len(head))]
    return preferred[:20]


def logic_faults(scene: List[dict], place: str) -> List[str]:
    faults = []
    kinds = {b.get("kind") for b in scene}
    if place in GROVE and ("chimera" in kinds or "shore" in kinds or "siren" in kinds
                           or "boat" in kinds or "net" in kinds or "tidepool" in kinds):
        faults.append("Grove scene must not hold chimera or shore life")
    if place not in WORKING_SHORE and ("shore" in kinds or "siren" in kinds or "pearl" in kinds
                               or "tidepool" in kinds or "net" in kinds):
        faults.append("Shore life outside a working seashore")
    if "boat" in kinds and place not in WORKING_SHORE and place not in le.RIVER:
        faults.append("Boat outside river or sea")
    if place not in CHIMERA_CITIES and "chimera" in kinds:
        faults.append("Chimera outside holy-city family")
    if "forge" in kinds and place not in le.FORGE:
        faults.append("Forge outside Kremnos family")
    if "banner" in kinds and place not in le.FORGE:
        faults.append("Banner outside Kremnos family")
    if "mill" in kinds and place not in FIELDS:
        faults.append("Mill outside field places")
    if "market_stall" in kinds and place not in MARKET_CITIES:
        faults.append("Market stall outside market cities")
    if "dromas" in kinds and place not in DROMAS_ROADS:
        faults.append("Dromas outside road places")
    if place == "Vortex of Genesis" and (
        "siren" in kinds or "net" in kinds or "tidepool" in kinds
    ):
        faults.append("Vortex must not hold fishing-shore life")
    if place in TOMB_PLACES and ("olive" in kinds or "cicada" in kinds or "fountain" in kinds):
        faults.append("Tomb must not hold living-grove picnic life")
    indoor = kinds & INDOOR_LAND
    if indoor:
        faults.append("Indoor furniture on outdoor land: " + ", ".join(sorted(indoor)))
    for b in scene:
        if b.get("status") in {"dead", "starving", "plague"}:
            faults.append(f"Forbidden status on {b.get('id')}")
    return faults


def apply_tick(world, flags: Optional[dict] = None) -> Dict[str, Any]:
    """Refresh scene for the visitor's place; idempotent per clock key."""
    bucket = eco_bucket(world)
    try:
        from .lived_mechanisms import clock_key
        key = clock_key(world)
    except Exception:
        key = _date_seed(world)

    place, _ = _place_of(world, None)
    scene = derive_scene(world, place=place, include_residents=True)
    gaz = []
    for b in scene:
        if b.get("kind") == "resident":
            continue
        if b.get("status") in {"ailing", "restless", "uneasy", "vigorous", "full", "sowing", "reaping"}:
            gaz.append(f"{b['name'].capitalize()} — {b['doing']}.")
        elif b.get("kind") == "chimera" and b.get("status") == "wandering":
            gaz.append(f"Chimeras wander Okhema's stalls this hour.")
            break
    gaz = gaz[:4]

    idempotent = bucket.get("last_key") == key
    bucket["scene"] = scene
    bucket["gazette"] = gaz
    bucket["last_key"] = key
    if flags:
        bucket["flags_echo"] = {
            k: flags.get(k) for k in (
                "resting", "market_open", "device_withdrawn", "harvest_phase", "carrying"
            ) if k in flags
        }

    return {
        "place": place,
        "scene": scene,
        "gazette": gaz,
        "idempotent": idempotent,
        "faults": logic_faults(scene, place),
        "lines": [] if idempotent else list(gaz[:2]),
        "clock_key": key,
    }


def scene_for_heir(world, character_id: str) -> List[dict]:
    place, traveling = _place_of(world, character_id)
    if traveling:
        return derive_scene(world, place=place, character_id=character_id)
    return derive_scene(world, place=place, character_id=character_id)


def get_being(world, object_id: str,
              character_id: Optional[str] = None,
              place: Optional[str] = None) -> Optional[dict]:
    if place:
        pool = derive_scene(world, place=place, character_id=character_id,
                            include_residents=True)
    elif character_id:
        pool = scene_for_heir(world, character_id)
    else:
        pool = eco_bucket(world).get("scene") or derive_scene(world)
    for b in pool:
        if b.get("id") == object_id:
            return b
    # Fresh derive at visitor place as last resort
    for b in derive_scene(world):
        if b.get("id") == object_id:
            return b
    return None


def interact(world, object_id: str,
             character_id: Optional[str] = None,
             place: Optional[str] = None) -> dict:
    """Click / notice an ambient being — sound, line, identity. No mutation."""
    being = get_being(world, object_id, character_id=character_id, place=place)
    if not being:
        return {"ok": False, "reason": "That life is not in this scene this hour."}

    kind = being.get("kind")
    sound = being.get("sound")
    line = ""
    if being.get("place") and kind != "dawn":
        flavored = voice.flavor_notice(being.get("place") or "", kind, being)
        if flavored:
            return {
                "ok": True,
                "being": being,
                "sound": sound,
                "line": flavored,
                "textbox": sound or flavored,
                "care_hint": being.get("care_hint") or "",
            }
    if kind == "chimera":
        line = f'{being["name"].capitalize()} looks up and howls: “{sound}!”'
    elif kind == "resident":
        if being.get("caravan_id"):
            line = (
                f"{being['name']} walks with the trade caravan — "
                f"{_role_doing(being.get('role'), being.get('spot'))}."
            )
        else:
            line = (
                f"{being['name']} — {_role_doing(being.get('role'), being.get('spot'))}. "
            )
    elif kind == "dromas":
        if being.get("caravan_id"):
            line = (
                f"{being['name'].capitalize()} walks under harness; "
                "a trade caravan keeps its order."
            )
        else:
            line = f"{being['name'].capitalize()} stands in the road-scent of this hour."
    elif kind == "dromas_calf":
        if being.get("caravan_id"):
            line = (
                f"{being['name'].capitalize()} keeps pace with the train — "
                "small plates, full curiosity."
            )
        else:
            line = f"{being['name'].capitalize()} stays near the adult beasts."
    elif kind == "hearth_cat":
        line = f'The cat answers: “{sound}.”'
    elif kind == "shore":
        line = f"You hear {sound} along the quay."
    elif kind == "grove_leaf":
        line = f"Leaf answers leaf — {sound}."
    elif kind == "wheat":
        line = f"The wheat stands as it is: {being.get('doing')}."
    elif kind == "grass":
        line = f"Grass at your feet: {being.get('doing')}."
    elif kind == "wind":
        line = f"The air of this hour: {being.get('doing')}."
    elif kind == "dawn":
        line = f"The Dawn Device: {being.get('doing')}."
    elif kind == "thief_star":
        line = f"You look up. {being.get('doing').capitalize()}."
    elif kind == "lamp":
        line = f"A lamp: {being.get('doing')}."
    elif kind == "hearth":
        line = f"The hearth: {being.get('doing')}."
    elif kind == "bath":
        line = f"Water: {being.get('doing')}."
    elif kind == "well":
        line = f"The well: {being.get('doing')}."
    elif kind == "shrine":
        line = f"Stone and thanks: {being.get('doing')}."
    elif kind == "market_stall":
        line = f"{being['name'].capitalize()}: {being.get('doing')}."
        if being.get("status") == "open":
            line += " A vendor keeps the awning."
    elif kind == "forge":
        line = f"The forge answers: {sound}."
    elif kind == "loom":
        line = f"Thread: {being.get('doing')}."
    elif kind == "scroll":
        line = f"A page: {being.get('doing')}."
    elif kind == "gate":
        line = f"The threshold: {being.get('doing')}."
    elif kind == "siren":
        line = f"You hear {sound}."
    elif kind == "maze":
        line = f"The maze-edge: {being.get('doing')}."
    elif kind == "pebble":
        line = "A road-stone the size of a thumb lies where a wheel missed it."
    elif kind == "pearl":
        line = "A pale shore-pearl; the sea keeps giving them back."
    elif kind == "fountain":
        line = f"Water on stone: {being.get('doing')}."
    elif kind == "olive":
        line = f"Shade of leaf: {being.get('doing')}."
    elif kind == "cicada":
        line = f"You hear {sound}."
    elif kind == "laundry":
        line = f"Cloth on the air: {being.get('doing')}."
    elif kind == "boat":
        line = f"A hull: {being.get('doing')}."
    elif kind == "net":
        line = f"Mesh: {being.get('doing')}."
    elif kind == "ribbon":
        line = f"Thanks-cloth: {being.get('doing')}."
    elif kind == "mosaic":
        line = f"The floor: {being.get('doing')}."
    elif kind == "courier":
        line = f"An errand on the wing: {being.get('doing')}."
    elif kind == "banner":
        line = f"City cloth: {being.get('doing')}."
    elif kind == "incense":
        line = f"A thin sweetness: {being.get('doing')}."
    elif kind == "kite":
        line = f"Paper against sky: {being.get('doing')}."
    elif kind == "mill":
        line = f"Stone: {being.get('doing')}."
    elif kind == "tidepool":
        line = f"A shore's pocket: {being.get('doing')}."
    elif kind == "pillar":
        line = f"A public column: {being.get('doing')}."
    else:
        line = f"{being.get('name')}: {being.get('doing')}"

    return {
        "ok": True,
        "being": being,
        "sound": sound,
        "line": line,
        "textbox": sound or line,
        "care_hint": being.get("care_hint") or "",
    }


def authorized_actions(heir_id: str, being: dict) -> List[dict]:
    """Which gated care buttons apply for this Heir + being right now."""
    auth = CARE_AUTH.get(heir_id) or {}
    out = []
    kind = being.get("kind")
    status = being.get("status")
    for action_id, spec in auth.items():
        if kind not in (spec.get("kinds") or set()):
            continue
        if status not in (spec.get("from_status") or set()):
            continue
        out.append({
            "id": action_id,
            "label": action_id.replace("_", " "),
            "note": spec.get("note") or "",
            "mutates": spec.get("mutate", True) is not False
            and spec.get("to_status") is not None,
        })
    return out


def apply_care(world, heir_id: str, object_id: str, action_id: str,
               *, save: bool = True) -> dict:
    """Strictly gated mutation. Heirs cannot write arbitrary world fields.

    Rules:
    - Heir must be in CARE_AUTH for this action.
    - Target must be in the Heir's current scene.
    - Only status/doing on vivid.eco.beings[id] may change.
    - Forbidden statuses and keys are refused.
    - Audit trail always written.
    """
    heir_id = (heir_id or "").strip().lower()
    action_id = (action_id or "").strip()
    auth = (CARE_AUTH.get(heir_id) or {}).get(action_id)
    if not auth:
        return {
            "ok": False,
            "reason": "This Heir is not authorized for that care.",
        }

    # Heir must stand where the life is.
    place, traveling = _place_of(world, heir_id)
    if traveling:
        return {"ok": False, "reason": "On the road — tend life when you arrive."}

    being = get_being(world, object_id, character_id=heir_id)
    if not being:
        return {"ok": False, "reason": "That life is not here with this Heir this hour."}
    if being.get("place") != place:
        return {"ok": False, "reason": "That life is not in this Heir's place."}

    kind = being.get("kind")
    status = being.get("status")
    if kind not in (auth.get("kinds") or set()):
        return {"ok": False, "reason": "Wrong kind of life for this care."}
    if status not in (auth.get("from_status") or set()):
        return {"ok": False, "reason": "Nothing to tend — that life is not in need."}

    mutates = auth.get("mutate", True) is not False and auth.get("to_status") is not None
    to_status = auth.get("to_status")
    if mutates:
        if to_status in {"dead", "starving", "plague", "gone"}:
            return {"ok": False, "reason": "Forbidden care outcome."}
        note = auth.get("note") or "tended"
        today = _date_seed(world).rsplit("-p", 1)[0]
        _set_overlay(world, object_id, {
            "status": to_status,
            "doing": note,
            "tended_by": heir_id,
            "tended_date": today,
            "tended_at": _date_seed(world),
            "last_action": action_id,
        })

    audit = {
        "heir": heir_id,
        "object_id": object_id,
        "action": action_id,
        "from": status,
        "to": to_status if mutates else status,
        "place": place,
        "ts": _date_seed(world),
        "mutated": bool(mutates),
    }
    bucket = eco_bucket(world)
    log = list(bucket.get("audit") or [])
    log.append(audit)
    bucket["audit"] = log[-40:]

    # Refresh scene cache
    bucket["scene"] = derive_scene(world, place=place, character_id=heir_id)

    if save:
        try:
            world.save()
        except Exception:
            pass

    refreshed = get_being(world, object_id, character_id=heir_id) or being
    return {
        "ok": True,
        "mutated": bool(mutates),
        "being": refreshed,
        "note": auth.get("note") or "",
        "audit": audit,
        "world_fact": (
            f"{heir_id} used {action_id} on {being.get('name')} "
            f"({status} → {to_status if mutates else status})."
        ),
    }


def visitor_touch(world, object_id: str, action_id: str,
                  place: Optional[str] = None, *, save: bool = True) -> dict:
    """Visitor ambient acts — pocket a pearl, sit a hearth, wave. No Heir write."""
    action_id = _ACT_ALIASES.get(action_id, action_id)
    spec = VISITOR_ACT.get(action_id)
    if not spec:
        return {"ok": False, "reason": "That is not an allowed touch."}
    being = get_being(world, object_id, place=place)
    if not being:
        return {"ok": False, "reason": "That life is not in this scene this hour."}
    if being.get("kind") not in spec["kinds"]:
        return {"ok": False, "reason": "Wrong kind of thing for that touch."}

    bucket = eco_bucket(world)
    today = _date_seed(world).rsplit("-p", 1)[0]
    if action_id == "pick_keepsake":
        pocket = list(bucket.get("pocket") or [])
        if any(p.get("id") == object_id and p.get("date") == today for p in pocket):
            return {"ok": False, "reason": "You already carry that small thing today."}
        pocket.append({
            "id": object_id, "name": being.get("name"), "date": today,
        })
        bucket["pocket"] = pocket[-12:]
    notes = list(bucket.get("touches") or [])
    notes.append({
        "action": action_id, "object_id": object_id, "place": being.get("place"),
        "ts": _date_seed(world),
    })
    bucket["touches"] = notes[-40:]
    if save:
        try:
            world.save()
        except Exception:
            pass
    note = touch_note_for(being.get("place") or place, action_id, being.get("kind") or "")
    return {
        "ok": True,
        "note": note,
        "being": being,
        "line": note,
    }


def touch_note_for(place: Optional[str], action_id: str, kind: str) -> str:
    """Visitor act copy — regional lively sheets; calm default when none fit."""
    action_id = _ACT_ALIASES.get(action_id, action_id)
    spec = VISITOR_ACT.get(action_id) or {}
    note = (spec.get("notes") or {}).get(kind) or spec.get("note") or ""
    flavored = voice.flavor_touch(place or "", action_id, kind)
    if flavored:
        return flavored
    return note


def prompt_block(world, character_id: str, limit: int = 8) -> str:
    """Injector: what living presence the Heir can see and (if authorized) tend."""
    scene = scene_for_heir(world, character_id)
    if not scene:
        return ""
    bits = []
    for b in scene[:limit]:
        if b.get("kind") == "resident":
            bits.append(
                f"- {b.get('name')} — {_role_doing(b.get('role'), b.get('spot'))}."
            )
        else:
            bits.append(
                f"- {b.get('name')} [{b.get('status')}]: {b.get('doing')}."
            )
    auth_lines = []
    for b in scene:
        for a in authorized_actions(character_id, b):
            if a.get("mutates"):
                auth_lines.append(
                    f"You may tend {b.get('name')} ({a['id']}) if the visitor asks — "
                    f"only that care, nothing else."
                )
    body = (
        "# Living presence in your scene (ecosystem)\n"
        "These lives are on the stage with you this hour. Notice them; "
        "do not inventory the whole world. If the visitor points at one, "
        "answer about *that* one. You cannot change the clock, other Heirs, "
        "or invent famine or death.\n"
        + "\n".join(bits)
    )
    if auth_lines:
        body += "\n# Care you are authorized to give\n" + "\n".join(auth_lines[:3])
    return body


def gazette_items(world, limit: int = 3) -> List[str]:
    gaz = list((eco_bucket(world).get("gazette") or []))
    if not gaz:
        apply_tick(world)
        gaz = list((eco_bucket(world).get("gazette") or []))
    return gaz[:limit]
