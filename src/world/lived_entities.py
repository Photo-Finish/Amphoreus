"""Lived world entities — coarse, positive, Amphoreus-native.

The visitor asked for physical things that shape a day, not inner parts
(skin, axle). Status is *derived* from the Light Calendar, the Keeper's
sky, and where the body stands — never a second random weather roll.

Excluded on purpose: famine, plague, war, storm-as-catastrophe.
The black tide remains the existing vivid-stage pressure, not a new entity.

Sanctuary rule: people here live on unless a system *desperately* needs
someone not to. No lived-entity may stage burial, dying, or a grave as
today's work. Canon places (Aidonia, the Nether) may exist as geography;
they are not a death mechanic.

Never authors an Heir's spoken line. Never opens the knowledge wall.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Place families (canon geography — see map_data.py)
# --------------------------------------------------------------------------- #
SEA = {
    "Styxia", "Aedes Elysiae", "Vortex of Genesis",
    "Warbling Shores", "Aedes Elysiae, of old",
}
RIVER = {"Styxia", "Aidonia", "Janusopolis", "Sanctum of Prophecy", "Warbling Shores"}
GROVE = {"Grove of Epiphany", "Radiant Scarwood", "Great Tomb", "Universal Matrix"}
MOUNTAIN = {
    "Okhema", "Dawncloud", "Eternal Holy City", "Demigod Council",
    "Eye of Twilight", "Fortress of Dome",
}
FORGE = {"Castrum Kremnos", "Bloodbathed Battlefront"}
FIELDS = {"Aedes Elysiae", "Aedes Elysiae, of old"}
GATES = {"Janusopolis", "Okhema", "Sanctum of Prophecy", "Eternal Holy City"}
HEALER = {"Grove of Epiphany", "Okhema", "Dawncloud", "Radiant Scarwood"}
SHRINE = {"Okhema", "Janusopolis", "Dawncloud", "Eternal Holy City", "Demigod Council"}
WORKSHOP = {"Okhema", "Castrum Kremnos", "Eternal Holy City", "Bloodbathed Battlefront"}
SCROLL = {"Grove of Epiphany", "Okhema", "Radiant Scarwood", "Eternal Holy City"}
TEACHING = {"Grove of Epiphany", "Radiant Scarwood"}
CITYISH = {
    "Okhema", "Dawncloud", "Janusopolis", "Castrum Kremnos", "Styxia",
    "Aidonia", "Grove of Epiphany", "Aedes Elysiae", "Eye of Twilight",
    "Eternal Holy City", "Demigod Council", "Sanctum of Prophecy",
    "Radiant Scarwood", "Bloodbathed Battlefront", "Warbling Shores",
    "Fortress of Dome",
}

# Coarse catalog: id, display name, how it acts on a day, where it is *local*.
# presence "always" = felt everywhere (sky, hours, Dawn Device).
CATALOG: List[Dict[str, Any]] = [
    {
        "id": "dawn_device",
        "name": "Dawn Device",
        "mechanism": "Lights and warms the waking world; people and crops keep time by it.",
        "presence": "always",
    },
    {
        "id": "thief_star",
        "name": "Thief Star",
        "mechanism": "Marks the night road; travelers watch it when the Device withdraws.",
        "presence": "night",
    },
    {
        "id": "sky",
        "name": "Today's sky",
        "mechanism": "The Keeper's weather — what the body feels outdoors this day.",
        "presence": "always",
    },
    {
        "id": "wind",
        "name": "Wind",
        "mechanism": "Cools labor, dries cloth, fills a sail, and can delay a road.",
        "presence": "always",
    },
    {
        "id": "earth",
        "name": "Earth",
        "mechanism": "Holds the seed; Georios' gift underfoot.",
        "presence": "always",
    },
    {
        "id": "river_of_souls",
        "name": "River of Souls",
        "mechanism": "The pale river of Styxia; boats, hush, and a long current.",
        "places": RIVER,
    },
    {
        "id": "sea",
        "name": "Sea",
        "mechanism": "Fish, trade, and the Ocean's breath at the shore.",
        "places": SEA,
    },
    {
        "id": "grove",
        "name": "Grove",
        "mechanism": "Shade, timber, and scholarship among the trees.",
        "places": GROVE,
    },
    {
        "id": "mountain",
        "name": "Kephale's mountain",
        "mechanism": "The holy city's wall of stone and stillness above Okhema.",
        "places": MOUNTAIN,
    },
    {
        "id": "hearth",
        "name": "Hearth",
        "mechanism": "Cooks, warms, and gathers a household.",
        "presence": "settlement",
    },
    {
        "id": "harvest",
        "name": "Harvest",
        "mechanism": "Fills the granaries; the year is planned around it.",
        "presence": "always",
    },
    {
        "id": "dromas",
        "name": "Dromases",
        "mechanism": "Beasts of the road; Georios' vigor on the long haul.",
        "presence": "always",
    },
    {
        "id": "water",
        "name": "City water",
        "mechanism": "Baths, wells, and the day's drink.",
        "presence": "settlement",
    },
    {
        "id": "dwelling",
        "name": "House",
        "mechanism": "Keeps weather and night off the body.",
        "presence": "settlement",
    },
    {
        "id": "city",
        "name": "The city",
        "mechanism": "Work, rumor, and many hearths in one place.",
        "places": CITYISH,
    },
    {
        "id": "cloth",
        "name": "Cloth",
        "mechanism": "Warmth and work; Mnestia's memory in thread.",
        "presence": "settlement",
    },
    {
        "id": "road",
        "name": "Road",
        "mechanism": "Connects cities; feet and wheels wear it.",
        "presence": "always",
    },
    {
        "id": "gates",
        "name": "Gates",
        "mechanism": "Janus's thresholds — a city opens or closes.",
        "places": GATES,
    },
    {
        "id": "harbor",
        "name": "Harbor",
        "mechanism": "Ships meet land; goods and news come ashore.",
        "places": SEA,
    },
    {
        "id": "fields",
        "name": "Fields",
        "mechanism": "Sowing and reaping under Georios.",
        "places": FIELDS,
    },
    {
        "id": "workshop",
        "name": "Workshop",
        "mechanism": "Turns material into tools, cloth, pots.",
        "places": WORKSHOP,
    },
    {
        "id": "market",
        "name": "Market",
        "mechanism": "Strangers trade without knowing each other.",
        "presence": "settlement",
    },
    {
        "id": "coin",
        "name": "Coin",
        "mechanism": "Stands in for goods so trade can travel.",
        "presence": "settlement",
    },
    {
        "id": "ship",
        "name": "Ship",
        "mechanism": "Carries people and cargo farther than a road.",
        "places": SEA,
    },
    {
        "id": "forge",
        "name": "Forge",
        "mechanism": "Iron from the earth into useful metal.",
        "places": FORGE,
    },
    {
        "id": "scroll",
        "name": "Scroll",
        "mechanism": "Speech that outlives the speaker.",
        "places": SCROLL,
    },
    {
        "id": "letter",
        "name": "Letter",
        "mechanism": "A voice across distance; the roads carry it.",
        "presence": "always",
    },
    {
        "id": "hours",
        "name": "Light Calendar hours",
        "mechanism": "Many people keep the same time.",
        "presence": "always",
    },
    {
        "id": "teaching",
        "name": "Teaching hall",
        "mechanism": "Hands a craft or a canon to the next generation.",
        "places": TEACHING,
    },
    {
        "id": "healer",
        "name": "Healer's house",
        "mechanism": "Tends hurt, fever, and weariness — comfort in a life that goes on.",
        "places": HEALER,
    },
    {
        "id": "shrine",
        "name": "Shrine",
        "mechanism": "Offerings and thanks in stone.",
        "places": SHRINE,
    },
]


def _period_idx(world) -> int:
    try:
        return int(getattr(world.clock, "period", 0) or 0)
    except Exception:
        return 0


def _month(world) -> int:
    try:
        return int(getattr(world.clock, "month", 9) or 9)
    except Exception:
        return 9


def _period_name(world) -> str:
    try:
        return str(world.clock.period_name)
    except Exception:
        return "Entry Hour"


def _is_night(world) -> bool:
    """Curtain-Fall is night. Month of Evernight also stretches darkness."""
    p = _period_idx(world)
    if p >= 4:
        return True
    if _month(world) == 3 and p in (0, 3, 4):
        return True
    return False


def _weather_at(world, place: str) -> str:
    try:
        return (world.ambient_weather(place) or "").strip()
    except Exception:
        return ""


def _sky_tags(weather: str) -> set[str]:
    w = (weather or "").lower()
    tags = set()
    if any(k in w for k in ("veil", "dim", "grey", "gray", "curtain", "weak", "evernight")):
        tags.add("veiled")
    if any(k in w for k in ("blaz", "scorch", "strongest", "hottest")):
        tags.add("blazing")
    if any(k in w for k in ("bright", "clear", "golden")):
        tags.add("bright")
    if any(k in w for k in ("rain", "shower")):
        tags.add("rain")
    if any(k in w for k in ("wind", "breeze", "edge to it", "restless")):
        tags.add("windy")
    if any(k in w for k in ("still", "hush", "quiet", "somber")):
        tags.add("still")
    if any(k in w for k in ("storm", "unpredictable", "whim")):
        tags.add("wild")
    return tags


def _surged_here(world, place: str) -> bool:
    try:
        from src.world import world_events as wev
        if not wev.surge_active(world):
            return False
        cities = world.surge.get("cities") or []
        return place in cities
    except Exception:
        return False


def _traveling(world, character_id: Optional[str]) -> bool:
    if character_id:
        try:
            return bool(world.travel_info(character_id))
        except Exception:
            return False
    try:
        return world.visitor_place().get("kind") == "traveling"
    except Exception:
        return False


def resolve_place(world, character_id: Optional[str] = None) -> str:
    """Where the body stands: an Heir, or the visitor."""
    if character_id:
        try:
            info = world.travel_info(character_id)
            if info:
                return str(info.get("from") or world.location_name(character_id) or "Okhema")
        except Exception:
            pass
        try:
            return world.location_name(character_id) or "Okhema"
        except Exception:
            return "Okhema"
    try:
        vp = world.visitor_place()
        if vp.get("kind") == "traveling":
            return str(vp.get("from") or vp.get("to") or "Okhema")
        return str(vp.get("at") or "Okhema")
    except Exception:
        return "Okhema"


def _local(spec: dict, place: str, traveling: bool) -> str:
    """here | near | distant."""
    eid = spec["id"]
    if traveling and eid not in {
        "dawn_device", "thief_star", "sky", "wind", "earth",
        "hours", "road", "dromas", "letter", "harvest",
    }:
        return "distant"
    presence = spec.get("presence")
    places = spec.get("places")
    if presence == "always":
        if eid in ("sky", "hours", "dawn_device", "earth", "wind", "road"):
            return "here"
        return "near"
    if presence == "night":
        return "here"
    if presence == "settlement":
        return "here" if place in CITYISH else "distant"
    if places:
        return "here" if place in places else "distant"
    return "near"


def _status_for(spec: dict, world, place: str, traveling: bool,
                weather: str, surged: bool) -> str:
    eid = spec["id"]
    p = _period_idx(world)
    month = _month(world)
    night = _is_night(world)
    tags = _sky_tags(weather)
    pname = _period_name(world)

    if eid == "dawn_device":
        if night:
            if "blazing" in tags or "bright" in tags:
                return ("Today's light was strong; this hour the Device has "
                        "withdrawn and night holds the streets.")
            if "veiled" in tags or month == 3:
                return "The Device sleeps behind Oronyx's veil; the night is long."
            return "The Dawn Device has withdrawn; lamps and the Thief Star take the watch."
        if "veiled" in tags or month == 3:
            return "The Device burns behind a veil — day, but a dim one."
        if "rain" in tags:
            return "Georios' rain beads on the light; the Device still keeps the hour."
        if "blazing" in tags or month == 6:
            return "The Device stands high and hot; work is done in its glare."
        if p == 0:
            return "The Device kindles Entry Hour — doors and prayers open with it."
        if p == 3:
            return "The light slants toward Parting Hour; the Device leans west."
        return "The Device holds the day's ordinary light."

    if eid == "thief_star":
        if night:
            return "The Thief Star is out; the night road has a mark to steer by."
        if month == 3:
            return "Oronyx's month: the star's darkness leaks even into the waking hours."
        return "The Thief Star waits below the day; it will return at Curtain-Fall."

    if eid == "sky":
        if weather:
            if night:
                return f"Today's sky was set as: {weather} This hour it is night under that day."
            return weather
        return "The sky keeps its own counsel."

    if eid == "wind":
        if "windy" in tags or "wild" in tags:
            return "The wind has an edge; cloth snaps and the road may slow."
        if "still" in tags:
            return "The air is still; banners hang."
        if month == 10:
            return "A restless Calamity wind — enough to cool a forge-walk, not a storm-entity."
        return "A mild air moves; enough to dry a sleeve."

    if eid == "earth":
        if month == 4:
            return "The earth smells of turned soil — Cultivation's hands are in it."
        if month == 8:
            return "Harvest dust lies on the earth; the fields have given."
        return "The ground is there to stand on — Georios' quiet gift."

    if eid == "harvest":
        if month == 4:
            return "Sowing, not reaping — the harvest is still a promise in the seed."
        if month in (5, 6):
            return "Crops drink the light; brewing and swelling, not yet the full reaping."
        if month == 8:
            return "The harvest comes in; granaries fill."
        if month == 9:
            return "Granaries hold what was reaped; this month remembers grain more than it cuts it."
        return "The fields rest from this month's main work; no famine — only the calendar's turn."

    if eid == "dromas":
        if traveling:
            return "Dromases share the road with you — the long haul is theirs."
        if month == 4:
            return "Georios' beasts are doubly vigorous; the roads are full of them."
        if p in (2, 3):
            return "Dromases move goods between cities this hour."
        return "Dromases rest in their yards, or pace a quiet street."

    if eid == "hearth":
        if traveling:
            return "The hearth you left is behind you; a camp-fire is all the road offers."
        if night:
            return "Hearths hold the houses; the day's last meal and warmth."
        return "Hearths are lit for work and food."

    if eid == "water":
        if traveling:
            return "Road water is what you carry; the city's baths wait at the next gate."
        if place in {"Okhema", "Eternal Holy City"}:
            return "The Marmoreal baths and the city's wells — drink and wash."
        return "Wells and cisterns of this place; the day's drink."

    if eid == "dwelling":
        if traveling:
            return "You are on the road — the house is the city you left or the one ahead."
        return "Walls and a roof keep this hour's weather off you."

    if eid == "city":
        if traveling:
            return "The city is ahead or behind; the road is what you have."
        if surged:
            return f"{place} keeps close — trade and talk are thinner at the tide's edge."
        if night:
            return f"{place} quiets toward sleep."
        return f"{place} is awake around you."

    if eid == "cloth":
        if month == 9:
            return "Looms and tongues both carry memory — Weaving's month."
        return "Cloth on the body: warmth, work, and whatever the city wove."

    if eid == "road":
        if traveling:
            return "The road is underfoot; the next city is still a measure of days."
        if p == 3:
            return "Parting Hour — wheels find the gates."
        return "The road waits at the gate, worn by those who already left."

    if eid == "market":
        if traveling:
            return "The market is in the city, not on this stretch of road."
        if night:
            return "Stalls are down; the square belongs to lamps and stray cats."
        if surged:
            return "A thinner market — people buy what they need and keep close."
        if p == 3:
            return "Stalls are packing; Parting Hour thins the square."
        if p == 0:
            return "Entry Hour: the market opens with prayers and first custom."
        if p == 2:
            return "Action Hour: the square is busiest."
        return "The market trades at an ordinary pace."

    if eid == "coin":
        if night or traveling:
            return "Coin sleeps in purses; trade will wait for a waking square."
        if month == 2:
            return "Month of Balance — accounts are weighed with the coin."
        if month == 12:
            return "Month of Fortune — coin changes hands faster than usual."
        return "Coin stands in for goods in the square."

    if eid == "hours":
        return f"It is {pname} — the Light Calendar hour everyone here keeps."

    if eid == "letter":
        unread = 0
        try:
            from src.world import living_world as lw
            unread = int(lw.unread_count(world, "visitor") or 0)
        except Exception:
            pass
        if unread:
            return f"The roads carry letters; {unread} wait in your mailbox."
        return "The roads carry letters; none wait unread for you just now."

    if eid == "river_of_souls":
        return "The River of Souls runs here — pale water, boats, and a long hush."
    if eid == "sea":
        if month == 5:
            return "Fishermen return fuller in the Month of Joy; the sea feeds the table."
        return "The sea is at the shore — trade and fish, not a storm-entity."
    if eid == "grove":
        if p in (1,):
            return "Lucid Hour in the Grove: pages, leaves, and quiet study."
        return "The Grove stands in leaf and timber around you."
    if eid == "mountain":
        return "Kephale's mountain hangs above — stone, stillness, the holy city's wall."
    if eid == "gates":
        if p == 3:
            return "The gates take farewells this hour."
        if p == 0:
            return "The gates take the morning's first steps."
        return "The gates stand; Janus's threshold is a day's ordinary door."
    if eid == "harbor":
        if night:
            return "The harbor lamps; ships hold to the quay."
        return "Ships meet land here; goods and news come ashore."
    if eid == "fields":
        if month == 4:
            return "Hands in the soil — Cultivation."
        if month == 8:
            return "The fields are stripped toward gold — Reaping."
        return "The coastal fields lie under this month's slower work."
    if eid == "workshop":
        if night:
            return "The workshop is banked for the night."
        return "Hammers and benches — material becoming tools."
    if eid == "ship":
        if night:
            return "Hulls at rest in the harbor."
        return "A ship can leave from here farther than any road."
    if eid == "forge":
        if night:
            return "The forge is banked; iron will wait for Action Hour."
        if month == 10:
            return "Kremnos' forges ring — iron for walls and tools in Strife's month."
        return "The forge turns ore into useful metal."
    if eid == "scroll":
        if p == 1:
            return "Lucid Hour — the best hour for a scroll."
        return "Scrolls sleep on their shelves, or open in someone's hands."
    if eid == "teaching":
        if p in (1, 2):
            return "The teaching hall is at work."
        if night:
            return "The teaching hall is dark; lessons resume with Lucid Hour."
        return "The Grove's teaching waits between hours."
    if eid == "healer":
        return "The healer's house is open — rest, balm, and a body that will see another hour."
    if eid == "shrine":
        if p == 0:
            return "Entry Hour prayers at the shrine."
        return "The shrine holds offerings from those who already passed."

    return "Present in the world."


def snapshot(world, place: Optional[str] = None,
             character_id: Optional[str] = None) -> Dict[str, Any]:
    """Full ledger: ambient + every catalog entity with status and presence."""
    traveling = _traveling(world, character_id)
    if not place:
        place = resolve_place(world, character_id)
    weather = _weather_at(world, place)
    surged = _surged_here(world, place)
    night = _is_night(world)
    rows = []
    for spec in CATALOG:
        if spec.get("presence") == "night" and not night and _month(world) != 3:
            loc = "distant"
        else:
            loc = _local(spec, place, traveling)
        row = {
            "id": spec["id"],
            "name": spec["name"],
            "mechanism": spec["mechanism"],
            "presence": loc,
            "status": _status_for(spec, world, place, traveling, weather, surged),
        }
        rows.append(row)
    news = ""
    try:
        news = world.ambient_news() or ""
    except Exception:
        pass
    weather_map = {}
    try:
        weather_map = dict((world.ambient or {}).get("weather") or {})
    except Exception:
        pass
    errands = {}
    try:
        errands = dict((world.ambient or {}).get("errands") or {})
    except Exception:
        pass
    clock = ""
    try:
        clock = world.clock.format()
    except Exception:
        pass
    return {
        "place": place,
        "traveling": traveling,
        "clock": clock,
        "period": _period_name(world),
        "month": _month(world),
        "night": night,
        "surged": surged,
        "weather_here": weather,
        "weather": weather_map,
        "errands": errands,
        "news": news,
        "entities": rows,
    }


def here_entities(snap: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
    """Entities the body can actually meet this hour (for Visit / chat)."""
    always_ids = {"dawn_device", "sky", "hours", "wind", "earth"}
    here = [r for r in snap.get("entities") or [] if r.get("presence") == "here"]
    near = [r for r in snap.get("entities") or [] if r.get("presence") == "near"]
    here_always = [r for r in here if r["id"] in always_ids]
    here_local = [r for r in here if r["id"] not in always_ids]
    ordered = here_always[:4] + here_local + near
    out: List[Dict[str, Any]] = []
    seen = set()
    for row in ordered:
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        out.append(row)
        if len(out) >= limit:
            break
    return out


def prompt_lines(snap: Dict[str, Any], limit: int = 6) -> str:
    rows = here_entities(snap, limit=limit)
    if not rows:
        return ""
    bits = []
    for r in rows:
        bits.append(f"{r['name']}: {r['status']}")
    return (
        "# Lived world (what is physically here this hour)\n"
        + " ".join(bits)
        + " Treat these as the stage you stand on. Do not invent famine, plague, "
        "a death this hour does not need, or a second weather. Do not place the "
        "sea in a grove or a busy market at Curtain-Fall if the status says otherwise."
    )


def logic_faults(snap: Dict[str, Any]) -> List[str]:
    """Catch contradictions the visitor could feel. Empty = consistent."""
    faults: List[str] = []
    by_id = {r["id"]: r for r in snap.get("entities") or []}
    night = bool(snap.get("night"))
    period = str(snap.get("period") or "")
    month = int(snap.get("month") or 0)
    place = str(snap.get("place") or "")
    traveling = bool(snap.get("traveling"))
    weather = str(snap.get("weather_here") or "").lower()
    surged = bool(snap.get("surged"))

    dawn = (by_id.get("dawn_device") or {}).get("status") or ""
    star = (by_id.get("thief_star") or {}).get("status") or ""
    market = (by_id.get("market") or {}).get("status") or ""
    harvest = (by_id.get("harvest") or {}).get("status") or ""
    dwelling = (by_id.get("dwelling") or {}).get("status") or ""
    sea = by_id.get("sea") or {}
    forge = by_id.get("forge") or {}
    sky = (by_id.get("sky") or {}).get("status") or ""

    if night and any(k in dawn.lower() for k in ("stands high and hot", "kindles entry")):
        faults.append("Dawn Device still blazing after nightfall")
    if (not night) and month != 3 and "is out" in star.lower() and "Curtain-Fall" not in period:
        if "waits below" not in star.lower():
            faults.append("Thief Star overhead in ordinary daylight")
    if period == "Curtain-Fall Hour" and any(k in market.lower() for k in ("busiest", "opens with")):
        faults.append("Market open at Curtain-Fall")
    if month == 4 and "comes in" in harvest.lower() and "sowing" not in harvest.lower():
        faults.append("Reaping during Cultivation")
    if month in (1, 2, 3, 7, 10, 11, 12) and "comes in" in harvest.lower():
        faults.append("Harvest coming in outside Reaping")
    if traveling and "keep this hour's weather off you" in dwelling.lower():
        faults.append("Inside a house while on the road")
    if sea.get("presence") == "here" and place in GROVE:
        faults.append("Sea at the Grove")
    if forge.get("presence") == "here" and place in {"Aidonia", "The Nether"}:
        faults.append("Forge at Aidonia / the Nether")
    if surged and "busiest" in market.lower():
        faults.append("Feast-busy market under a tide surge")
    if "veil" in weather and "stands high and hot" in dawn.lower() and not night:
        faults.append("Blazing Device under a veiled sky")
    if sky and weather and night is False:
        # Daily sky should echo the Keeper line when we are in daylight.
        if weather and weather not in sky.lower() and "today's sky was set" not in sky.lower():
            # sky status may be the weather string itself
            if sky.lower() != weather and weather not in sky.lower():
                if not (sky.startswith("The sky keeps")):
                    faults.append("Sky status drifted from Keeper weather")
    return faults


def errand_text(raw: Any) -> str:
    if isinstance(raw, dict):
        ask = (raw.get("ask") or "").strip()
        cause = (raw.get("cause") or "").strip()
        if ask and cause:
            return f"{ask} — cause: {cause}"
        return ask or cause
    return str(raw or "").strip()
