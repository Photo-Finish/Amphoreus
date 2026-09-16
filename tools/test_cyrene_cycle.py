# -*- coding: utf-8 -*-
"""Cyrene year cycle — three blocks, Mem mute, whisper always cyrene.

    python tools/test_cyrene_cycle.py
"""
from __future__ import annotations

import ast
import os
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.cyrene_cycle import (
    BLOCK_FAIRY,
    BLOCK_PAGE,
    BLOCK_VILLAGE,
    FACE_CHILDHOOD,
    FACE_DEMIURGE,
    FACE_MEM,
    FACES,
    TALK_ID,
    block_of,
    from_civil_date,
    from_clock,
    mem_companion_ok,
    month_from_clock,
    slot_for_month,
    talk_persona,
    talk_target,
    visual_face,
    whisper_open,
)
from src.world.sanctuary_clock import GMT8, UNC_ASTRORUM, UNC_SCARLET, WorldClock

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        extra = f"  {extra}" if extra else ""
        print(f"FAIL  {name}{extra}")


def main():
    print("== Month index lookup ==")
    expect_face = {
        1: FACE_CHILDHOOD, 2: FACE_CHILDHOOD, 3: FACE_CHILDHOOD,
        4: FACE_CHILDHOOD, 5: FACE_CHILDHOOD, 6: FACE_CHILDHOOD,
        7: FACE_DEMIURGE, 8: FACE_DEMIURGE, 9: FACE_DEMIURGE,
        10: FACE_DEMIURGE, 11: FACE_DEMIURGE,
        12: FACE_MEM, 13: FACE_MEM, 0: FACE_MEM,
    }
    expect_block = {
        1: BLOCK_VILLAGE, 6: BLOCK_VILLAGE,
        7: BLOCK_PAGE, 11: BLOCK_PAGE,
        12: BLOCK_FAIRY, 13: BLOCK_FAIRY, 0: BLOCK_FAIRY,
    }
    for month, face in expect_face.items():
        check(f"visual_face({month}) = {face}", visual_face(month) == face,
              visual_face(month))
        persona = FACE_DEMIURGE if face == FACE_DEMIURGE else FACE_CHILDHOOD
        check(f"talk_persona({month}) = {persona}",
              talk_persona(month) == persona, talk_persona(month))
        check(f"talk_target({month}) = cyrene", talk_target(month) == TALK_ID)
        check(f"whisper({month}) on", whisper_open(month) is True)
    for month, block in expect_block.items():
        check(f"block({month}) = {block}", block_of(month) == block, block_of(month))

    check("Uncounted is not childhood", visual_face(0) != FACE_CHILDHOOD)
    check("naive <=6 must not win for 0", visual_face(0) == FACE_MEM)
    check("surjection hits all three faces",
          {visual_face(m) for m in range(0, 14)} == set(FACES))
    check("talk_target never mem",
          all(talk_target(m) != "mem" for m in range(0, 14)))
    check("Fairy persona is childhood (sleeper)",
          talk_persona(0) == FACE_CHILDHOOD and talk_persona(12) == FACE_CHILDHOOD)
    check("mute Mem ok in Village", mem_companion_ok(1) is True)
    check("mute Mem ok in Page", mem_companion_ok(9) is True)
    check("mute Mem ok in Fairy", mem_companion_ok(0) is True)

    print("== Clock numbering (1..13, Uncounted = 0) ==")
    gate = WorldClock(year=4933, month=1, week=1, day=1)
    weave = WorldClock(year=4933, month=9, week=1, day=1)
    fortune = WorldClock(year=4933, month=12, week=1, day=1)
    membrance = WorldClock(year=4933, month=13, week=4, day=7)
    scarlet = WorldClock(year=4935, month=12, week=4, day=7, uncounted=UNC_SCARLET)
    astrorum = WorldClock(year=4933, month=13, week=4, day=7, uncounted=UNC_ASTRORUM)
    check("Gate month_from_clock = 1", month_from_clock(gate) == 1)
    check("Weaving (default sim month) is Page/demiurge",
          from_clock(weave).visual_face == FACE_DEMIURGE
          and from_clock(weave).block == BLOCK_PAGE)
    check("Fortune counted is Fairy/mem", from_clock(fortune).visual_face == FACE_MEM)
    check("Membrance is Fairy/mem", from_clock(membrance).visual_face == FACE_MEM)
    check("Scarlet Uncounted is month 0", month_from_clock(scarlet) == 0)
    check("Dies Astrorum is month 0", month_from_clock(astrorum) == 0)
    check("Scarlet picture is mem, talk cyrene/childhood",
          from_clock(scarlet).visual_face == FACE_MEM
          and from_clock(scarlet).talk_target == "cyrene"
          and from_clock(scarlet).talk_persona == FACE_CHILDHOOD
          and from_clock(scarlet).whisper is True)
    check("Astrorum same Fairy slot",
          from_clock(astrorum).block == BLOCK_FAIRY
          and from_clock(astrorum).talk_target == "cyrene")

    print("== Common civil 2026 (4933) ==")
    table_2026 = [
        (date(2026, 1, 1), BLOCK_VILLAGE, FACE_CHILDHOOD, FACE_CHILDHOOD),
        (date(2026, 6, 17), BLOCK_VILLAGE, FACE_CHILDHOOD, FACE_CHILDHOOD),
        (date(2026, 6, 18), BLOCK_PAGE, FACE_DEMIURGE, FACE_DEMIURGE),
        (date(2026, 11, 4), BLOCK_PAGE, FACE_DEMIURGE, FACE_DEMIURGE),
        (date(2026, 11, 5), BLOCK_FAIRY, FACE_MEM, FACE_CHILDHOOD),
        (date(2026, 12, 30), BLOCK_FAIRY, FACE_MEM, FACE_CHILDHOOD),
        (date(2026, 12, 31), BLOCK_FAIRY, FACE_MEM, FACE_CHILDHOOD),
    ]
    for d, block, face, persona in table_2026:
        slot = from_civil_date(d)
        check(f"{d.isoformat()} {block}/{face}",
              slot.block == block and slot.visual_face == face
              and slot.talk_persona == persona and slot.talk_target == "cyrene"
              and slot.whisper is True,
              slot.as_dict())

    print("== Leap civil 2028 (4935) ==")
    table_2028 = [
        (date(2028, 6, 16), BLOCK_VILLAGE, FACE_CHILDHOOD),
        (date(2028, 6, 17), BLOCK_PAGE, FACE_DEMIURGE),
        (date(2028, 11, 3), BLOCK_PAGE, FACE_DEMIURGE),
        (date(2028, 11, 4), BLOCK_FAIRY, FACE_MEM),
        (date(2028, 12, 2), BLOCK_FAIRY, FACE_MEM),  # Scarlet Day
        (date(2028, 12, 31), BLOCK_FAIRY, FACE_MEM),
    ]
    for d, block, face in table_2028:
        slot = from_civil_date(d)
        clk = WorldClock.from_civil_date(d)
        check(f"{d.isoformat()} leap {block}/{face}",
              slot.block == block and slot.visual_face == face
              and slot.talk_target == "cyrene",
              f"{slot.as_dict()} clock={clk.format_short()}")
    scarlet_d = WorldClock.from_civil_date(date(2028, 12, 2))
    check("2 Dec 2028 is Scarlet Uncounted", scarlet_d.uncounted == UNC_SCARLET)

    print("== 1x GMT+8 helper returns a slot ==")
    now_slot = from_clock(WorldClock.from_gmt8(
        datetime(2026, 8, 18, 12, 0, tzinfo=GMT8)))
    check("18 Aug 2026 Weaving is Page",
          now_slot.block == BLOCK_PAGE and now_slot.visual_face == FACE_DEMIURGE,
          now_slot.as_dict())
    check("slot_for_month matches visual_face",
          slot_for_month(7).visual_face == visual_face(7))

    print("== Unwired: no UI / Eternal Page imports in the module ==")
    src = (ROOT / "src" / "world" / "cyrene_cycle.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(a.name.split(".", 1)[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module.split(".", 1)[0])
    banned = {"streamlit", "ui_eternal_page", "ui_app", "src.ui_eternal_page"}
    check("no Streamlit / talk-UI import",
          not any(n in banned or n.startswith("src.ui") for n in imported)
          and "streamlit" not in src
          and "eternal_page" not in src
          and "ui_eternal" not in src,
          str(imported))
    check("does not mention mem as talk id in talk_target body",
          talk_target(13) == "cyrene")

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILED:", ", ".join(FAILED))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
