# -*- coding: utf-8 -*-
"""Cyrene's year cycle — the picture she holds and the register she speaks in.

`src/world/cyrene_cycle.py` resolves which face occupies her seat for a Light
month (childhood / demiurge / mem) and which persona the whisper should follow.
This module binds that answer to the two things a page needs:

* **a face file** — her own Pom-Pom Gallery poses for the two speaking forms,
  and Mem's official still while the fairy holds the seat (the mute companion,
  who still leaves the whisper to childhood Cyrene);
* **a register hint** — one short paragraph handed to
  `manager.chat(extra_system=...)`, so her voice follows the writer rather than
  becoming a second character.

Rules from `docs/CYRENE-CYCLE.md` kept here:

* the talk target is always the Cyrene card — Mem never speaks, and no `mem`
  speaker id is invented;
* the hint is a **register**, not a re-identification: it never says "this month
  you are Mem", never mentions models, and never opens the knowledge wall;
* a missing or tiny art file falls back to the normal Cyrene pose, so the page
  still draws if the catalog is trimmed.

Nothing here writes memory, world state, or a character card.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.world import cyrene_cycle as cycle

ROOT = Path(__file__).resolve().parents[2]
CUTE = ROOT / "assets" / "eternal_page" / "cute"
FORMS = ROOT / "assets" / "eternal_page" / "cyrene_forms"

# Form → the official still that stands for it. Childhood and Demiurge are her
# own PPG poses (canon: `cute/cyrene/05.png` is the navy-dress child,
# `02.png` the adult look); Mem is the official fairy artwork.
FACE_BY_FORM: dict[str, Path] = {
    cycle.FACE_CHILDHOOD: CUTE / "cyrene" / "05.png",
    cycle.FACE_DEMIURGE: CUTE / "cyrene" / "02.png",
    cycle.FACE_MEM: FORMS / "mem" / "ppg23_03_sleep.png",
}

# A register, not a second person: it names the voice to use and forbids
# announcing it. `src/characters/cyrene.json` already carries both voices.
_REGISTER = {
    cycle.PERSONA_CHILDHOOD: (
        "Register for this reply: the girl who writes — warm, quick, playful, a "
        "little wry, short sentences, curiosity leading. This is your own voice, "
        "not another person's. Do not announce or explain the register."
    ),
    cycle.PERSONA_DEMIURGE: (
        "Register for this reply: the Demiurge — serene, measured, unhurried, "
        "with the weight of the long war behind the calm. This is your own voice, "
        "not another person's. Do not announce or explain the register."
    ),
}

MIN_BYTES = 4000


def current_slot(world=None) -> cycle.CyreneSlot:
    """The seat for 'now', following the sanctuary clock (1× and 2×–60× alike).

    Falls back to the Fairy seat rather than raising: a page must draw even when
    the persisted world state is unreadable.
    """
    try:
        if world is None:
            from src.world.world_state import WorldState

            world = WorldState()
        clock = getattr(world, "clock", None)
        if clock is not None:
            return cycle.from_clock(clock)
    except Exception:
        pass
    return cycle.slot_for_month(0)


def face_path(form: Optional[str]) -> Optional[Path]:
    """The still for a form, or None to keep the usual Cyrene pose."""
    path = FACE_BY_FORM.get(str(form or ""))
    if path is not None and path.is_file() and path.stat().st_size > MIN_BYTES:
        return path
    return None


def register_for(persona: Optional[str]) -> str:
    """The register hint for a persona, or '' when there is nothing to say."""
    return _REGISTER.get(str(persona or ""), "")


def speak_hint(character_id: str, slot: Optional[cycle.CyreneSlot]) -> str:
    """What to append for this speaker on this date — '' for everyone but Cyrene."""
    if character_id != cycle.TALK_ID or slot is None:
        return ""
    return register_for(slot.talk_persona)


def whole_year() -> list[dict]:
    """The three blocks as one table — used by the suite and by the docs check."""
    rows = []
    for month in range(0, 14):  # 0 = Uncounted, 1..13 = the counted months
        slot = cycle.slot_for_month(month)
        face = face_path(slot.visual_face)
        rows.append(
            {
                "month": month,
                "block": slot.block,
                "visual_face": slot.visual_face,
                "talk_target": slot.talk_target,
                "talk_persona": slot.talk_persona,
                "face": face.name if face else "",
            }
        )
    return rows
