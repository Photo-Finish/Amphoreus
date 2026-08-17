"""vivid_stage2.py — Stage 2: society and natural world the visitor can enter.

Canon-checked (official Amphoreus setting):
- Shared scenes are *organic* co-presence (PHILOSOPHY: host, never author).
- Black tide presses edge cities in *journey* mode only; Mydei guards Kremnos.
- Aglaea is blind but perceives through golden threads — she can sense when
  the visitor overhears private words that travel the threads.
- NPCs are the alive-only roster from world_events.NPCS (no dead figures).
- Aftermath stays peaceful: no surge invitations / tide pressure.

Pure data + logic. Never authors an Heir's spoken line for them.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Heirs whose duty keeps them at the tide's edge when it stirs.
_TIDE_GUARDIANS = {
    "mydei": "Castrum Kremnos",   # God of Strife — watches Kremnos / the tide
    "castorice": "Aidonia",       # Death — Aidonia is an EDGE city
    "hysilens": "Styxia",         # Ocean — Styxia feels the drowned edge
}

# Who can *sense* an overhear (canon perception), not mere gossip.
_OVERHEAR_SENSITIVE = {
    "aglaea": (
        "Your golden threads trembled — someone nearby listened to words that "
        "were not meant for every ear. You sensed the visitor overhearing. "
        "Treat them with the cool courtesy of one who notices, not with open "
        "accusation unless they confess; the tapestry remembers."
    ),
    "cipher": (
        "A locked door rattled: the visitor caught a private word. You noticed. "
        "Keep your secrets closer, and test them with a smile."
    ),
}


def vivid_bucket(world) -> dict:
    """Persistent Stage-2 ledger on the world state."""
    v = getattr(world, "vivid", None)
    if not isinstance(v, dict):
        v = {}
        world.vivid = v
    v.setdefault("overhears", [])          # [{heir, source, snippet, ts}]
    v.setdefault("noticed_by", {})         # cid -> {snippet, source, ts}
    v.setdefault("active_scene", None)     # {host, companions, place, ts} | None
    v.setdefault("declined", [])           # recent invite declines (for UI/tests)
    v.setdefault("npc_chats", [])          # [{npc, city, line, ts}]
    return v


# --------------------------------------------------------------------------- #
# Place-hour frame — land + society before every Visit
# --------------------------------------------------------------------------- #
def place_hour_frame(world, character_id: str,
                     name_of=None) -> dict:
    """A short scene card: clock, weather, who's here, errand, rumor, news."""
    from .schedules import scheduled_entry
    from . import world_events as wev
    from . import living_world as lw

    loc = world.location_name(character_id)
    traveling = bool(world.travel_info(character_id))
    period = world.clock.format_short()
    weather = world.ambient_weather(loc) or "the sky keeps its own counsel"
    sched_loc, sched_act = scheduled_entry(
        character_id, world.clock.day, world.clock.period)

    def _nm(cid: str) -> str:
        if name_of:
            try:
                return name_of(cid) or cid
            except Exception:
                return cid
        try:
            return world.name_of(cid)
        except Exception:
            return cid

    present = []
    if not traveling:
        for cid in world.agents_at(loc):
            if cid != character_id:
                present.append(_nm(cid))

    errand = world.ambient_errand(character_id) or ""
    news = world.ambient_news() or ""
    rumors = wev.rumors_for(world, character_id, limit=1)
    surge = ""
    if wev.surge_active(world) and loc in (world.surge.get("cities") or []):
        surge = wev.surge_text(world)
    mood = lw.mood_of(world, character_id)

    return {
        "place": loc,
        "traveling": traveling,
        "time": period,
        "weather": weather,
        "routine": sched_act,
        "routine_place": sched_loc,
        "present": present,
        "errand": errand,
        "news": news,
        "rumor": rumors[0] if rumors else "",
        "surge": surge,
        "mood": mood.get("label") or mood.get("valence"),
    }


def place_hour_markdown(frame: dict, heir_name: str) -> str:
    """Visitor-facing card text."""
    if frame.get("traveling"):
        where = f"{heir_name} is on the road."
    else:
        where = f"{heir_name} is in **{frame.get('place')}**."
    lines = [
        f"**This hour** — {frame.get('time')}",
        where,
        f"Sky: *{frame.get('weather')}*",
        f"Usual work: {frame.get('routine')} (in {frame.get('routine_place')})",
    ]
    if frame.get("present"):
        lines.append("Also here: " + ", ".join(frame["present"]))
    else:
        lines.append("Also here: — (for now, only the two of you)")
    if frame.get("errand"):
        lines.append(f"Errand on their mind: {frame['errand']}")
    if frame.get("rumor"):
        lines.append(f"Something heard lately: {frame['rumor']}")
    if frame.get("news"):
        lines.append(f"Word around Amphoreus: {frame['news']}")
    if frame.get("surge"):
        lines.append(f"⚠️ {frame['surge']}")
    return "\n\n".join(lines)


def place_hour_prompt_block(frame: dict) -> str:
    """Compact injector for the Heir's system prompt."""
    bits = [
        f"It is {frame.get('time')}.",
        f"The sky here: {frame.get('weather')}.",
        f"Your usual work this hour: {frame.get('routine')}.",
    ]
    if frame.get("present"):
        bits.append("Also present: " + ", ".join(frame["present"]) + ".")
    if frame.get("errand"):
        bits.append(f"An errand weighs on you: {frame['errand']}.")
    if frame.get("surge"):
        bits.append(frame["surge"])
    if frame.get("rumor"):
        bits.append(f"You heard: {frame['rumor']}")
    return "# This hour in the living world\n" + " ".join(bits)


# --------------------------------------------------------------------------- #
# Shared-scene invite — organic co-presence (MVP: host + one companion)
# --------------------------------------------------------------------------- #
def companions_here(world, host_id: str) -> List[str]:
    """Other Heirs co-located with the host and not traveling."""
    if world.travel_info(host_id):
        return []
    loc = world.location_name(host_id)
    return [c for c in world.agents_at(loc) if c != host_id]


def invite_shared_scene(world, host_id: str, companion_id: str,
                        name_of=None) -> dict:
    """Ask a co-located Heir to sit in the visitor's scene.

    Returns {ok, reason, host, companion, place, declined_by?}.
    Canon: guardians at a surged edge may refuse — duty first.
    """
    v = vivid_bucket(world)
    place = world.location_name(host_id)

    def _nm(cid):
        if name_of:
            try:
                return name_of(cid)
            except Exception:
                pass
        try:
            return world.name_of(cid)
        except Exception:
            return cid

    if companion_id == host_id:
        return {"ok": False, "reason": "cannot sit with yourself",
                "host": host_id, "companion": companion_id, "place": place}

    if world.travel_info(host_id) or world.travel_info(companion_id):
        reason = f"{_nm(companion_id)} is on the road — not here to sit with."
        v["declined"].append({"who": companion_id, "reason": reason,
                              "ts": world.clock.format_short()})
        del v["declined"][12:]
        return {"ok": False, "reason": reason, "host": host_id,
                "companion": companion_id, "place": place, "declined_by": companion_id}

    if companion_id not in companions_here(world, host_id):
        reason = f"{_nm(companion_id)} is not at {place}."
        return {"ok": False, "reason": reason, "host": host_id,
                "companion": companion_id, "place": place}

    # Black-tide duty: Mydei (and other edge guardians) may refuse.
    refuse = _tide_duty_refusal(world, companion_id, _nm)
    if refuse:
        v["declined"].append({"who": companion_id, "reason": refuse,
                              "ts": world.clock.format_short()})
        del v["declined"][12:]
        return {"ok": False, "reason": refuse, "host": host_id,
                "companion": companion_id, "place": place,
                "declined_by": companion_id, "cause": "black_tide"}

    # Aftermath: still allow sitting — peace does not forbid company.
    scene = {
        "host": host_id,
        "companions": [companion_id],
        "place": place,
        "ts": world.clock.format_short(),
    }
    v["active_scene"] = scene
    return {"ok": True, "reason": "joined", "host": host_id,
            "companion": companion_id, "place": place, "scene": scene}


def _tide_duty_refusal(world, character_id: str, name_of) -> str:
    """Guardians refuse social invitations when the tide presses their post."""
    from . import world_events as wev
    from . import living_world as lw
    try:
        from src.core.visitor_mode import current_mode
        if current_mode() == "aftermath":
            return ""
    except Exception:
        pass
    if not lw.black_tide_enabled(world) or not wev.surge_active(world):
        return ""
    home_edge = _TIDE_GUARDIANS.get(character_id)
    if not home_edge:
        return ""
    cities = world.surge.get("cities") or []
    here = world.location_name(character_id)
    # Refuse if their edge city is surged AND they stand there (or at home duty).
    if home_edge in cities and here in (home_edge,):
        nm = name_of(character_id)
        return (
            f"{nm} turns the invitation aside — the black tide presses "
            f"{home_edge}, and duty holds them to the watch."
        )
    return ""


def clear_shared_scene(world):
    vivid_bucket(world)["active_scene"] = None


def shared_scene_prompt_block(world, character_id: str,
                              name_of=None) -> str:
    """If this Heir is in an active shared scene, ground the chat in co-presence."""
    scene = vivid_bucket(world).get("active_scene")
    if not scene:
        return ""
    members = [scene.get("host")] + list(scene.get("companions") or [])
    if character_id not in members:
        return ""

    def _nm(cid):
        if name_of:
            try:
                return name_of(cid)
            except Exception:
                pass
        try:
            return world.name_of(cid)
        except Exception:
            return cid

    others = [_nm(c) for c in members if c != character_id]
    return (
        "# Shared scene — you are not alone with the visitor\n"
        f"You sit together in {scene.get('place')} with "
        + ", ".join(others)
        + ". Speak in your own voice. You may answer the visitor, and you may "
        "briefly acknowledge the other Heir as living company — never narrate "
        "their inner thoughts, never force a plot. Organic co-presence only."
    )


# --------------------------------------------------------------------------- #
# Society continuity — letters, gossip, bond drift made felt
# --------------------------------------------------------------------------- #
def society_continuity_block(world, character_id: str,
                             name_of=None) -> str:
    from . import world_events as wev

    parts = []
    letters = [l for l in world.letters if l.get("to") == character_id]
    if letters:
        latest = letters[-1]
        parts.append(
            f"A letter from {latest.get('from_name')} still rests near you: "
            f"\"{str(latest.get('text', ''))[:120]}\""
        )
    # Gossip that names the visitor
    for r in wev.rumors_for(world, character_id, limit=3):
        low = r.lower()
        if "stranger" in low or "visitor" in low or "trailblaze" in low:
            parts.append(f"Word of the visitor has reached you: {r}")
            break
    # Relationship drift involving this Heir
    drifts = []
    for key, delta in (world.relationship_delta or {}).items():
        if not isinstance(delta, int) or delta == 0:
            continue
        if character_id not in key.split("|"):
            continue
        a, b = key.split("|", 1)
        other = b if a == character_id else a
        try:
            on = world.name_of(other) if not name_of else name_of(other)
        except Exception:
            on = other
        way = "warmer" if delta > 0 else "cooler"
        drifts.append(f"your bond with {on} feels {way} of late")
    if drifts:
        parts.append(drifts[0])
    if not parts:
        return ""
    return "# Society continues around you\n" + "\n".join(f"- {p}" for p in parts)


# --------------------------------------------------------------------------- #
# Overhear — private words caught; golden-thread Heirs notice
# --------------------------------------------------------------------------- #
def note_overhear(world, about_heir: str, snippet: str,
                  source: str = "a private exchange") -> dict:
    """Record that the visitor overheard something concerning about_heir.

    Sensitive Heirs (Aglaea via golden threads, Cipher via locked doors)
    receive a *noticed_by* mark that later Visit injectors will surface.
    """
    v = vivid_bucket(world)
    entry = {
        "heir": about_heir,
        "snippet": (snippet or "")[:160],
        "source": source,
        "ts": world.clock.format_short(),
    }
    v["overhears"].append(entry)
    del v["overhears"][20:]

    # Who notices? Aglaea/Cipher always can if present in Amphoreus (threads /
    # trickery travel). Also the subject may grow cooler if told later.
    for watcher, guidance in _OVERHEAR_SENSITIVE.items():
        v["noticed_by"][watcher] = {
            "about": about_heir,
            "snippet": entry["snippet"],
            "source": source,
            "ts": entry["ts"],
            "guidance": guidance,
        }
    return entry


def overhear_prompt_block(world, character_id: str) -> str:
    mark = vivid_bucket(world).get("noticed_by", {}).get(character_id)
    if not mark:
        return ""
    return (
        "# You sensed an overhearing\n"
        + mark.get("guidance", "")
        + f"\nWhat was caught (as you sensed it): \"{mark.get('snippet', '')}\" "
        f"(from {mark.get('source', 'somewhere near')}, about "
        f"{mark.get('about', 'another')})."
    )


def clear_overhear_notice(world, character_id: str):
    vivid_bucket(world).get("noticed_by", {}).pop(character_id, None)


def detect_overhear_intent(user_message: str) -> bool:
    """Visitor phrases that mean they are listening in / reading private words."""
    t = (user_message or "").lower()
    keys = [
        "overhear", "overheard", "eavesdrop", "listened in", "listening in",
        "read their letter", "read the letter", "peeked at", "caught you saying",
        "i heard you tell", "i heard them", "through the door",
    ]
    return any(k in t for k in keys)


# --------------------------------------------------------------------------- #
# Arrive into an ongoing moment — recent encounter / letter as scene seed
# --------------------------------------------------------------------------- #
def ongoing_moment(world, character_id: str,
                   chronicle_tail: Optional[List[dict]] = None) -> dict:
    """Something that was already happening when the visitor arrives."""
    # Prefer a recent letter to this Heir
    letters = [l for l in world.letters if l.get("to") == character_id]
    if letters:
        latest = letters[-1]
        return {
            "kind": "letter",
            "summary": (
                f"When you arrive, {latest.get('to_name', 'they')} has a letter "
                f"from {latest.get('from_name')} open: "
                f"\"{str(latest.get('text', ''))[:100]}\""
            ),
            "raw": latest,
        }
    # Else a recent encounter line from chronicle if provided
    if chronicle_tail:
        for row in reversed(chronicle_tail[-12:]):
            if row.get("kind") == "encounter" and character_id:
                text = row.get("text") or ""
                if text:
                    return {
                        "kind": "encounter",
                        "summary": f"You arrive mid-moment: {text[:160]}",
                        "raw": row,
                    }
    rumor = None
    try:
        from . import world_events as wev
        rs = wev.rumors_for(world, character_id, limit=1)
        if rs:
            rumor = rs[0]
    except Exception:
        pass
    if rumor:
        return {
            "kind": "rumor",
            "summary": f"As you arrive, talk still hangs in the air: {rumor}",
            "raw": {"text": rumor},
        }
    return {"kind": "quiet", "summary": "The hour is quiet when you arrive.", "raw": {}}


def ongoing_moment_prompt(moment: dict) -> str:
    if not moment or moment.get("kind") == "quiet":
        return ""
    return (
        "# The visitor arrives into an ongoing moment\n"
        + moment.get("summary", "")
        + " Acknowledge the interrupted moment naturally if it fits — "
        "do not restart a scripted scene."
    )


# --------------------------------------------------------------------------- #
# Talk-to-place NPC — living residents only
# --------------------------------------------------------------------------- #
def npcs_in_city(city: str) -> List[dict]:
    from . import world_events as wev
    return [n for n in wev.NPCS if n.get("city") == city]


def talk_to_npc(world, city: str, npc_name: str) -> dict:
    """A short, deterministic sanctuary-safe line from a living NPC."""
    from . import world_events as wev
    match = None
    for n in wev.NPCS:
        if n.get("name") == npc_name and n.get("city") == city:
            match = n
            break
    if not match:
        # Allow match by name alone if they are in this city roster
        for n in wev.NPCS:
            if n.get("name") == npc_name:
                if n.get("city") != city:
                    return {"ok": False, "reason": f"{npc_name} is not in {city}."}
                match = n
                break
    if not match:
        return {"ok": False, "reason": "unknown or non-living figure"}

    weather = world.ambient_weather(city) or "an ordinary sky"
    surge_note = ""
    try:
        from . import world_events as wev2
        from . import living_world as lw
        if (lw.black_tide_enabled(world) and wev2.surge_active(world)
                and city in (world.surge.get("cities") or [])):
            surge_note = " They glance toward the darkening edge and lower their voice."
    except Exception:
        pass

    line = (
        f"{match['name']} ({match['role']}) regards you under {weather}. "
        f"{match['flavor']}{surge_note}"
    )
    entry = {"npc": match["name"], "city": city, "line": line,
             "ts": world.clock.format_short()}
    vivid_bucket(world).setdefault("npc_chats", []).append(entry)
    del vivid_bucket(world)["npc_chats"][20:]
    return {"ok": True, "line": line, "npc": match}


# --------------------------------------------------------------------------- #
# Lived road — weather / tide aware vignettes (extends ui_travel flavor)
# --------------------------------------------------------------------------- #
_ROAD_BY_WEATHER = {
    "rain": "Rain needles the path; carts leave dark tracks behind you.",
    "storm": "Thunder walks the ridge; you keep to the lee of the stones.",
    "clear": "The road runs bright and hard under a clean Amphoreus sky.",
    "fog": "Fog takes the milestones; you follow the sound of distant bells.",
    "blacktide": "At the edge of sight the air thickens — the black tide's breath.",
    "snow": "Pale dusting on the verge; your breath hangs like a small lantern.",
}


def classify_sky(weather: str) -> str:
    s = (weather or "").lower()
    if "black tide" in s or "darkens the sky" in s:
        return "blacktide"
    if "storm" in s or "thunder" in s:
        return "storm"
    if "rain" in s:
        return "rain"
    if "fog" in s or "mist" in s:
        return "fog"
    if "snow" in s:
        return "snow"
    return "clear"


def lived_road_line(world, fr: str, to: str, remaining: int = 0) -> str:
    """One richer road line using origin/destination weather + surge edges."""
    from . import world_events as wev
    from . import living_world as lw

    w_from = world.ambient_weather(fr) or ""
    w_to = world.ambient_weather(to) or ""
    sky = classify_sky(w_to or w_from)
    base = _ROAD_BY_WEATHER.get(sky, _ROAD_BY_WEATHER["clear"])
    if (lw.black_tide_enabled(world) and wev.surge_active(world)
            and to in (world.surge.get("cities") or [])):
        return (
            f"{base} Ahead, {to} waits under a surged sky — "
            f"{int(remaining)} day(s) remain."
        )
    key = f"{fr}|{to}|{remaining}|{sky}"
    # Stable slight variation without randomness across reruns
    twist = [
        f"Between {fr} and {to}, {base}",
        f"On the road to {to}: {base}",
        f"Leaving {fr} behind — {base}",
    ]
    seed = sum(ord(c) * (i + 1) for i, c in enumerate(key))
    return twist[seed % len(twist)]


def tide_edge_prompt(world, character_id: str) -> str:
    """Black tide as edge-of-life pressure (journey), for injectors."""
    from . import world_events as wev
    from . import living_world as lw
    try:
        from src.core.visitor_mode import current_mode
        if current_mode() == "aftermath":
            return ""
    except Exception:
        pass
    line = lw.surge_consequence_line(world, character_id)
    if line:
        return "# The black tide at the edge of life\n" + line
    if wev.surge_active(world):
        return "# The black tide at the edge of life\n" + wev.surge_text(world)
    return ""
