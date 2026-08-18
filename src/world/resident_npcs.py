"""Stage-2 resident NPCs — a coarse Amphoreus street, not second protagonists.

Generated from a template, spread across real map cities. Copilot's small
`world_events.NPCS` list is left verbatim and wins on name collision.

Tick: after lived mechanisms flags exist, each city gets a visible set this
hour, and 1–3 Heir–resident encounters are persisted. No death, burial,
famine, war, or plague jobs.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import lived_entities as le

# Roles that imply sea/harbor — never assigned inland / Grove.
_SEA_ROLES = {"fisher", "harbor-hand", "boat-hand", "sailor"}

_TEMPERS = (
    "wry", "quiet", "brisk", "devout", "practical",
    "gentle", "dry", "warm", "spare", "keen",
)

_CITY_ROLES: Dict[str, List[str]] = {
    "Okhema": [
        "weaver", "baker", "merchant", "shrine-tender", "gate-warden",
        "scribe", "healer's aide", "courier", "smith", "water-carrier",
        "dromas-handler", "loom-hand",
    ],
    "Dawncloud": [
        "scribe", "shrine-tender", "council-clerk", "courier", "weaver",
        "healer's aide", "water-carrier",
    ],
    "Janusopolis": [
        "gate-warden", "courier", "merchant", "scribe", "shrine-tender",
        "baker", "dromas-handler",
    ],
    "Grove of Epiphany": [
        "grove-student", "scribe", "healer's aide", "timber-warden",
        "leaf-binder", "water-carrier",
    ],
    "Great Tomb": ["scribe", "stone-warden", "quiet scholar"],
    "Castrum Kremnos": [
        "smith", "dromas-handler", "courier", "baker", "gate-warden", "scribe",
    ],
    "Styxia": [
        "fisher", "harbor-hand", "boat-hand", "baker", "scribe", "water-carrier",
    ],
    "Aidonia": [
        "shrine-tender", "healer's aide", "weaver", "baker", "scribe", "quiet scholar",
    ],
    "Aedes Elysiae": [
        "field-hand", "baker", "weaver", "fisher", "dromas-handler", "scribe",
    ],
    "Vortex of Genesis": ["shrine-tender", "harbor-hand", "quiet scholar", "scribe"],
    "Eye of Twilight": [
        "sentry", "wind-watcher", "courier", "scribe", "water-carrier",
    ],
}

_CITY_COUNTS: Dict[str, int] = {
    "Okhema": 26,
    "Dawncloud": 8,
    "Janusopolis": 10,
    "Grove of Epiphany": 12,
    "Great Tomb": 4,
    "Castrum Kremnos": 10,
    "Styxia": 10,
    "Aidonia": 8,
    "Aedes Elysiae": 12,
    "Vortex of Genesis": 4,
    "Eye of Twilight": 6,
}

_CITY_TIES: Dict[str, List[str]] = {
    "Okhema": ["aglaea", "cerydra", "cipher", "hysilens"],
    "Dawncloud": ["cerydra", "aglaea"],
    "Janusopolis": ["tribbie"],
    "Grove of Epiphany": ["anaxa", "hyacine"],
    "Great Tomb": ["anaxa"],
    "Castrum Kremnos": ["mydei"],
    "Styxia": ["hysilens"],
    "Aidonia": ["castorice"],
    "Aedes Elysiae": ["phainon", "cyrene"],
    "Vortex of Genesis": ["cyrene"],
    "Eye of Twilight": ["hyacine"],
}

_ROLE_PLACE = {
    "weaver": "workshop", "loom-hand": "workshop", "smith": "workshop",
    "baker": "hearth", "merchant": "market", "shrine-tender": "shrine",
    "gate-warden": "gates", "scribe": "teaching hall",
    "healer's aide": "healer's house", "courier": "road",
    "water-carrier": "market", "dromas-handler": "road",
    "grove-student": "teaching hall", "timber-warden": "grove",
    "leaf-binder": "grove", "council-clerk": "shrine",
    "fisher": "harbor", "harbor-hand": "harbor", "boat-hand": "harbor",
    "sailor": "harbor", "field-hand": "fields", "stone-warden": "shrine",
    "quiet scholar": "teaching hall", "sentry": "gates",
    "wind-watcher": "road",
}

_RESERVED_NAMES = {
    "phainon", "aglaea", "mydei", "castorice", "anaxa", "hyacine", "cipher",
    "cerydra", "tribbie", "cyrene", "hysilens", "evernight", "dan heng",
    "bartholos", "seliose", "noldus", "mem", "theodosia", "gorgo", "krateros",
    "trianne", "eikura shuu", "researcher eikura shuu", "john", "sarah",
}

_PREFIXES = [
    "Mer", "Ktes", "Thal", "Hel", "Cael", "Lys", "Ore", "Ian", "Nyx",
    "Drom", "Ser", "Ves", "Aur", "Cle", "Ner", "Tim", "Eir", "Pha",
    "Chr", "Dor", "Hal", "Rhae", "Xan", "Kal", "Thes", "Oph",
    "Myr", "Sap", "Leo", "Zeph", "Cym", "Pyr", "Ast", "Neo", "Tho",
    "Ism", "Daph", "Pel", "Led", "Ophe",
]
_SUFFIXES = ["a", "ia", "on", "is", "as", "en", "or", "ys", "e", "os"]


def _stable(text: str) -> int:
    s = 0
    for ch in text:
        s = (s * 31 + ord(ch)) & 0x7FFFFFFF
    return s


def _name_at(n: int) -> str:
    """Deterministic Amphoreus-flavored name, never a reserved or Earth name."""
    attempts = 0
    i = n
    while attempts < 400:
        p = _PREFIXES[i % len(_PREFIXES)]
        s = _SUFFIXES[(i // len(_PREFIXES)) % len(_SUFFIXES)]
        # Mix so later indices don't just recycle the same 40.
        if (i // (len(_PREFIXES) * len(_SUFFIXES))) % 2:
            p = _PREFIXES[(i * 7) % len(_PREFIXES)]
        name = p + s
        if len(name) >= 4 and name.lower() not in _RESERVED_NAMES:
            if name[0].isupper() and name.isalpha():
                return name
        i += 11
        attempts += 1
    return f"Aeon{n}"


def _habit_for(role: str) -> Dict[str, str]:
    """Where they ARE by Light Calendar period (0 Entry … 4 Curtain-Fall)."""
    place = _ROLE_PLACE.get(role, "hearth")
    work = place
    if role in _SEA_ROLES:
        work = "harbor"
    if role in {"grove-student", "quiet scholar", "scribe"}:
        teach = "teaching hall"
        return {"0": "hearth", "1": teach, "2": teach, "3": "grove", "4": "hearth"}
    if role in {"merchant", "baker", "water-carrier"}:
        return {"0": "hearth", "1": "market", "2": "market", "3": "gates", "4": "hearth"}
    if role in {"gate-warden", "sentry"}:
        return {"0": "gates", "1": "gates", "2": "gates", "3": "gates", "4": "hearth"}
    if role in {"courier", "dromas-handler"}:
        return {"0": "hearth", "1": "road", "2": "road", "3": "gates", "4": "hearth"}
    if role in {"shrine-tender", "council-clerk"}:
        return {"0": "shrine", "1": "shrine", "2": "shrine", "3": "shrine", "4": "hearth"}
    if role == "healer's aide":
        return {"0": "healer's house", "1": "healer's house", "2": "healer's house",
                "3": "healer's house", "4": "hearth"}
    if role == "field-hand":
        return {"0": "hearth", "1": "fields", "2": "fields", "3": "road", "4": "hearth"}
    if role in {"weaver", "loom-hand", "smith"}:
        return {"0": "hearth", "1": "workshop", "2": "workshop", "3": "market", "4": "hearth"}
    if work == "harbor":
        return {"0": "hearth", "1": "harbor", "2": "harbor", "3": "harbor", "4": "hearth"}
    return {"0": "hearth", "1": work, "2": work, "3": "gates", "4": "hearth"}


def _generate() -> List[dict]:
    people: List[dict] = []
    n = 0
    used = set()
    for city, count in _CITY_COUNTS.items():
        roles = _CITY_ROLES[city]
        ties_pool = _CITY_TIES.get(city) or []
        for i in range(count):
            name = _name_at(n)
            while name.lower() in used:
                n += 1
                name = _name_at(n)
            used.add(name.lower())
            role = roles[i % len(roles)]
            if city in le.GROVE and role in _SEA_ROLES:
                role = "grove-student"
            npc = {
                "id": f"{_slug(city)}-{_slug(name)}-{i}",
                "name": name,
                "city": city,
                "role": role,
                "habitual_place": _ROLE_PLACE.get(role, "hearth"),
                "temperament": _TEMPERS[(n + i) % len(_TEMPERS)],
                "ties": [],
                "period_habit": _habit_for(role),
                "source": "stage2",
            }
            if ties_pool and (i % 3 == 0):
                npc["ties"] = [ties_pool[i % len(ties_pool)]]
            people.append(npc)
            n += 1
    return people


def _slug(text: str) -> str:
    out = []
    for ch in (text or "").lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_'" and out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-") or "x"


_ROSTER: Optional[List[dict]] = None


def generated_roster() -> List[dict]:
    global _ROSTER
    if _ROSTER is None:
        _ROSTER = _generate()
    return _ROSTER


def _wrap_copilot() -> List[dict]:
    """Read Copilot NPCS at call-time; do not copy the list into this file."""
    from . import world_events as wev
    wrapped = []
    extra = {
        "Bartholos": {
            "id": "okhema-bartholos", "habitual_place": "market",
            "temperament": "wry", "ties": ["cipher"],
            "period_habit": _habit_for("merchant"),
        },
        "Seliose": {
            "id": "grove-seliose", "habitual_place": "teaching hall",
            "temperament": "gentle", "ties": ["hyacine"],
            "period_habit": _habit_for("quiet scholar"),
        },
        "Noldus": {
            "id": "janusopolis-noldus", "habitual_place": "gates",
            "temperament": "warm", "ties": ["tribbie"],
            "period_habit": _habit_for("gate-warden"),
        },
        "Researcher Eikura Shuu": {
            "id": "okhema-eikura-shuu", "habitual_place": "teaching hall",
            "temperament": "keen", "ties": ["anaxa"],
            "period_habit": _habit_for("scribe"),
        },
        "Mem": {
            "id": "aedes-mem", "habitual_place": "hearth",
            "temperament": "quiet", "ties": ["cyrene"],
            "period_habit": _habit_for("quiet scholar"),
        },
        "Theodosia": {
            "id": "styxia-theodosia", "habitual_place": "harbor",
            "temperament": "spare", "ties": ["hysilens"],
            "period_habit": _habit_for("harbor-hand"),
        },
    }
    for raw in wev.NPCS:
        name = raw.get("name") or ""
        city = raw.get("city") or "Okhema"
        role = raw.get("role") or "resident"
        meta = extra.get(name) or {
            "id": f"{_slug(city)}-{_slug(name)}",
            "habitual_place": "hearth",
            "temperament": "quiet",
            "ties": [],
            "period_habit": _habit_for("scribe"),
        }
        wrapped.append({
            "id": meta["id"],
            "name": name,
            "city": city,
            "role": role,
            "habitual_place": meta["habitual_place"],
            "temperament": meta["temperament"],
            "ties": list(meta.get("ties") or []),
            "period_habit": dict(meta["period_habit"]),
            "flavor": raw.get("flavor") or "",
            "source": "copilot",
        })
    return wrapped


def living_roster() -> List[dict]:
    """Generated street plus Copilot names (Copilot wins on collision)."""
    by_name: Dict[str, dict] = {}
    for n in generated_roster():
        by_name[n["name"]] = n
    for n in _wrap_copilot():
        by_name[n["name"]] = n
    return list(by_name.values())


def roster_in_city(city: str) -> List[dict]:
    return [n for n in living_roster() if n.get("city") == city]


def _spot_now(npc: dict, period: int, flags: dict) -> str:
    habit = npc.get("period_habit") or {}
    spot = habit.get(str(period)) or habit.get(period) or "hearth"
    resting = bool(flags.get("resting"))
    city = npc.get("city") or ""
    # Local square — do not inherit the visitor's road or a Grove "market_open".
    local_market = (not resting) and period in (1, 2) and city not in le.GROVE
    if resting:
        if period == 0 and (npc.get("habitual_place") == "shrine"
                            or npc.get("role") == "shrine-tender"):
            return "shrine"
        if period == 0 and npc.get("role") == "healer's aide":
            return "healer's house"
        return "hearth"
    if spot == "market" and not local_market:
        if period == 3:
            return "market"
        return "hearth"
    return str(spot)


def visible_in_city(world, city: str, flags: Optional[dict] = None) -> List[dict]:
    """Residents a visitor could actually meet this hour in `city`."""
    if flags is None:
        try:
            from . import lived_mechanisms as lm
            flags = lm.derive(world, place=city)["flags"]
        except Exception:
            flags = {}
    period = 0
    try:
        period = int(world.clock.period)
    except Exception:
        period = 0
    surged = False
    try:
        surged = le._surged_here(world, city)
    except Exception:
        surged = bool(flags.get("surged"))
    out: List[dict] = []
    for npc in roster_in_city(city):
        if city in le.GROVE and npc.get("role") in _SEA_ROLES:
            continue
        spot = _spot_now(npc, period, flags)
        if surged and spot == "market":
            if _stable(npc["id"] + str(period)) % 3 != 0:
                continue
        row = dict(npc)
        row["spot"] = spot
        out.append(row)
    out.sort(key=lambda r: r.get("id") or r.get("name") or "")
    return out


def greet_here(world, city: str, limit: int = 4) -> List[dict]:
    """Visit affordance: 2–4 people here this hour, not a census."""
    return visible_in_city(world, city)[: max(0, limit)]


def last_encounter_for(world, city: str) -> Optional[dict]:
    try:
        res = (getattr(world, "vivid") or {}).get("residents") or {}
        for enc in res.get("encounters") or []:
            if enc.get("city") == city:
                return enc
    except Exception:
        return None
    return None


def residents_bucket(world) -> dict:
    from .vivid_stage2 import vivid_bucket
    v = vivid_bucket(world)
    b = v.get("residents")
    if not isinstance(b, dict):
        b = {}
        v["residents"] = b
    return b


def _heir_name(world, cid: str) -> str:
    try:
        return world.name_of(cid) or cid
    except Exception:
        return cid


def _encounter_line(npc: dict, heir_name: str, city: str, spot: str,
                    flags: dict) -> str:
    name = npc.get("name") or "A resident"
    role = npc.get("role") or "resident"
    rest = bool(flags.get("resting"))
    withdrawn = bool(flags.get("device_withdrawn"))
    thin = bool(flags.get("market_thin") or flags.get("surged"))
    if rest:
        line = f"{name} keeps the hearth while {heir_name} is in {city}."
    elif spot == "market":
        line = f"{role.capitalize()} {name} nods to {heir_name} at the stalls."
    elif spot == "gates":
        line = f"{name} is at the gates as {heir_name} passes."
    elif spot in {"harbor"}:
        line = f"{name} works the quay while {heir_name} is in {city}."
    elif spot in {"teaching hall", "grove"}:
        line = f"{name} looks up from a page as {heir_name} walks the Grove."
    elif spot == "workshop":
        line = f"{name} pauses at the bench when {heir_name} comes by."
    elif spot == "shrine":
        line = f"{name} tends the shrine as {heir_name} is in {city}."
    elif spot == "fields":
        line = f"{name} is in the fields while {heir_name} is in {city}."
    elif spot == "healer's house":
        line = f"{name} offers a cup of water at the healer's house as {heir_name} passes."
    elif spot == "road":
        line = f"{name} shares the road-edge with {heir_name}."
    else:
        line = f"{name} is here in {city} with {heir_name}."
    if withdrawn and not rest:
        line = line.rstrip(".") + "; lamps are already thinking of the hour."
    elif withdrawn and rest:
        line = line.rstrip(".") + " The Device is withdrawn."
    if thin and spot == "market":
        line = line.rstrip(".") + " The square stays close, not feast-busy."
    if flags.get("cooling") and spot in {"market", "road", "fields", "gates"}:
        line = line.rstrip(".") + " Cloth snaps in the air."
    return line


def apply_tick(world, flags: Optional[dict] = None) -> Dict[str, Any]:
    """Visible sets + Heir encounters for this clock key. Idempotent."""
    from . import lived_mechanisms as lm
    key = lm.clock_key(world)
    bucket = residents_bucket(world)
    if flags is None:
        flags = (lm.lived_bucket(world).get("flags")
                 or lm.derive(world).get("flags") or {})

    if bucket.get("last_key") == key:
        return {
            "visible_by_city": bucket.get("visible_by_city") or {},
            "encounters": list(bucket.get("encounters") or []),
            "lines": [],
            "idempotent": True,
            "last_key": key,
        }

    period = 0
    try:
        period = int(world.clock.period)
    except Exception:
        period = 0

    visible_by_city: Dict[str, List[dict]] = {}
    for city in _CITY_COUNTS:
        city_flags = dict(flags)
        try:
            city_flags["surged"] = le._surged_here(world, city)
        except Exception:
            pass
        rows = visible_in_city(world, city, flags=city_flags)
        visible_by_city[city] = [
            {"id": r["id"], "name": r["name"], "role": r["role"],
             "spot": r.get("spot"), "temperament": r.get("temperament")}
            for r in rows[:10]
        ]

    encounters: List[dict] = []
    lines: List[str] = []
    try:
        locations = set(world.agent_location.values())
    except Exception:
        locations = set()
    for city in sorted(locations):
        heirs = []
        try:
            heirs = list(world.agents_at(city) or [])
        except Exception:
            heirs = []
        if not heirs:
            continue
        city_flags = dict(flags)
        try:
            city_flags["surged"] = le._surged_here(world, city)
        except Exception:
            pass
        vis = visible_in_city(world, city, flags=city_flags)
        if not vis:
            continue
        for cid in heirs:
            if len(encounters) >= 3:
                break
            tied = [n for n in vis if cid in (n.get("ties") or [])]
            pool = tied or vis
            idx = _stable(key + city + cid) % len(pool)
            npc = pool[idx]
            spot = npc.get("spot") or _spot_now(npc, period, city_flags)
            hname = _heir_name(world, cid)
            line = _encounter_line(npc, hname, city, spot, city_flags)
            enc = {
                "resident": npc.get("name"),
                "resident_id": npc.get("id"),
                "role": npc.get("role"),
                "heir": cid,
                "heir_name": hname,
                "city": city,
                "spot": spot,
                "line": line,
            }
            encounters.append(enc)
            lines.append(line)
        if len(encounters) >= 3:
            break

    bucket["last_key"] = key
    bucket["visible_by_city"] = visible_by_city
    bucket["encounters"] = encounters
    return {
        "visible_by_city": visible_by_city,
        "encounters": encounters,
        "lines": lines,
        "idempotent": False,
        "last_key": key,
    }


def talk_to_npc(world, city: str, npc_name: str) -> dict:
    """Deterministic sanctuary-safe line; respects market_open / resting / sky."""
    from . import lived_mechanisms as lm
    from . import world_events as wev
    from .vivid_stage2 import vivid_bucket

    match = None
    for n in living_roster():
        if n.get("name") == npc_name:
            if n.get("city") != city:
                return {"ok": False, "reason": f"{npc_name} is not in {city}."}
            match = n
            break
    if not match:
        return {"ok": False, "reason": "unknown or non-living figure"}

    weather = ""
    try:
        weather = world.ambient_weather(city) or "an ordinary sky"
    except Exception:
        weather = "an ordinary sky"
    flags = {}
    try:
        flags = lm.derive(world, place=city)["flags"]
    except Exception:
        flags = {}

    flavor = (match.get("flavor") or "").strip()
    if not flavor:
        temper = match.get("temperament") or "quiet"
        flavor = (
            f"{match['name']} is a {temper} {match['role']} of {city}, "
            f"keeping to the {match.get('habitual_place') or 'street'}."
        )

    hour_note = ""
    if flags.get("resting"):
        hour_note = " They speak from a doorway; the city is at rest."
    elif flags.get("market_thin") or flags.get("surged"):
        hour_note = " Trade is thinner; they keep their voice down."
    elif flags.get("market_open") and (match.get("habitual_place") == "market"
                                       or "merchant" in (match.get("role") or "")):
        hour_note = " The square is trading around them."
    elif flags.get("device_withdrawn"):
        hour_note = " Lamps hold the street."

    surge_note = ""
    try:
        from . import living_world as lw
        if (lw.black_tide_enabled(world) and wev.surge_active(world)
                and city in (world.surge.get("cities") or [])):
            surge_note = " They glance toward the darkening edge and lower their voice."
    except Exception:
        pass

    line = (
        f"{match['name']} ({match['role']}) regards you under {weather}. "
        f"{flavor}{hour_note}{surge_note}"
    )
    entry = {"npc": match["name"], "city": city, "line": line,
             "ts": world.clock.format_short()}
    vivid_bucket(world).setdefault("npc_chats", []).append(entry)
    del vivid_bucket(world)["npc_chats"][20:]
    return {"ok": True, "line": line, "npc": match}
