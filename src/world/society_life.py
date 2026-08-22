"""society_life.py — Stage-2 society continuity (shared hours, walk-ins, bonds).

Pure data + prompt scaffolding. Never authors Heir speech. Never opens the
knowledge wall. Sanctuary framing only — no famine / plague / war / burial.

Wire-in sites (Visit injectors, Walk handoff, Map popup) stay elsewhere;
this module stays testable without Streamlit.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Callable, Dict, List, Optional

# Soft canon overlays — not character cards. Cue text is atmosphere only.
BOND_PAIRS: Dict[frozenset, tuple] = {
    frozenset({"phainon", "mydei"}): (
        "rival warmth",
        "The air between you and Mydei/Phainon carries the old sparring heat — "
        "fond, sharp, unfinished.",
    ),
    frozenset({"aglaea", "tribbie"}): (
        "golden thread",
        "Aglaea's threads / Tribbie's care hum quietly when you share a room.",
    ),
    frozenset({"hysilens", "cerydra"}): (
        "tide and crown",
        "Old loyalty between Hysilens and Cerydra sits in the room like held music.",
    ),
    frozenset({"castorice", "phainon"}): (
        "quiet regard",
        "A soft distance of regard hangs between Castorice and Phainon.",
    ),
    frozenset({"anaxa", "hyacine"}): (
        "grove desk",
        "Instructor and assistant stillness — Anaxa and Hyacine share the Grove desk "
        "(she is his assistant instructor, not only a student).",
    ),
    frozenset({"anaxa", "phainon"}): (
        "grove desk",
        "Teacher and student — Anaxa's exacting care and Phainon's bright weight.",
    ),
    frozenset({"cyrene", "phainon"}): (
        "home shore",
        "Aedes air — Cyrene and Phainon share a home-shore ease.",
    ),
    frozenset({"castorice", "hyacine"}): (
        "close friends",
        "Cassie warmth — Castorice and Hyacine share close-friend ease (dried flowers, soft nicknames, no distance of duty).",
    ),
    frozenset({"cipher", "aglaea"}): (
        "thread and shadow",
        "Cipher's locked-door ease and Aglaea's golden patience sit together — old trust under the jokes, never a scripted confession.",
    ),
}

# Topics that would breach the knowledge wall if echoed as lessons.
_EARTH_MARKERS = (
    "python", "javascript", "smartphone", "iphone", "android", "internet",
    "wifi", "wi-fi", "computer", "laptop", "chatgpt", "openai", "google",
    "programming", "codebase", "github", "kubernetes", "docker", "sql",
    "earth", "america", "china", "europe", "tokyo", "new york", "bitcoin",
    "satellite", "spaceship", "astronaut", "quantum computer", "nuclear bomb",
    "vaccine", "covid", "twitter", "facebook", "tiktok", "youtube",
)

_HEIR_DISPLAY = {
    "tribbie": "Tribbie",
    "cerydra": "Cerydra",
    "evernight": "Evernight",
    "dan-heng-permansor-terrae": "Dan Heng",
    "hysilens": "Hysilens",
    "hyacine": "Hyacine",
    "phainon": "Phainon",
    "anaxa": "Anaxa",
    "aglaea": "Aglaea",
    "mydei": "Mydei",
    "castorice": "Castorice",
    "cipher": "Cipher",
    "cyrene": "Cyrene",
}

_GATHERING_CAP = 24
_ECO_NOTICE_CAP = 40
_ABSENCE_DAYS = 5
_GATHERING_RECALL_DAYS = 14
_GATHERING_RECALL_ENTRIES = 6
_ECO_NOTICE_DAYS = 4


# --------------------------------------------------------------------------- #
# Ledger
# --------------------------------------------------------------------------- #
def vivid_ext(world) -> dict:
    """Ensure world.vivid keys for society-life continuity."""
    v = getattr(world, "vivid", None)
    if not isinstance(v, dict):
        v = {}
        world.vivid = v
    v.setdefault("shared_gatherings", [])
    v.setdefault("eco_notices", [])
    v.setdefault("visitor_absences", {})
    v.setdefault("resident_memory", {})
    v.setdefault("teaching_echoes", [])
    v.setdefault("heir_invites", {})
    v.setdefault("letter_choices", {})
    v.setdefault("resident_errands", {})
    return v


def _day_index(world) -> int:
    try:
        from .sanctuary_clock import _day_index as _di
        return int(_di(world.clock))
    except Exception:
        try:
            c = world.clock
            return int(getattr(c, "year", 0) or 0) * 400 + int(
                getattr(c, "month", 0) or 0
            ) * 28 + int(getattr(c, "day", 0) or 0)
        except Exception:
            return 0


def _clock_label(world) -> str:
    try:
        return world.clock.format_short()
    except Exception:
        return ""


def _nm(cid: str, name_of: Optional[Callable] = None, world=None) -> str:
    if name_of:
        try:
            n = name_of(cid)
            if n:
                return n
        except Exception:
            pass
    if world is not None:
        try:
            return world.name_of(cid)
        except Exception:
            pass
    return _HEIR_DISPLAY.get(cid, cid)


# --------------------------------------------------------------------------- #
# Item 2 — Shared moments stick in solo visits
# --------------------------------------------------------------------------- #
def note_shared_gathering(
    world,
    members: list,
    place: str,
    snippets: list,
    *,
    clock_label: str = "",
) -> dict:
    """Append to vivid['shared_gatherings']; also return payload. Cap ~24."""
    v = vivid_ext(world)
    clean_members = [str(m).strip() for m in (members or []) if str(m).strip()]
    clean_snips = [
        str(s).strip()[:160] for s in (snippets or []) if str(s).strip()
    ][:8]
    payload = {
        "members": clean_members,
        "place": place or "",
        "snippets": clean_snips,
        "clock": clock_label or _clock_label(world),
        "day_index": _day_index(world),
        "ts": _clock_label(world),
    }
    bucket = v.setdefault("shared_gatherings", [])
    bucket.append(payload)
    if len(bucket) > _GATHERING_CAP:
        v["shared_gatherings"] = bucket[-_GATHERING_CAP:]
    return payload


def _gatherings_for(
    world, character_id: str, *, limit_entries: int = _GATHERING_RECALL_ENTRIES
) -> List[dict]:
    v = vivid_ext(world)
    today = _day_index(world)
    involving = [
        g for g in (v.get("shared_gatherings") or [])
        if character_id in (g.get("members") or [])
    ]
    recent_by_day = [
        g for g in involving
        if today - int(g.get("day_index") or today) <= _GATHERING_RECALL_DAYS
    ]
    pool = recent_by_day if recent_by_day else involving
    return pool[-limit_entries:]


def shared_gathering_prompt(
    world, character_id: str, name_of=None
) -> str:
    """Short recall block for solo Visit if this Heir was in a recent gathering.

    Clears nothing — memory stays in the ledger.
    """
    hits = _gatherings_for(world, character_id)
    if not hits:
        return ""
    g = hits[-1]
    others = [
        _nm(m, name_of, world)
        for m in (g.get("members") or [])
        if m != character_id
    ]
    place = g.get("place") or "somewhere familiar"
    snip = ""
    for s in (g.get("snippets") or []):
        if s:
            snip = str(s)[:100]
            break
    who = ", ".join(others) if others else "the company"
    lines = [
        "# A shared hour you remember",
        f"Not long ago in {place}, you shared an hour with {who}.",
    ]
    if snip:
        lines.append(f"A scrap that still sits with you: \"{snip}\"")
    lines.append(
        "If it fits, let that shared hour color a breath of your reply — "
        "never narrate another Heir's private thoughts."
    )
    return "\n".join(lines)


def promote_gathering_to_memories(
    manager, members, place, snippets
) -> None:
    """Add a curated one-liner moment memory per member (not full transcript)."""
    if manager is None:
        return
    mem = getattr(manager, "memory", None)
    if mem is None or not hasattr(mem, "add_memory"):
        return
    members = [str(m).strip() for m in (members or []) if str(m).strip()]
    snips = [str(s).strip() for s in (snippets or []) if str(s).strip()]
    scrap = snips[0][:80] if snips else "quiet company"
    place = place or "a shared place"
    for cid in members:
        others = [_HEIR_DISPLAY.get(m, m) for m in members if m != cid]
        who = ", ".join(others) if others else "the company"
        line = (
            f"A shared hour in {place} with {who} — "
            f"one scrap remains: {scrap}."
        )
        try:
            mem.add_memory(cid, mtype="moment", content=line, importance=2)
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# Item 3+4 — Stronger walk-in scenes
# --------------------------------------------------------------------------- #
def _heirs_named_in(text: str) -> List[str]:
    found = []
    low = (text or "")
    for cid, name in _HEIR_DISPLAY.items():
        if re.search(rf"\b{re.escape(name)}\b", low, flags=re.IGNORECASE):
            found.append(cid)
    return found


def walk_in_scene(
    world,
    character_id: str,
    chronicle_tail=None,
    name_of=None,
) -> dict:
    """Prefer richer mid-letter / mid-encounter / mid-rumor scenes."""
    # Letter open
    letters = [
        l for l in (getattr(world, "letters", None) or [])
        if l.get("to") == character_id
    ]
    if letters:
        latest = letters[-1]
        from_name = latest.get("from_name") or _nm(
            latest.get("from", ""), name_of, world
        )
        excerpt = str(latest.get("text", "") or "")[:120]
        heir_name = _nm(character_id, name_of, world)
        ui = (
            f"You find {heir_name} mid-letter — a page from {from_name} lies open: "
            f"\"{excerpt}\""
        )
        prompt = (
            "# Walk-in — a letter interrupted\n"
            f"When the visitor arrives, you have a letter from {from_name} open. "
            f"Excerpt still under your eye: \"{excerpt}\" "
            "Acknowledge the interruption naturally if it fits — "
            "do not restart a scripted scene, and do not invent the writer's next lines."
        )
        return {
            "kind": "letter_open",
            "from_name": from_name,
            "excerpt": excerpt,
            "interrupted": True,
            "ui_summary": ui,
            "prompt_block": prompt,
            "raw": latest,
        }

    # Chronicle encounter / heir talk
    if chronicle_tail:
        for row in reversed(list(chronicle_tail)[-12:]):
            if row.get("kind") not in ("encounter", "meeting", "heir_talk", None):
                # Still allow plain encounter-ish rows with text
                if row.get("kind") and row.get("kind") != "encounter":
                    continue
            text = str(row.get("text") or "").strip()
            if not text:
                continue
            named = _heirs_named_in(text)
            if (
                character_id in named
                and len([c for c in named if c != character_id]) >= 1
            ):
                others = [
                    _nm(c, name_of, world)
                    for c in named
                    if c != character_id
                ]
                ui = (
                    f"You arrive mid-exchange — {text[:140]}"
                )
                prompt = (
                    "# Walk-in — Heirs mid-talk\n"
                    f"When the visitor arrives, you are already in company "
                    f"({', '.join(others)}). What was in the air: {text[:160]} "
                    "Continue in your own voice; never put words in another Heir's mouth."
                )
                return {
                    "kind": "heir_talk",
                    "ui_summary": ui,
                    "prompt_block": prompt,
                    "raw": row,
                }
            ui = f"You arrive mid-moment: {text[:160]}"
            prompt = (
                "# Walk-in — an encounter mid-stride\n"
                f"The visitor arrives while this is still unfolding: {text[:160]} "
                "Acknowledge the interrupted moment naturally if it fits."
            )
            return {
                "kind": "encounter_mid",
                "ui_summary": ui,
                "prompt_block": prompt,
                "raw": row,
            }

    # Rumor hanging
    rumor = None
    try:
        from . import world_events as wev
        rs = wev.rumors_for(world, character_id, limit=1)
        if rs:
            rumor = rs[0]
    except Exception:
        pass
    if rumor:
        ui = f"Talk still hangs in the air as you arrive: {rumor}"
        prompt = (
            "# Walk-in — a rumor still hanging\n"
            f"Word has not finished settling: {rumor} "
            "You may let it color the hour; do not invent famine, plague, war, or burial."
        )
        return {
            "kind": "rumor_hanging",
            "ui_summary": ui,
            "prompt_block": prompt,
            "raw": {"text": rumor},
        }

    return {
        "kind": "quiet",
        "ui_summary": "The hour is quiet when you arrive.",
        "prompt_block": "",
        "raw": {},
    }


def walk_in_prompt(scene: dict) -> str:
    if not scene or scene.get("kind") == "quiet":
        return ""
    return str(scene.get("prompt_block") or "").strip()


# --------------------------------------------------------------------------- #
# Letter mini-scene — read together / wait / leave
# --------------------------------------------------------------------------- #

_LETTER_SCENE_KINDS = frozenset({"letter_open", "letter"})
_LETTER_CHOICE_LABELS = {
    "read_together": "read the letter together",
    "wait_quietly": "wait quietly beside the open letter",
    "leave_them": "step back and leave them to the letter",
}


def letter_scene_choices(scene: dict) -> list:
    """Choices for mid-letter walk-ins (letter_open, or legacy kind letter)."""
    if not scene or scene.get("kind") not in _LETTER_SCENE_KINDS:
        return []
    return [
        {"id": "read_together", "label": "Read it with them"},
        {"id": "wait_quietly", "label": "Wait quietly"},
        {"id": "leave_them", "label": "Leave them to the letter"},
    ]


def apply_letter_choice(world, character_id: str, choice_id: str) -> dict:
    """Persist the visitor's letter-scene choice for this Visit hour."""
    v = vivid_ext(world)
    bucket = v.setdefault("letter_choices", {})
    choice_id = (choice_id or "").strip()
    if choice_id not in _LETTER_CHOICE_LABELS:
        return {"ok": False, "reason": "unknown choice"}
    entry = {
        "choice_id": choice_id,
        "label": _LETTER_CHOICE_LABELS[choice_id],
        "hour": _clock_label(world),
        "day_index": _day_index(world),
        "character_id": character_id,
    }
    bucket[character_id] = entry
    return {"ok": True, **entry}


def current_letter_choice(world, character_id: str) -> dict:
    """Today's letter-scene choice for this Heir, or {}."""
    v = vivid_ext(world)
    entry = (v.get("letter_choices") or {}).get(character_id)
    if not isinstance(entry, dict):
        return {}
    if entry.get("day_index") != _day_index(world):
        return {}
    return entry


def letter_choice_prompt(world, character_id: str) -> str:
    """Prompt addon when a letter-scene choice was made this calendar day."""
    entry = current_letter_choice(world, character_id)
    label = (entry.get("label") or "") if entry else ""
    if not label:
        return ""
    return (
        "# The visitor's choice at your letter\n"
        f"When they found you mid-letter, they chose to {label}. "
        "Acknowledge that choice lightly if it fits — do not restart a scripted scene, "
        "and do not invent the writer's next lines."
    )


# --------------------------------------------------------------------------- #
# Item 6 — Bond weather
# --------------------------------------------------------------------------- #

def bond_weather_block(
    world, character_id: str, name_of=None
) -> str:
    """Soft co-location bond cue. Never invent jealousy plots."""
    try:
        if world.travel_info(character_id):
            return ""
    except Exception:
        pass
    loc = ""
    try:
        loc = world.location_name(character_id)
    except Exception:
        return ""
    present = []
    try:
        for cid in world.agents_at(loc):
            if cid == character_id:
                continue
            try:
                if world.travel_info(cid):
                    continue
            except Exception:
                pass
            present.append(cid)
    except Exception:
        return ""
    dh = "dan-heng-permansor-terrae"

    # Prefer a canon soft pair involving this Heir and someone here.
    for other in present:
        key = frozenset({character_id, other})
        if key in BOND_PAIRS:
            tag, cue = BOND_PAIRS[key]
            return (
                f"# Bond weather\n"
                f"({tag}) {cue} "
                "Let it sit as air in the room — never invent jealousy, rivalry plots, "
                "or force either Heir to speak about the bond."
            )

    # Cipher co-located (not a fake pair): locked-door secrecy weather.
    # Checked before relationship_delta so soft deltas do not swallow it.
    if present and (character_id == "cipher" or "cipher" in present):
        return (
            "# Bond weather\n"
            "(locked-door air) Cipher's presence thins the room to secrets and side-doors — "
            "a soft secrecy weather, not a claim of romance. "
            "Let it sit as air — never invent jealousy or force a confession."
        )

    # Dan Heng · Permansor Terrae: soft Georios / earth-underfoot land cue
    # (alone or with company — place texture, not a relationship plot).
    if character_id == dh or dh in present:
        place = loc or ""
        return (
            "# Bond weather\n"
            "(earth underfoot) Soft Georios land-cue — earth underfoot, stone patience"
            + (f" in {place}" if place else "")
            + ". Let the ground steady the hour; do not invent Titan sermons."
        )

    if not present:
        return ""

    # Fallback: relationship_delta warmer/cooler with someone here.
    deltas = getattr(world, "relationship_delta", None) or {}
    for other in present:
        pair = "|".join(sorted([character_id, other]))
        delta = deltas.get(pair, 0)
        if not isinstance(delta, int) or delta == 0:
            continue
        on = _nm(other, name_of, world)
        way = "warmer" if delta > 0 else "cooler"
        return (
            f"# Bond weather\n"
            f"Your bond with {on} feels {way} of late. "
            "Hold it as weather, not as a plot — no jealousy scripts."
        )

    return ""

def record_eco_notice(
    world,
    *,
    place: str,
    object_id: str,
    kind: str,
    line: str,
    visitor_action: str = "",
    heir_hint: str = "",
) -> None:
    """Append to vivid['eco_notices'] with ts/clock. Cap 40."""
    v = vivid_ext(world)
    entry = {
        "place": place or "",
        "object_id": object_id or "",
        "kind": kind or "",
        "line": (line or "")[:200],
        "visitor_action": (visitor_action or "")[:120],
        "heir_hint": (heir_hint or "")[:160],
        "clock": _clock_label(world),
        "day_index": _day_index(world),
        "ts": _clock_label(world),
    }
    bucket = v.setdefault("eco_notices", [])
    bucket.append(entry)
    if len(bucket) > _ECO_NOTICE_CAP:
        v["eco_notices"] = bucket[-_ECO_NOTICE_CAP:]


def eco_notices_for_place(world, place: str, limit: int = 5) -> list:
    v = vivid_ext(world)
    place = place or ""
    rows = [
        e for e in (v.get("eco_notices") or [])
        if (e.get("place") or "") == place
    ]
    return rows[-max(0, int(limit)):]


def eco_notice_prompt(world, character_id: str) -> str:
    """Notices at the Heir's current place from the last few days."""
    try:
        if world.travel_info(character_id):
            return ""
        place = world.location_name(character_id)
    except Exception:
        return ""
    today = _day_index(world)
    rows = []
    for e in eco_notices_for_place(world, place, limit=12):
        age = today - int(e.get("day_index") or today)
        if age <= _ECO_NOTICE_DAYS:
            rows.append(e)
    if not rows:
        return ""
    lines = ["# What the land already showed"]
    for e in rows[-5:]:
        bit = (e.get("line") or "").strip()
        if not bit:
            continue
        hint = (e.get("heir_hint") or "").strip()
        if hint:
            lines.append(f"- {bit} ({hint})")
        else:
            lines.append(f"- {bit}")
    if len(lines) == 1:
        return ""
    lines.append(
        "You may answer about what the land already showed — cared chimera, "
        "touched shore, watched road — without inventing harm or opening the wall."
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Item 16 — Long leave / return
# --------------------------------------------------------------------------- #
def note_visit_touch(world, character_id: str) -> None:
    """Update vivid visitor_absences[cid].last_seen_day from world.clock."""
    v = vivid_ext(world)
    absences = v.setdefault("visitor_absences", {})
    row = absences.setdefault(character_id, {})
    row["last_seen_day"] = _day_index(world)
    row["last_seen_clock"] = _clock_label(world)


def _parse_iso_day_index(iso_ish: str, world) -> Optional[int]:
    """Best-effort: treat ISO date as civil GMT+8 and map via day gap estimate."""
    if not iso_ish or not isinstance(iso_ish, str):
        return None
    s = iso_ish.strip()
    # Accept YYYY-MM-DD or full ISO timestamp
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if not m:
        return None
    try:
        then = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        # Approximate: compare to "now" civil from clock if available; else use then vs today.
        # Light Calendar day_index is Amphoreus-internal; for bond fallback we only need
        # a *relative* gap. Use civil days between then and today (GMT+8).
        try:
            from .sanctuary_clock import GMT8
            now = datetime.now(GMT8).replace(tzinfo=None)
        except Exception:
            now = datetime.now()
        gap = (now.date() - then.date()).days
        return _day_index(world) - max(0, gap)
    except Exception:
        return None


def absence_prompt_block(
    world, character_id: str, bond_last_seen: str | None = None
) -> str:
    """Soft return beat after >=5 days away. Once per clock day via returned_ack."""
    v = vivid_ext(world)
    absences = v.setdefault("visitor_absences", {})
    row = absences.setdefault(character_id, {})
    today = _day_index(world)

    if row.get("returned_ack") == today:
        return ""

    last = row.get("last_seen_day")
    if last is None and bond_last_seen:
        last = _parse_iso_day_index(bond_last_seen, world)

    if last is None:
        # First touch — seed without absence drama.
        note_visit_touch(world, character_id)
        return ""

    gap = today - int(last)
    if gap < _ABSENCE_DAYS:
        note_visit_touch(world, character_id)
        return ""

    block = (
        "# The visitor returns after absence\n"
        "Some days have passed since they last stood with you. Letters may have "
        "piled a little; the hearth was kept; road dust still hangs on their sleeve. "
        "Greet the return in your own voice — no accusation, no invented catastrophe."
    )
    row["returned_ack"] = today
    note_visit_touch(world, character_id)
    return block


def absence_visit_vignette(
    world, character_id: str, bond_last_seen: str | None = None
) -> str:
    """Literary 1–2 sentences for Visit chrome after a long leave.

    Peek-only: does not set returned_ack (the prompt block still owns that).
    UI should gate with session key shown_return_vignette_{cid}.
    """
    v = vivid_ext(world)
    absences = v.get("visitor_absences") or {}
    row = absences.get(character_id) or {}
    today = _day_index(world)

    last = row.get("last_seen_day")
    if last is None and bond_last_seen:
        last = _parse_iso_day_index(bond_last_seen, world)
    if last is None:
        return ""

    gap = today - int(last)
    if gap < _ABSENCE_DAYS:
        return ""

    days = max(_ABSENCE_DAYS, gap)
    return (
        f"Some {days} Light-Calendar days have passed since you last stood here. "
        "The hearth was kept; a little road dust still hangs on a sleeve — "
        "greet the return without accusation."
    )


# --------------------------------------------------------------------------- #
# Item 15 — Co-located teaching echo (secondhand only)
# --------------------------------------------------------------------------- #
def _topic_looks_earth(topic: str) -> bool:
    low = (topic or "").lower()
    return any(m in low for m in _EARTH_MARKERS)


def maybe_echo_teaching(
    world, teacher_id: str, topic: str, place: str
) -> list:
    """Record secondhand echoes for co-located Heirs. Does not open the wall."""
    topic = (topic or "").strip()
    if not topic or _topic_looks_earth(topic):
        return []
    place = place or ""
    try:
        here = [
            cid for cid in world.agents_at(place)
            if cid != teacher_id and not world.travel_info(cid)
        ]
    except Exception:
        return []
    if not here:
        return []

    v = vivid_ext(world)
    echoes = v.setdefault("teaching_echoes", [])
    out = []
    teacher_name = _nm(teacher_id, None, world)
    for cid in here:
        entry = {
            "for": cid,
            "teacher_id": teacher_id,
            "teacher_name": teacher_name,
            "topic": topic[:120],
            "place": place,
            "secondhand": True,
            "consumed": False,
            "day_index": _day_index(world),
            "clock": _clock_label(world),
        }
        echoes.append(entry)
        out.append(entry)
    # Soft cap
    if len(echoes) > 40:
        v["teaching_echoes"] = echoes[-40:]
    return out


def teaching_echo_prompt(world, character_id: str) -> str:
    """Inject secondhand 'you overheard a lesson nearby'; mark consumed."""
    v = vivid_ext(world)
    echoes = v.get("teaching_echoes") or []
    hit = None
    for e in echoes:
        if e.get("for") == character_id and not e.get("consumed"):
            hit = e
            break
    if not hit:
        return ""
    hit["consumed"] = True
    topic = hit.get("topic") or "a local lesson"
    teacher = hit.get("teacher_name") or _nm(hit.get("teacher_id", ""), None, world)
    place = hit.get("place") or "nearby"
    return (
        "# A lesson overheard nearby\n"
        f"Secondhand only: while near {place}, you caught the edge of a lesson "
        f"from {teacher} on \"{topic}\". You did not sit the lesson yourself — "
        "hold it as something in the air, Amphoreus-framed, never as outworld knowledge."
    )


# --------------------------------------------------------------------------- #
# Map hour vignette
# --------------------------------------------------------------------------- #
def map_hour_vignette(world, place: str) -> str:
    """One literary clause for Map popup. Cap ~180 chars."""
    place = place or "Okhema"
    bits: List[str] = []
    try:
        from . import lived_mechanisms as lm
        lines = lm.visitor_stage_lines(world, place=place) or []
        if lines:
            bits.append(str(lines[0]).strip().rstrip("."))
    except Exception:
        pass
    if not bits:
        try:
            from . import ecosystem as eco
            scene = eco.derive_scene(world, place=place, include_residents=False) or []
            for being in scene[:3]:
                kind = being.get("kind") or being.get("id") or ""
                status = being.get("status") or being.get("doing") or ""
                if kind:
                    bits.append(
                        f"{str(kind).replace('_', ' ')} "
                        f"{str(status).strip()}".strip()
                    )
                    break
        except Exception:
            pass
    if not bits:
        try:
            weather = world.ambient_weather(place) or ""
            period = world.clock.period_name
            if weather:
                bits.append(f"{period} in {place}; {weather}")
            else:
                bits.append(f"{period} in {place} — the hour keeps its own counsel")
        except Exception:
            bits.append(f"The hour in {place} keeps its own counsel")
    text = bits[0]
    if not text.endswith((".", "…")):
        text = text + "."
    if len(text) > 180:
        text = text[:177].rstrip() + "…"
    return text
