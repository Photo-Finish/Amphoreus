# -*- coding: utf-8 -*-
"""Cyrene year cycle — three-block picture/talk lookup (unwired).

Same sanctuary Light Calendar as `sanctuary_clock.py` (months 1..13;
Uncounted = 0). Pictures surject onto {childhood, demiurge, mem}.
Whisper always uses character id ``cyrene``; Mem has no talk card.

Not imported by Eternal Page, Visit UI, or character cards. Art keys TBD.
Spec: docs/CYRENE-CYCLE.md
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

TALK_ID = "cyrene"

FACE_CHILDHOOD = "childhood"
FACE_DEMIURGE = "demiurge"
FACE_MEM = "mem"
FACES = (FACE_CHILDHOOD, FACE_DEMIURGE, FACE_MEM)

PERSONA_CHILDHOOD = "childhood"
PERSONA_DEMIURGE = "demiurge"

BLOCK_VILLAGE = "village"
BLOCK_PAGE = "page"
BLOCK_FAIRY = "fairy"
BLOCKS = (BLOCK_VILLAGE, BLOCK_PAGE, BLOCK_FAIRY)


def _month_index(month) -> int:
    """1..13 counted months; 0 = Uncounted. Out-of-range clamps to the year."""
    try:
        m = int(month)
    except (TypeError, ValueError):
        return 0
    if m < 0:
        return 0
    if m > 13:
        return 13
    return m


def month_from_clock(clock) -> int:
    """Read sanctuary clock month numbering; Uncounted → 0."""
    if clock is None:
        return 0
    if getattr(clock, "uncounted", None):
        return 0
    return _month_index(getattr(clock, "month", 0) or 0)


def visual_face(month: int) -> str:
    """Picture for Light month 1..13 (0 = Uncounted → Fairy / mem).

    Uncounted must not fall through ``month <= 6`` into childhood.
    """
    m = _month_index(month)
    if m <= 0 or m >= 12:
        return FACE_MEM
    if m <= 6:
        return FACE_CHILDHOOD
    return FACE_DEMIURGE


def talk_target(month: int) -> str:
    """Always the Cyrene card. Never ``mem``."""
    _month_index(month)  # validate / clamp; id does not depend on month
    return TALK_ID


def talk_persona(month: int) -> str:
    """Demiurge register only while the picture is Demiurge; else childhood.

    Fairy (Mem picture) still whispers as childhood Cyrene (sleeper/writer).
    """
    if visual_face(month) == FACE_DEMIURGE:
        return PERSONA_DEMIURGE
    return PERSONA_CHILDHOOD


def block_of(month: int) -> str:
    """Village / Page / Fairy from the same month index."""
    m = _month_index(month)
    if m <= 0 or m >= 12:
        return BLOCK_FAIRY
    if m <= 6:
        return BLOCK_VILLAGE
    return BLOCK_PAGE


def whisper_open(month: int) -> bool:
    """Whisper stays on in every block, including when the picture is Mem."""
    _month_index(month)
    return True


def mem_companion_ok(_month: int = 0) -> bool:
    """Mute Mem may sit beside the occupant in any block."""
    return True


@dataclass(frozen=True)
class CyreneSlot:
    """Resolved Cyrene-seat occupancy for one Light-Calendar date."""

    month: int
    block: str
    visual_face: str
    talk_target: str
    talk_persona: str
    whisper: bool = True

    def as_dict(self) -> dict:
        return {
            "month": self.month,
            "block": self.block,
            "visual_face": self.visual_face,
            "talk_target": self.talk_target,
            "talk_persona": self.talk_persona,
            "whisper": self.whisper,
        }


def slot_for_month(month: int) -> CyreneSlot:
    m = _month_index(month)
    return CyreneSlot(
        month=m,
        block=block_of(m),
        visual_face=visual_face(m),
        talk_target=talk_target(m),
        talk_persona=talk_persona(m),
        whisper=whisper_open(m),
    )


def from_clock(clock) -> CyreneSlot:
    """Resolve from a `WorldClock` (or any object with month / uncounted)."""
    return slot_for_month(month_from_clock(clock))


def from_civil_date(d) -> CyreneSlot:
    """Gregorian date → overlay clock → slot (Gate = 1 January)."""
    from src.world.sanctuary_clock import WorldClock

    return from_clock(WorldClock.from_civil_date(d))


def from_gmt8(when: Optional[object] = None) -> CyreneSlot:
    """1× overlay 'now' (GMT+8) → slot."""
    from src.world.sanctuary_clock import WorldClock

    return from_clock(WorldClock.from_gmt8(when))
