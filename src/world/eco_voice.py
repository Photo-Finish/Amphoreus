"""Place-voice for ecosystem land — funny, vibrant, sanctuary-safe.

Okhema is the positive standard. Other regions keep their own color while
matching that energy. Dawn Device copy is never flavored here.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple


def voice_key(place: str) -> str:
    p = place or ""
    if p in {"Okhema", "Eternal Holy City"}:
        return "okhema"
    if p in {"Dawncloud", "Demigod Council"}:
        return "dawncloud"
    if p in {"Janusopolis", "Sanctum of Prophecy"}:
        return "janus"
    if p in {"Castrum Kremnos", "Bloodbathed Battlefront"}:
        return "kremnos"
    if p in {"Grove of Epiphany", "Radiant Scarwood"}:
        return "grove"
    if p in {"Styxia", "Warbling Shores"}:
        return "styxia"
    if p == "Aidonia":
        return "aidonia"
    if p in {"Aedes Elysiae", "Aedes Elysiae, of old"}:
        return "aedes"
    if p == "Vortex of Genesis":
        return "vortex"
    if p in {"Great Tomb", "Universal Matrix"}:
        return "tomb"
    if p in {"Eye of Twilight", "Fortress of Dome"}:
        return "sky"
    if p == "The Nether":
        return "nether"
    if p == "Beyond Time":
        return "beyond"
    return "default"


# --- stall packs: (names, doing, notices) ---
_STALLS: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]] = {
    "okhema": (
        (
            "a fruit stall with main-character grapes",
            "a cloth stall of dangerous taste",
            "a sweet stall of moral hazard",
            "a pottery stall of well-behaved jars",
        ),
        (
            "purple grapes posing harder than the Heirs",
            "selling dye that will absolutely start an argument",
            "honey cakes weaponized for friendship",
            "bowls waiting to become someone's favorite mistake",
        ),
        (
            "Gold awning, loud fruit, vendor smiling like the grapes pay rent.",
            "Fabrics flutter like they have side quests. Blue-and-gold is winning today.",
            "Sugar in small packages. Resistance is optional and discouraged.",
            "Clay that survived the kiln and now wants a kitchen drama.",
        ),
    ),
    "dawncloud": (
        (
            "a fruit stall with council-approved peaches",
            "a cloth stall of sky-dye opinions",
        ),
        (
            "peaches lobbying harder than senators",
            "cloth that votes blue no matter who asks",
        ),
        (
            "Fruit under a bright awning — democracy, but juicier.",
            "Sky-cloth for sale; the vendor has already cast three ballots today.",
        ),
    ),
    "janus": (
        (
            "a threshold charm stall",
            "a twin-ribbon booth",
        ),
        (
            "selling luck for both sides of a door",
            "ribbons that refuse to pick a favorite tomorrow",
        ),
        (
            "Charms for hello and goodbye in the same breath. Very Janus.",
            "Twin ribbons argue politely about which way is forward.",
        ),
    ),
    "kremnos": (
        (
            "a ration stall of honest bread",
            "a spear-polish booth",
        ),
        (
            "bread that survived a long march and still tastes like home",
            "oil and cloth for spears that are currently off-duty",
        ),
        (
            "Rations with dignity. No one here is starving for drama.",
            "Polish only — the spear is resting, not recruiting.",
        ),
    ),
    "styxia": (
        (
            "a pearl-and-shell stall",
            "a pale-sweet booth",
        ),
        (
            "shells that remember tides better than gossip",
            "sweets soft enough for a quiet shore",
        ),
        (
            "Pearls and shells under a soft awning. The river approves.",
            "Pale sweets; the vendor whispers prices like lullabies.",
        ),
    ),
    "aedes": (
        (
            "a village fruit crate",
            "a honey-and-wheat stall",
        ),
        (
            "fruit that grew up with the same kids who left and came home",
            "honey cakes practicing being legendary",
        ),
        (
            "Village fruit — no gold awning required, just sun.",
            "Honey and wheat: childhood's favorite side quest.",
        ),
    ),
}


_NAMES: Dict[str, Dict[str, str]] = {
    "okhema": {
        "grass": "the gossiping grass",
        "wind": "Okhema's restless air",
        "well": "the gossip well",
        "shrine": "a shrine of thanks (not a guilt booth)",
        "incense": "a stick of household sweetness",
        "gate": "Janus's ordinary door (with main-quest lighting)",
        "pebble": "a thumb-sized road celebrity",
        "mosaic": "a floor that remembers everyone's footsteps",
        "fountain": "the square's chatty water",
        "pillar": "a column practicing good posture",
        "laundry": "wash on the line, living its best life",
        "courier": "an errand-bird on a deadline",
    },
    "dawncloud": {
        "grass": "balcony grass with voting rights",
        "wind": "a sky-council draft",
        "well": "a cistern of clear arguments",
        "shrine": "a shrine that keeps minutes",
        "incense": "incense for calm debate",
        "pebble": "a pebble that attended every meeting",
        "mosaic": "a floor of polite majorities",
        "fountain": "a fountain practicing eloquence",
        "pillar": "a column holding up the agenda",
        "laundry": "council robes airing their opinions",
        "courier": "a bird carrying tomorrow's motion",
        "chimera": "a little chimera with a seat at the table",
    },
    "janus": {
        "grass": "threshold grass (both sides)",
        "wind": "a hinge-wind of hello-goodbye",
        "well": "a well that serves arrivals and farewells",
        "shrine": "a shrine of open doors",
        "incense": "incense that smells like crossroads",
        "gate": "a thousand-gated ordinary door",
        "pebble": "a pebble that has crossed more doors than you",
        "fountain": "water choosing both directions",
        "ribbon": "a ribbon of twin thanks",
        "boat": "a river-boat of thresholds",
        "courier": "a bird that never uses the same gate twice",
        "dromas": "a road-beast of the twin city",
    },
    "kremnos": {
        "grass": "parade-ground grass off duty",
        "wind": "a dry wind with spear-polish manners",
        "well": "a well that hydrates legends between chapters",
        "forge": "an anvil with opinions",
        "banner": "a city banner resting its colors",
        "pebble": "a stone that once practiced marching",
        "pillar": "a spear-monument practicing stillness",
        "courier": "a bird that delivers like a challenge accepted",
        "dromas": "a war-road dromas currently on errands of peace",
        "dromas_calf": "a calf learning the road without the roar",
    },
    "grove": {
        "grove_leaf": "Cerces' leaf with footnotes",
        "olive": "an olive arguing softly with shade",
        "cicada": "the grove's brass section",
        "fountain": "a scholar's fountain (quiet, judgmental)",
        "grass": "grass that has read the syllabus",
        "wind": "a page-turning breeze",
        "pebble": "a pebble used as a paperweight of destiny",
        "dromas": "a patient dromas waiting out a lecture",
        "dromas_calf": "a calf auditing Intro to Roads",
    },
    "styxia": {
        "shore": "the pearly shore's living breath",
        "siren": "a shore-song keeping soft time",
        "pearl": "a pearl the river keeps giving back",
        "boat": "a pale hull at hush",
        "net": "a net drying like a quiet poem",
        "tidepool": "a pocket of tide practicing mirrors",
        "grass": "shore-grass whispering tide gossip",
        "wind": "a river-breeze with good manners",
        "well": "a well of pale cool water",
        "fountain": "water remembering names gently",
        "incense": "incense for the remembered, not the buried",
        "pebble": "a shore-stone the size of a kept promise",
        "courier": "a bird that knows the river's shortcuts",
        "dromas": "a dromas that does not hurry the dead or the living",
    },
    "aidonia": {
        "grass": "snow-edge grass keeping vigil",
        "wind": "a northern hush with opinions",
        "well": "a cistern under white quiet",
        "ribbon": "a ribbon of soft farewell",
        "boat": "a pale boat on the long current",
        "pebble": "a snow-stone monument in miniature",
        "pillar": "a monument practicing patience",
        "incense": "cold-sweet incense of Thanatos's thanks",
        "dromas": "a road-beast wearing frost like dignity",
    },
    "aedes": {
        "wheat": "wheat that still knows childhood names",
        "maze": "a village maze with friendly wrong turns",
        "mill": "a mill humming old songs",
        "kite": "a kite practicing freedom above home",
        "cicada": "summer brass over the fields",
        "grass": "home-grass under returning feet",
        "wind": "a sea-breeze that smells like coming back",
        "well": "the village well (everybody's business)",
        "shore": "the village shore at ease",
        "siren": "a soft shore-song for sailors who left",
        "pearl": "a pearl like a kept postcard",
        "boat": "a working hull tied like a promise",
        "net": "nets drying into tomorrow's dinner",
        "tidepool": "a child's tide-pocket",
        "pebble": "a road-stone that watched kids grow up",
        "dromas": "a village dromas with excellent gossip range",
    },
    "vortex": {
        "wind": "star-ripple air",
        "pillar": "a pillar of quiet genesis",
        "pebble": "a stone that remembers Coreflame light",
    },
    "tomb": {
        "grove_leaf": "a leaf that wandered into the matrix",
        "pillar": "a pillar of ordered ruin",
        "wind": "air circulating like thought",
        "pebble": "a data-stone (metaphorically; still a pebble)",
    },
    "sky": {
        "wind": "Aquila's leftover draft",
        "pillar": "a sky-column practicing altitude",
        "kite": "a kite that thinks it is a small sun",
        "grass": "terrace grass above the world",
        "pebble": "a stone that fell up somehow",
    },
    "nether": {
        "wind": "a breeze among pale blossoms",
    },
    "beyond": {
        "wind": "a page-edge breeze outside the hour",
        "dawn": "the Device",  # unused — dawn never flavored
    },
}


def _chimera_name(key: str, idx: int) -> Optional[str]:
    if key == "okhema":
        return "another little chaos-cloud" if idx > 1 else "a little chimera"
    if key == "dawncloud":
        return (
            "another little council-chimera" if idx > 1
            else "a little chimera with a seat at the table"
        )
    return None


def _dromas_name(key: str, idx: int, kind: str) -> Optional[str]:
    if kind == "dromas_calf":
        return _NAMES.get(key, {}).get("dromas_calf")
    if kind != "dromas":
        return None
    base = _NAMES.get(key, {}).get("dromas")
    if not base:
        if key == "okhema":
            return "another blue road-beast" if idx > 1 else "a blue road-beast"
        return None
    if key == "okhema":
        return "another blue road-beast" if idx > 1 else "a blue road-beast"
    if idx > 1:
        return f"another {base[2:]}" if base.startswith("a ") else f"another {base}"
    return base


def flavor_name(place: str, kind: str, idx: int, name: str) -> str:
    if kind == "dawn":
        return name
    key = voice_key(place)
    if kind == "chimera":
        return _chimera_name(key, idx) or name
    if kind in {"dromas", "dromas_calf"}:
        return _dromas_name(key, idx, kind) or name
    if kind == "market_stall":
        pack = _STALLS.get(key) or _STALLS.get("okhema")
        if pack and key in _STALLS:
            return pack[0][(max(1, idx) - 1) % len(pack[0])]
        return name
    return _NAMES.get(key, {}).get(kind, name)


def flavor_doing(place: str, kind: str, status: str, doing: str,
                 period: int, idx: int) -> str:
    if kind == "dawn":
        return doing
    key = voice_key(place)
    quiet = status in {"resting", "quiet", "down", "in", "withdrawn", "ailing"}
    if kind == "market_stall" and status == "open" and key in _STALLS:
        line = _STALLS[key][1][(max(1, idx) - 1) % len(_STALLS[key][1])]
        if period == 2:
            return f"Action Hour — {line}"
        return line

    table = {
        "okhema": {
            "chimera:wandering": "doing laps of the baths like it owns the spa membership",
            "dromas:busy": "hauling today's gossip and tomorrow's cargo with equal dignity",
            "dromas_calf:day": "practicing dignity near the adult beasts",
            "grass:stirring": "whispering about everyone's shoes",
            "grass:day": "ready to gossip about everyone's shoes",
            "wind:stirring": "rearranging hairstyles without consent",
            "wind:day": "shopping for opinions to rearrange",
            "well:open": "serving cold drinks and colder takes",
            "shrine:day": "collecting quiet gratitude like spare coins",
            "incense:day": "smelling expensive on a street-food budget",
            "gate:open": "open, dramatic, still just a door",
            "pebble:any": "surviving chariot traffic like a tiny legend",
            "mosaic:day": "public art doing overtime under sandals",
            "fountain:open": "gossiping with stone at full volume",
            "pillar:any": "holding up the hour's light (and its own reputation)",
            "laundry:hanging": "drying shirts that have opinions about the wind",
            "courier:flying": "cutting the sky like late mail with confidence",
        },
        "dawncloud": {
            "chimera:wandering": "lobbying for snacks between motions",
            "dromas:busy": "hauling agendas and amphorae with equal gravity",
            "grass:day": "photosynthesizing democracy",
            "wind:day": "circulating drafts before they become law",
            "well:open": "serving water and clearer thinking",
            "shrine:day": "taking attendance of thanks",
            "incense:day": "calming the chamber one breath at a time",
            "pebble:any": "surviving every session without filing a complaint",
            "mosaic:day": "recording footprints as unofficial minutes",
            "fountain:open": "practicing oratory in splash form",
            "pillar:any": "holding the ceiling and the tone",
            "laundry:hanging": "airing robes until the rhetoric cools",
            "courier:flying": "delivering the next item of business",
        },
        "janus": {
            "dromas:busy": "carrying cargo through a city that is always mid-hello",
            "grass:day": "growing on both sides of the argument",
            "wind:day": "opening one door while closing another, politely",
            "well:open": "hydrating pilgrims and locals alike",
            "gate:open": "being a door so hard it became a personality",
            "pebble:any": "collecting stamps from a thousand thresholds",
            "fountain:open": "splashing in stereo",
            "ribbon:day": "tying thanks in matching pairs",
            "boat:day": "waiting for the next crossing of intention",
            "courier:flying": "choosing gates like a card trick",
            "incense:day": "sweetening the air where roads meet",
            "shrine:day": "collecting thanks for safe arrivals",
        },
        "kremnos": {
            "dromas:busy": "moving supplies with parade-ground posture",
            "dromas_calf:day": "learning stride without learning war",
            "grass:day": "standing at ease",
            "wind:day": "drying banner-cloth and cooler heads",
            "well:open": "watering heroes between chapters",
            "forge:ringing": "turning ore into tools, not trouble",
            "forge:day": "keeping iron honest",
            "banner:open": "flying color without calling a march",
            "pebble:any": "remembering drills it never signed up for",
            "pillar:any": "commemorating strength that chose rest today",
            "courier:flying": "carrying word faster than a challenge",
        },
        "grove": {
            "grove_leaf:day": "annotating sunlight in the margins",
            "olive:day": "offering shade and unsolicited critique",
            "cicada:singing": "brassing the hot hours into a seminar",
            "cicada:day": "keeping time for thinkers",
            "fountain:open": "providing water and peer review",
            "grass:day": "taking notes with its roots",
            "wind:day": "turning pages nobody left open",
            "pebble:any": "holding down theories that try to blow away",
            "dromas:busy": "waiting out a lecture with monumental patience",
            "dromas_calf:day": "auditing Intro to Roads",
        },
        "styxia": {
            "shore:day": "breathing pearl-light, not storm",
            "siren:day": "keeping a low shore-song for company",
            "pearl:any": "practicing being given back by the sea",
            "boat:day": "resting hull against hush",
            "net:day": "drying into patience",
            "tidepool:day": "mirroring sky in a pocket",
            "grass:day": "gossiping exclusively about tides",
            "wind:day": "carrying river hush inland",
            "well:open": "serving pale cool water",
            "fountain:open": "remembering names in splash",
            "incense:day": "sweet smoke for the living who remember",
            "pebble:any": "surviving soft currents like a tiny legend",
            "courier:flying": "cutting a quiet line over pearly water",
            "dromas:busy": "hauling with respect for the long current",
        },
        "aidonia": {
            "grass:day": "keeping green under white quiet",
            "wind:day": "rearranging frost, not funerals",
            "well:open": "serving cold clear water",
            "ribbon:day": "holding soft farewell without a grave",
            "boat:day": "waiting on the long pale current",
            "pebble:any": "a monument you can pocket",
            "pillar:any": "practicing patience in the snow",
            "incense:day": "cold-sweet thanks, not a summons",
            "dromas:busy": "walking frost roads with quiet dignity",
        },
        "aedes": {
            "wheat:day": "nodding like it recognizes your footsteps",
            "maze:day": "offering friendly wrong turns",
            "mill:day": "humming the village into flour",
            "kite:day": "practicing sky above home",
            "cicada:day": "summer brass over childhood fields",
            "grass:day": "welcoming returning sandals",
            "wind:day": "smelling like the road home",
            "well:open": "serving water and everyone's news",
            "shore:day": "keeping the village edge soft",
            "siren:day": "a lullaby for sailors between voyages",
            "pearl:any": "postcard from the tide",
            "boat:day": "tied like a promise kept",
            "net:day": "rehearsing tomorrow's catch",
            "tidepool:day": "holding a child's sky",
            "pebble:any": "watching generations learn to skip stones",
            "dromas:busy": "delivering village gossip at lawful speed",
        },
        "vortex": {
            "wind:day": "rippling starlight through quiet air",
            "pillar:any": "holding genesis without making a speech",
            "pebble:any": "keeping a Coreflame glint in pebble form",
        },
        "tomb": {
            "grove_leaf:day": "reminding stone that green once visited",
            "pillar:any": "ordering ruin into something walkable",
            "wind:day": "circulating like a long thought",
            "pebble:any": "being a pebble in a place that thinks in matrices",
        },
        "sky": {
            "wind:day": "drafting weather from memory",
            "pillar:any": "holding altitude with manners",
            "kite:day": "pretending to be a smaller sun",
            "grass:day": "growing on a terrace above rumor",
            "pebble:any": "refusing to fall the ordinary way",
        },
        "nether": {
            "wind:day": "moving among pale blossoms without hurry",
        },
        "beyond": {
            "wind:day": "turning a page the hour cannot see",
        },
    }.get(key, {})

    def pick(*candidates: str) -> Optional[str]:
        for c in candidates:
            if c in table:
                return table[c]
        return None

    busy_dromas = status in {"hauling", "well", "vigorous", "restless"}
    if kind == "chimera" and status == "wandering":
        return pick("chimera:wandering") or doing
    if kind == "dromas" and busy_dromas:
        return pick("dromas:busy") or doing
    if kind == "dromas_calf" and not quiet:
        return pick("dromas_calf:day") or doing
    if kind == "grass":
        if status == "stirring":
            return pick("grass:stirring", "grass:day") or doing
        if not quiet:
            return pick("grass:day") or doing
    if kind == "wind":
        if status == "stirring":
            return pick("wind:stirring", "wind:day") or doing
        if not quiet:
            return pick("wind:day") or doing
    if kind == "well" and status == "open":
        return pick("well:open") or doing
    if kind == "shrine" and status in {"quiet", "open"}:
        return pick("shrine:day") or doing
    if kind == "incense" and status in {"well", "open"}:
        return pick("incense:day") or doing
    if kind == "gate" and status == "open":
        return pick("gate:open") or doing
    if kind == "pebble":
        return pick("pebble:any") or doing
    if kind == "mosaic" and not quiet:
        return pick("mosaic:day") or doing
    if kind == "fountain" and status == "open":
        return pick("fountain:open") or doing
    if kind == "pillar":
        return pick("pillar:any") or doing
    if kind == "laundry" and status == "hanging":
        return pick("laundry:hanging") or doing
    if kind == "courier" and status == "flying":
        return pick("courier:flying") or doing
    if kind == "forge" and status == "ringing":
        return pick("forge:ringing", "forge:day") or doing
    if kind == "forge" and not quiet:
        return pick("forge:day") or doing
    if kind == "banner" and status == "open":
        return pick("banner:open") or doing
    if kind == "ribbon" and not quiet:
        return pick("ribbon:day") or doing
    if kind == "boat" and not quiet:
        return pick("boat:day") or doing
    if kind == "grove_leaf" and not quiet:
        return pick("grove_leaf:day") or doing
    if kind == "olive" and not quiet:
        return pick("olive:day") or doing
    if kind == "cicada":
        if status == "singing":
            return pick("cicada:singing", "cicada:day") or doing
        if not quiet:
            return pick("cicada:day") or doing
    if kind == "shore" and not quiet:
        return pick("shore:day") or doing
    if kind == "siren" and not quiet:
        return pick("siren:day") or doing
    if kind == "pearl":
        return pick("pearl:any") or doing
    if kind == "net" and not quiet:
        return pick("net:day") or doing
    if kind == "tidepool" and not quiet:
        return pick("tidepool:day") or doing
    if kind == "wheat" and not quiet:
        return pick("wheat:day") or doing
    if kind == "maze" and not quiet:
        return pick("maze:day") or doing
    if kind == "mill" and not quiet:
        return pick("mill:day") or doing
    if kind == "kite" and status in {"up", "well"}:
        return pick("kite:day") or doing
    if kind == "kite" and not quiet:
        return pick("kite:day") or doing
    return doing


def flavor_notice(place: str, kind: str, being: dict) -> Optional[str]:
    if kind == "dawn":
        return None
    key = voice_key(place)
    status = being.get("status") or ""

    if kind == "market_stall" and key in _STALLS:
        oid = being.get("id") or ""
        try:
            idx = int(str(oid).rsplit(":", 1)[-1])
        except ValueError:
            idx = 1
        notices = _STALLS[key][2]
        return notices[(max(1, idx) - 1) % len(notices)]

    notices = {
        "okhema": {
            "chimera": (
                "It locks eyes with you and delivers a proud Awoo — "
                "half greeting, half press conference."
            ),
            "dromas": (
                "A blue mountain with legs. It smells like warm earth "
                "and slightly judgmental patience."
            ),
            "dromas_calf": (
                "Small blue plates, full curiosity. The calf is auditioning "
                "for road-beast seriousness."
            ),
            "grass": (
                "Edge-grass doing jazz hands in the breeze. "
                "Very unprofessional. Very alive."
            ),
            "wind": "The hour has opinions, and they are breezy.",
            "well": "The well is open for business: hydration first, drama second.",
            "shrine": "Stone, gold, and zero lectures. Leave thanks; leave lighter.",
            "incense": "Soft smoke doing interior design in midair.",
            "gate": 'Threshold energy: half farewell, half "bring snacks back."',
            "pebble": "A pebble the size of a promise. Pocketable. Iconic.",
            "mosaic": (
                "Gold geometry underfoot — the city's scrapbook, polished daily."
            ),
            "fountain": "Splash, sparkle, zero chill. Okhema's best free concert.",
            "pillar": (
                "Tall, gold-trimmed, slightly smug. Excellent shade sponsorship."
            ),
            "laundry": "Cloth flags of the ordinary — heroic in a domestic way.",
            "courier": "Feathers, purpose, zero small talk. You are not CC'd.",
        },
        "dawncloud": {
            "chimera": (
                "It Awoos like a point of order. The chamber is briefly improved."
            ),
            "dromas": (
                "A road-beast that has sat through worse meetings. "
                "Warm earth; cooler politics."
            ),
            "grass": "Balcony grass leaning in to hear the vote.",
            "wind": "A draft arrives; several speeches improve immediately.",
            "well": "Clear water. Clearer heads optional, encouraged.",
            "shrine": "Thanks filed under 'miscellaneous gratitude.'",
            "incense": "Calm-debate incense. Soft enough to pause a filibuster.",
            "pebble": "This pebble has perfect attendance.",
            "mosaic": "Footsteps as unofficial minutes — gold and stone.",
            "fountain": "Eloquence in splash form. No one interrupts it.",
            "pillar": "Supports the roof and the tone of the room.",
            "laundry": "Robes airing until the rhetoric cools.",
            "courier": "Incoming motion. You are not on the distribution list.",
        },
        "janus": {
            "dromas": "A twin-city road-beast. It greets you twice, somehow once.",
            "grass": "Grass on both sides of the threshold. It refuses to choose.",
            "wind": "Hello and goodbye arrive in the same breeze.",
            "well": "Water for arrivals, farewells, and everyone mid-door.",
            "gate": "A door so ordinary it became famous. Step carefully.",
            "pebble": "This stone has more stamps than your travel notes.",
            "fountain": "Water going both ways and somehow not arguing.",
            "ribbon": "Twin thanks. Matching set. Destiny-approved.",
            "boat": "A hull waiting for intention to pick a bank.",
            "courier": "Gate roulette, professional grade.",
            "incense": "Crossroads sweetness — not a summons, a welcome.",
            "shrine": "Thanks for open doors. No invoices.",
        },
        "kremnos": {
            "dromas": (
                "Parade-ground posture, errand-of-peace cargo. "
                "Pets accepted as treaty."
            ),
            "dromas_calf": "Small plates, big stride lessons, zero war stories.",
            "grass": "Standing at ease. Do not ask it to charge.",
            "wind": "Dry, honest, excellent for banner-cloth and cooler heads.",
            "well": "Hydration for legends between chapters.",
            "forge": "Iron rings; tools bloom. No one is ordering a blade today.",
            "banner": "Color on the wind — a city, not a march order.",
            "pebble": "It remembers drills. It prefers being a pebble.",
            "pillar": "Strength commemorated as stillness. Shade included.",
            "courier": "Delivers like a challenge you already won.",
        },
        "grove": {
            "grove_leaf": "Leaf with footnotes. Shade with syllabus.",
            "olive": "Silver leaves; unsolicited critique included free.",
            "cicada": "The grove's brass section is in session.",
            "fountain": "Water and peer review. Sip carefully.",
            "grass": "This grass has done the reading.",
            "wind": "A breeze turning pages nobody admitted leaving open.",
            "pebble": "Paperweight of destiny. Pocketable thesis.",
            "dromas": "Monumental patience. Lecture still in progress.",
            "dromas_calf": "Auditing Intro to Roads. Taking it pass/fail.",
        },
        "styxia": {
            "shore": "Pearl-light breath. Soft company. No storm invited.",
            "siren": "A low shore-song — lullaby, not lure.",
            "pearl": "The river keeps giving these back. Take the hint.",
            "boat": "Pale hull at hush. Not yours to commandeer.",
            "net": "Mesh drying into patience.",
            "tidepool": "A pocket mirror for the sky.",
            "grass": "Tide gossip only. Very exclusive.",
            "wind": "River hush with good manners.",
            "well": "Pale cool water for the living who remember.",
            "fountain": "Splash that keeps names gently.",
            "incense": "Sweet for remembrance — never a grave-work.",
            "pebble": "Shore-stone the size of a kept promise.",
            "courier": "Quiet wing-cut over pearly water.",
            "dromas": "Does not hurry the dead or the living. Excellent beast.",
        },
        "aidonia": {
            "grass": "Green under white quiet. Vigil, not gloom.",
            "wind": "Northern hush. Rearranges frost, not funerals.",
            "well": "Cold clear water. Dignity intact.",
            "ribbon": "Soft farewell cloth. No grave required.",
            "boat": "Pale boat on the long current. Waiting, not claiming.",
            "pebble": "A pocket monument. Snow-approved.",
            "pillar": "Patience in stone. Thanatos's city keeps manners.",
            "incense": "Cold-sweet thanks. Not a summons.",
            "dromas": "Frost-road dignity. Warm neck plates anyway.",
        },
        "aedes": {
            "wheat": "It nods like it remembers your childhood nickname.",
            "maze": "Friendly wrong turns. Bring snacks.",
            "mill": "Stone humming the village into flour.",
            "kite": "Freedom practice above home.",
            "cicada": "Summer brass. Fields approved.",
            "grass": "Home-grass under returning feet.",
            "wind": "Smells like the road home.",
            "well": "Everybody's water. Everybody's news.",
            "shore": "Village edge at ease.",
            "siren": "Lullaby for sailors between voyages.",
            "pearl": "Postcard from the tide.",
            "boat": "Tied like a promise kept.",
            "net": "Tomorrow's dinner in rehearsal.",
            "tidepool": "A child's sky in water form.",
            "pebble": "Skipped by generations. Still iconic.",
            "dromas": "Village gossip at lawful speed.",
        },
        "vortex": {
            "wind": "Starlight ripples. Thoughts optional, welcome.",
            "pillar": "Genesis without the speech. Excellent manners.",
            "pebble": "Coreflame glint, pebble budget.",
            "resident": None,
        },
        "tomb": {
            "grove_leaf": "Green visiting ordered ruin. Soft contradiction.",
            "pillar": "Ruin, organized. Walkable. Slightly smug.",
            "wind": "Air circulating like a long thought.",
            "pebble": "A pebble in a matrix. Still pocketable.",
        },
        "sky": {
            "wind": "Aquila's leftover draft. Weather with memory.",
            "pillar": "Altitude with manners.",
            "kite": "A small sun on a string. Ambitious.",
            "grass": "Terrace grass above rumor.",
            "pebble": "Fell up. Do not ask how.",
        },
        "nether": {
            "wind": "Pale blossoms move. No hurry. No grave-work.",
        },
        "beyond": {
            "wind": "A page-edge breeze outside ordinary hours.",
        },
    }.get(key, {})

    if kind == "dromas" and being.get("caravan_id") and key == "okhema":
        return (
            "A blue mountain with legs leads the train — "
            "warm earth, judgmental patience, excellent schedule."
        )
    if kind == "well" and status != "open" and key == "okhema":
        return "The gossip well is off-duty; cisterns keep the night's drink."
    line = notices.get(kind)
    return line


def flavor_touch(place: str, action_id: str, kind: str) -> Optional[str]:
    key = voice_key(place)
    # Shared lively defaults, then regional overlays.
    shared = {
        ("pet", "chimera"): "soft head, softer ego; the Awoo upgrades to deluxe",
        ("pet", "dromas"): (
            "neck plates warm under your palm; it accepts pets as a civic duty"
        ),
        ("pet", "dromas_calf"): (
            "the calf bumps your hand — soft plates, big future ego"
        ),
        ("greet_dromas", ""): (
            "it blows warm dust at your sleeve — considered a five-star review"
        ),
        ("drink", ""): "cool water; your dignity remains mostly intact",
        ("touch_air", "grass"): (
            "cool blades tickle; they refuse to take you seriously"
        ),
        ("touch_air", "wind"): (
            "it slips through your fingers like a joke you almost caught"
        ),
        ("leave_offering", ""): (
            "a scrap of thanks lands; the shrine does not invoice you"
        ),
        ("breathe_incense", ""): (
            "sweet, brief, not a summons — just good manners for the nose"
        ),
        ("step_through", ""): "you cross; the gate pretends it invented walking",
        ("pick_keepsake", ""): (
            "you take the stone; the road does not file a complaint"
        ),
        ("trace_mosaic", ""): (
            "your fingertip follows a pattern; the mosaic pretends not to blush"
        ),
        ("watch_water", ""): "water works; you watch it win",
        ("rest_shade", ""): "cool stone; the column does not charge rent",
        ("read_cloth", ""): (
            "shirts on the line debate the wind; you decline to referee"
        ),
        ("follow_bird", ""): (
            "the bird is already gone; your invite was never in the thread"
        ),
        ("listen_iron", ""): "iron rings, then waits; you do not order a blade",
        ("listen_cicada", ""): "brass of the season — a concert, not a message",
        ("brush_grain", ""): "heads nod against your palm; this is not a harvest",
        ("trail_maze", ""): "you walk the maze-edge; it keeps its small ecology",
        ("hum_mill", ""): "stone turns as it has turned; you do not take grain",
        ("glance_hull", ""): "hull and mesh at rest; you do not take a boat",
        ("hang_ribbon", ""): "thanks on the line — not a bargain, not a grave",
    }
    regional = {
        "kremnos": {
            ("pet", "dromas"): (
                "neck plates warm; the beast accepts pets as a temporary truce"
            ),
            ("listen_iron", ""): (
                "iron sings shop, not war — tools bloom under your listening"
            ),
            ("read_cloth", ""): (
                "banner-cloth speaks color and weather, not march orders"
            ),
        },
        "grove": {
            ("rest_shade", ""): (
                "olive shade holds a minute; the Grove grades your posture kindly"
            ),
            ("listen_cicada", ""): (
                "brass seminar in the timber — you audit silently"
            ),
            ("touch_air", "wind"): (
                "a page-breeze; several unread thoughts rustle"
            ),
        },
        "styxia": {
            ("drink", ""): "pale cool water; remembrance optional, hydration required",
            ("watch_water", ""): "the shore works softly; you watch it win at hush",
            ("pick_keepsake", ""): (
                "you pocket a pearl-promise; the river does not invoice you"
            ),
            ("breathe_incense", ""): (
                "cold-sweet thanks for the living who remember"
            ),
        },
        "aidonia": {
            ("drink", ""): "cold clear water under white quiet",
            ("hang_ribbon", ""): (
                "soft farewell cloth — thanks without a grave"
            ),
            ("pick_keepsake", ""): (
                "a snow-stone pocket monument; the road files no complaint"
            ),
            ("breathe_incense", ""): (
                "cold-sweet; Thanatos's city keeps manners"
            ),
        },
        "aedes": {
            ("brush_grain", ""): (
                "wheat nods like it knows your nickname"
            ),
            ("hum_mill", ""): "the mill hums home into flour",
            ("touch_air", "wind"): (
                "sea-breeze that smells like coming back"
            ),
        },
        "janus": {
            ("step_through", ""): (
                "you cross; the gate greets you twice and means it once"
            ),
            ("hang_ribbon", ""): "twin thanks tied; destiny does not invoice",
        },
        "sky": {
            ("touch_air", "wind"): (
                "altitude draft; your hair briefly joins the Skyfolk"
            ),
            ("rest_shade", ""): (
                "sky-column shade; rent paid in wonder"
            ),
        },
        "vortex": {
            ("touch_air", "wind"): (
                "star-ripple air through your fingers"
            ),
            ("pick_keepsake", ""): (
                "a Coreflame-glint pebble; genesis does not invoice"
            ),
            ("rest_shade", ""): "pillar shade; quiet genesis included",
        },
        "tomb": {
            ("touch_air", "wind"): "matrix air; long thoughts optional",
            ("pick_keepsake", ""): (
                "a data-pebble (still a pebble); the tomb does not invoice"
            ),
            ("rest_shade", ""): "ordered ruin shade; walkable, slightly smug",
        },
    }.get(key, {})

    for cand in ((action_id, kind), (action_id, "")):
        if cand in regional:
            return regional[cand]
        if cand in shared:
            return shared[cand]
    return None
