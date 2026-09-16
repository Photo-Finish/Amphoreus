# -*- coding: utf-8 -*-
"""An Eternal Page — Beyond Time memory-space (not a map city).

Official setting: the Trailblazer may speak with every Chrysos Heir on
As I've Written / Beyond Time: An Eternal Page. This module is the
sanctuary's circle logic: who stands near, who answers, and how that
talk writes the same per-Heir history Visit uses.

No weather, no ecosystem, no roads. Cute Heir companions only.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Iterable, Optional

from src.core.heir_folders import HEIR_FOLDERS

ROOT = Path(__file__).resolve().parents[2]
ART_DIR = ROOT / "assets" / "eternal_page" / "cute"
# Official Area_Vortex_of_Genesis art: starfield + cosmic swirl.
# bg-beyond-time.jpg is the Exotale garden plaza (Visit/Walk land), not this page.
PARCHMENT = ROOT / "assets" / "galgame" / "ground" / "bg-vortex-of-genesis.jpg"

# Cyrene keeps the page; the others stand in an arc around her.
CIRCLE: tuple[str, ...] = (
    "tribbie",
    "aglaea",
    "anaxa",
    "hyacine",
    "castorice",
    "cipher",
    "cyrene",
    "phainon",
    "mydei",
    "cerydra",
    "hysilens",
    "evernight",
    "dan-heng-permansor-terrae",
)

SHORT_NAME = {
    "aglaea": "Aglaea",
    "anaxa": "Anaxa",
    "castorice": "Castorice",
    "cerydra": "Cerydra",
    "cipher": "Cipher",
    "cyrene": "Cyrene",
    "dan-heng-permansor-terrae": "Dan Heng",
    "evernight": "Evernight",
    "hyacine": "Hyacine",
    "hysilens": "Hysilens",
    "mydei": "Mydei",
    "phainon": "Phainon",
    "tribbie": "Tribbie",
}

# left%, bottom% — two rows on the parchment (desktop-buddy sill).
LAYOUT: dict[str, tuple[float, float]] = {
    "tribbie": (8.0, 40.0),
    "aglaea": (22.0, 34.0),
    "anaxa": (36.0, 30.0),
    "hyacine": (50.0, 28.0),
    "castorice": (64.0, 30.0),
    "cipher": (78.0, 34.0),
    "cyrene": (46.0, 62.0),
    "phainon": (18.0, 66.0),
    "mydei": (32.0, 72.0),
    "cerydra": (60.0, 72.0),
    "hysilens": (74.0, 66.0),
    "evernight": (88.0, 58.0),
    "dan-heng-permansor-terrae": (6.0, 58.0),
}

MAX_SPEAKERS_DEFAULT = 4
STATE_SELECTED = "amp_eternal_selected"
STATE_BUBBLES = "amp_eternal_bubbles"
STATE_ROTATE = "amp_eternal_rotate"
STATE_EVERYONE = "amp_eternal_everyone"
STATE_LAYOUT = "amp_eternal_layout"
STATE_CMD = "amp_eternal_cmd"

SpeakFn = Callable[[str, str], str]
NameFn = Callable[[str], str]


def all_ids() -> list[str]:
    return [cid for cid in CIRCLE if cid in HEIR_FOLDERS]


def short_name(character_id: str) -> str:
    return SHORT_NAME.get(character_id, character_id.replace("-", " ").title())


def cute_art(character_id: str, emotion: Optional[str] = None) -> Optional[Path]:
    try:
        from src.world.eternal_emotion import pose_path
        posed = pose_path(character_id, emotion)
        if posed is not None:
            return posed
    except Exception:
        pass
    path = ART_DIR / f"{character_id}.png"
    if path.is_file() and path.stat().st_size > 4000:
        return path
    return None


def parchment_path() -> Optional[Path]:
    if PARCHMENT.is_file() and PARCHMENT.stat().st_size > 8000:
        return PARCHMENT
    return None


def art_missing() -> list[str]:
    return [cid for cid in all_ids() if cute_art(cid) is None]


def normalize_selected(selected: Optional[Iterable[str]]) -> list[str]:
    wanted = {str(s).strip() for s in (selected or []) if str(s).strip()}
    return [cid for cid in all_ids() if cid in wanted]


def toggle_member(selected: Optional[Iterable[str]], character_id: str) -> list[str]:
    cur = normalize_selected(selected)
    if character_id not in all_ids():
        return cur
    if character_id in cur:
        return [c for c in cur if c != character_id]
    return normalize_selected(cur + [character_id])


def solo_member(character_id: str) -> list[str]:
    if character_id in all_ids():
        return [character_id]
    return []


def place_of(character_id: str, overlay: Optional[dict] = None) -> tuple[float, float]:
    ov = overlay or {}
    pair = ov.get(character_id) if isinstance(ov, dict) else None
    if pair is not None:
        try:
            left, bottom = float(pair[0]), float(pair[1])
            return clamp_place(left, bottom)
        except Exception:
            pass
    return LAYOUT.get(character_id, (50.0, 50.0))


def clamp_place(left: float, bottom: float) -> tuple[float, float]:
    return max(4.0, min(96.0, float(left))), max(8.0, min(88.0, float(bottom)))


def move_companion(overlay: Optional[dict], character_id: str, left: float, bottom: float) -> dict:
    out = dict(overlay or {})
    if character_id not in all_ids():
        return out
    out[character_id] = list(clamp_place(left, bottom))
    return out


def pet_companion(character_id: str, world=None) -> bool:
    """A touch on the page — warms mood, never authors Heir speech."""
    if character_id not in all_ids():
        return False
    if world is None:
        try:
            from src.world.world_state import WorldState
            world = WorldState()
        except Exception:
            world = None
    if world is None:
        return True
    try:
        from src.world import living_world as lw
        lw.set_mood(world, character_id, 1, "a gentle touch on the Eternal Page")
    except Exception:
        m = getattr(world, "mood", None)
        if not isinstance(m, dict):
            world.mood = {}
            m = world.mood
        cur = m.get(character_id) or {}
        try:
            valence = int(cur.get("valence", 0) or 0) + 1
        except Exception:
            valence = 1
        valence = max(-3, min(3, valence))
        ts = ""
        try:
            ts = world.clock.format_short()
        except Exception:
            ts = str(cur.get("ts") or "")
        m[character_id] = {
            "valence": valence,
            "reason": "a gentle touch on the Eternal Page",
            "ts": ts,
        }
    try:
        world.save()
    except Exception:
        pass
    return True


def parse_command(raw: str) -> Optional[tuple]:
    """Parse a parent-bridge command: click/solo/pet/drag."""
    text = str(raw or "").strip()
    if not text:
        return None
    parts = text.split(":")
    kind = (parts[0] or "").strip().lower()
    cid = (parts[1] if len(parts) > 1 else "").strip()
    if kind not in {"click", "solo", "pet", "drag"}:
        return None
    if cid not in all_ids():
        return None
    if kind == "drag":
        try:
            left = float(parts[2])
            bottom = float(parts[3])
        except Exception:
            return None
        return ("drag", cid, left, bottom)
    return (kind, cid)


def _mentions(text: str, selected: list[str]) -> list[str]:
    blob = f" {text.lower()} "
    hits = []
    for cid in selected:
        names = {cid.replace("-", " "), short_name(cid).lower()}
        if cid == "dan-heng-permansor-terrae":
            names.update({"dan heng", "permansor", "terrae"})
        if cid == "anaxa":
            names.add("anaxagoras")
        if cid == "mydei":
            names.add("mydeimos")
        if cid == "tribbie":
            names.update({"tribbios", "trianne", "trinnon"})
        if any(re.search(rf"\b{re.escape(n)}\b", blob) for n in names if n):
            hits.append(cid)
    return hits


def pick_speakers(
    selected: Iterable[str],
    text: str = "",
    *,
    everyone: bool = False,
    rotate: int = 0,
    cap: int = MAX_SPEAKERS_DEFAULT,
) -> tuple[list[str], list[str]]:
    """Who answers this hour. Everyone selected still hears (listeners)."""
    members = normalize_selected(selected)
    if not members:
        return [], []
    if everyone or len(members) <= cap:
        return members, []
    named = _mentions(text, members)
    pool = named or members
    if named and len(named) <= cap:
        speakers = named
    else:
        start = abs(int(rotate)) % len(pool)
        ordered = pool[start:] + pool[:start]
        speakers = ordered[:cap]
        # Keep named Heirs in the answering set when possible.
        for cid in named:
            if cid not in speakers:
                speakers[-1] = cid
                speakers = normalize_selected(speakers)
    listeners = [c for c in members if c not in speakers]
    return speakers, listeners


def circle_prompt(members: list[str], speakers: list[str], name_of: Optional[NameFn] = None) -> str:
    def _nm(cid: str) -> str:
        if name_of:
            try:
                return name_of(cid)
            except Exception:
                pass
        return short_name(cid)

    near = ", ".join(_nm(c) for c in members) or "no one"
    answering = ", ".join(_nm(c) for c in speakers) or "no one"
    return (
        "# Where you are\n"
        "You stand on An Eternal Page — Beyond Time, the memory-space of "
        "As I've Written — not a city of Amphoreus. The star-stranger may "
        "speak to one of you, several, or all. There is no weather here, "
        "and no street. Reply only as yourself, a short spoken line, as if "
        "standing near the others on the page.\n"
        f"Standing near: {near}.\n"
        f"Answering this hour: {answering}.\n"
        "Do not speak another Heir's words. Do not mention Earth, machines, "
        "or that this is a program."
    )


def eternal_talk(
    manager,
    selected: Iterable[str],
    user_message: str,
    *,
    everyone: bool = False,
    rotate: int = 0,
    speak: Optional[SpeakFn] = None,
    name_of: Optional[NameFn] = None,
) -> dict:
    """Speak on the page. Speakers use Visit's `manager.chat` (shared history).

    Listeners receive the visitor's line in the same history.jsonl so a later
    Visit still remembers that they heard it. Journey / Aftermath framing is
    whatever `manager.chat` already injects from visitor_mode.
    """
    text = (user_message or "").strip()
    members = normalize_selected(selected)
    if not text:
        return {
            "ok": False,
            "reason": "empty",
            "members": members,
            "speakers": [],
            "listeners": [],
            "replies": [],
        }
    if not members:
        return {
            "ok": False,
            "reason": "none_near",
            "members": [],
            "speakers": [],
            "listeners": [],
            "replies": [],
        }

    speakers, listeners = pick_speakers(
        members, text, everyone=everyone, rotate=rotate
    )
    replies = []
    chat = speak
    if chat is None:
        chat = lambda cid, msg: manager.chat(cid, msg)

    for cid in speakers:
        line = str(chat(cid, text) or "").strip()
        replies.append(
            {
                "id": cid,
                "name": short_name(cid) if not name_of else (name_of(cid) or short_name(cid)),
                "text": line,
                "spoke": True,
            }
        )

    memory = getattr(manager, "memory", None)
    for cid in listeners:
        if memory is not None:
            try:
                memory.record_visit(cid)
            except Exception:
                pass
            try:
                memory.add_history(cid, "user", text)
            except Exception:
                pass
        replies.append(
            {
                "id": cid,
                "name": short_name(cid) if not name_of else (name_of(cid) or short_name(cid)),
                "text": "",
                "spoke": False,
            }
        )

    return {
        "ok": True,
        "reason": "ok",
        "members": members,
        "speakers": speakers,
        "listeners": listeners,
        "replies": replies,
        "next_rotate": int(rotate) + 1,
    }
