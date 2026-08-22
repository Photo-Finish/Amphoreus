# -*- coding: utf-8 -*-
"""Deterministic checks for Stage-2 ensemble injectors + speech sanitize.

No LLM. Covers society_life / group prompt blocks that Visit and gatherings
wire in, plus spoken_words stripping of sample group narration lines.

    python tools/test_ensemble_injectors.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.core.speech_sanitize import spoken_words, has_self_narration
from src.world.world_state import WorldState
from src.world.sanctuary_clock import PERIODS_PER_DAY
from src.world import society_life as sl
from src.world import resident_memory as rm
from src.world import world_events as wev
from src.world.group_chat import group_prompt_block

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def _name_of(cid: str) -> str:
    return {
        "phainon": "Phainon",
        "mydei": "Mydei",
        "aglaea": "Aglaea",
        "tribbie": "Tribbie",
        "anaxa": "Anaxa",
        "hyacine": "Hyacine",
        "cipher": "Cipher",
    }.get(cid, cid)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="amp-ens-"))
    state_path = tmp / "world_state.json"
    os.environ["AMPHOREUS_STATE_PATH"] = str(state_path)
    ws = WorldState(str(state_path))
    ws.time_scale = 2.0
    ws.ambient = {
        "weather": {"Okhema": "clear and bright, the Dawn Device steady"},
        "news": "The Dawn Device holds.",
    }

    print("== group_prompt_block ==")
    gpb = group_prompt_block(
        "phainon",
        ["phainon", "mydei", "aglaea"],
        "Okhema",
        _name_of,
        recent=[
            {"role": "user", "content": "What do you make of the road?"},
            {"speaker": "mydei", "content": "The spears stay sharp."},
        ],
        own_prior=["I will keep the square."],
    )
    check("group prompt non-empty", len(gpb) > 40, gpb[:60])
    check("group prompt gathering header",
          "gathering" in gpb.lower() and "not alone" in gpb.lower(), gpb[:80])
    check("group prompt names company", "Mydei" in gpb and "Aglaea" in gpb, gpb[:120])
    check("group prompt keeps wall cue", "knowledge of Amphoreus" in gpb, gpb[:160])

    print("== walk_in ==")
    wev.compose_letter(
        ws, "tribbie", "phainon",
        "The gates asked a question only you can answer.",
    )
    letter = sl.walk_in_scene(ws, "phainon", name_of=_name_of)
    wp = sl.walk_in_prompt(letter)
    check("walk_in letter prompt non-empty",
          bool(wp) and "letter" in wp.lower(), wp[:100])
    check("walk_in ui_summary non-empty",
          bool(letter.get("ui_summary")), str(letter.get("ui_summary"))[:80])

    print("== bond_weather ==")
    ws.set_location("phainon", "Okhema")
    ws.set_location("mydei", "Okhema")
    bw = sl.bond_weather_block(ws, "phainon", name_of=_name_of)
    check("bond_weather non-empty for pair",
          "Bond weather" in bw and len(bw) > 20, bw[:120])

    print("== shared_gathering ==")
    sl.note_shared_gathering(
        ws,
        members=["phainon", "mydei", "aglaea"],
        place="Okhema",
        snippets=["spears rested; bread passed"],
    )
    sg = sl.shared_gathering_prompt(ws, "phainon", name_of=_name_of)
    check("shared_gathering prompt non-empty",
          "shared hour" in sg.lower() and "Okhema" in sg, sg[:100])

    print("== absence (>=5 days) ==")
    ws.vivid["visitor_absences"] = {}
    sl.note_visit_touch(ws, "phainon")
    ws.clock.advance(7 * PERIODS_PER_DAY)
    ab = sl.absence_prompt_block(ws, "phainon")
    check("absence prompt after 7 days",
          "visitor returns after absence" in ab.lower() and len(ab) > 40,
          ab[:100])

    print("== eco_notice ==")
    ws.set_location("phainon", "Okhema")
    sl.record_eco_notice(
        world=ws,
        place="Okhema",
        object_id="chimera-okhema-1",
        kind="care",
        line="A chimera leaned into an offered hand by the square.",
        visitor_action="pet",
        heir_hint="the visitor cared for a chimera here",
    )
    ep = sl.eco_notice_prompt(ws, "phainon")
    check("eco_notice prompt non-empty",
          "What the land already showed" in ep and "chimera" in ep.lower(),
          ep[:120])

    print("== teaching echo skip earth ==")
    ws.set_location("anaxa", "Grove of Epiphany")
    ws.set_location("hyacine", "Grove of Epiphany")
    skip = sl.maybe_echo_teaching(
        ws, "anaxa", "python programming on Earth", "Grove of Epiphany",
    )
    check("teaching echo skips earth topic", skip == [])
    ok_echo = sl.maybe_echo_teaching(
        ws, "anaxa", "the Coreflame of Reason", "Grove of Epiphany",
    )
    check("teaching echo allows amphoreus topic",
          len(ok_echo) >= 1 and ok_echo[0].get("for") == "hyacine",
          str(ok_echo))
    te = sl.teaching_echo_prompt(ws, "hyacine")
    check("teaching echo prompt non-empty",
          "secondhand" in te.lower() or "lesson overheard" in te.lower(),
          te[:100])

    print("== map vignette ==")
    vg = sl.map_hour_vignette(ws, "Okhema")
    check("map vignette non-empty", bool(vg) and len(vg) > 8, vg)
    check("map vignette capped <=180", len(vg) <= 180, str(len(vg)))

    print("== resident_memory recognition after two meets ==")
    rec1 = rm.remember_meeting(
        ws, "okhema-ens-npc", name="Lysa", city="Okhema", line="Hello.")
    rec2 = rm.remember_meeting(
        ws, "okhema-ens-npc", name="Lysa", city="Okhema", line="Again.")
    check("two meets recorded",
          rec1.get("meets") == 1 and rec2.get("meets") == 2, str(rec2))
    recog = rm.recognition_line(
        ws, {"id": "okhema-ens-npc", "name": "Lysa", "city": "Okhema"})
    check("recognition after two meets",
          recog is not None and (
              "Back again" in recog
              or "Welcome back" in recog
              or "familiar" in recog.lower()
          ),
          repr(recog))

    print("== speech_sanitize on sample group lines ==")
    group_line = (
        '"Of course," I reply with a nod to Mydei. "The black tide waits."'
    )
    check("sample group line is narration", has_self_narration(group_line))
    cleaned = spoken_words(group_line)
    check("sanitize keeps spoken content",
          "Of course" in cleaned and "black tide" in cleaned, cleaned)
    check("sanitize strips reply tag",
          "I reply" not in cleaned and "nod to Mydei" not in cleaned, cleaned)
    astr = spoken_words("*smiles at Tribbie* The threads hum tonight.")
    check("sanitize strips asterisk beat",
          "threads hum" in astr and "*" not in astr, astr)
    fp = spoken_words("I went to Okhema yesterday.")
    check("sanitize keeps first-person travel",
          "I went to Okhema yesterday" in fp, fp)

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        for n in FAILED:
            print(f"  - {n}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
