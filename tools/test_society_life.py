# -*- coding: utf-8 -*-
"""Deterministic checks for Stage-2 society_life continuity.

No LLM / Streamlit. Uses tempfile WorldState like test_vivid_stage2.py.

    python tools/test_society_life.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.world_state import WorldState
from src.world.sanctuary_clock import PERIODS_PER_DAY
from src.world import society_life as sl
from src.world import world_events as wev

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


class _FakeMemory:
    def __init__(self):
        self.rows = []

    def add_memory(self, character_id, mtype, content, importance=2):
        self.rows.append({
            "character_id": character_id,
            "mtype": mtype,
            "content": content,
            "importance": importance,
        })


class _FakeManager:
    def __init__(self):
        self.memory = _FakeMemory()


def main():
    tmp = Path(tempfile.mkdtemp(prefix="amp-soc-"))
    state_path = tmp / "world_state.json"
    os.environ["AMPHOREUS_STATE_PATH"] = str(state_path)
    ws = WorldState(str(state_path))
    ws.time_scale = 2.0
    name_of = lambda c: {
        "phainon": "Phainon", "mydei": "Mydei", "aglaea": "Aglaea",
        "tribbie": "Tribbie", "anaxa": "Anaxa", "hyacine": "Hyacine",
    }.get(c, c)

    print("== vivid_ext ==")
    v = sl.vivid_ext(ws)
    for key in (
        "shared_gatherings", "eco_notices", "visitor_absences",
        "resident_memory", "teaching_echoes",
    ):
        check(f"vivid has {key}", key in v)

    print("== Item 2 shared gatherings ==")
    payload = sl.note_shared_gathering(
        ws,
        members=["phainon", "mydei", "aglaea"],
        place="Okhema",
        snippets=["spears rested; bread passed"],
        clock_label="test-hour",
    )
    check("note returns payload", payload.get("place") == "Okhema")
    check("gathering stored",
          len(ws.vivid["shared_gatherings"]) == 1)
    check("payload has members", "phainon" in payload["members"])
    pg = sl.shared_gathering_prompt(ws, "phainon", name_of=name_of)
    check("member gets shared-hour prompt",
          "A shared hour you remember" in pg, pg[:80])
    check("member prompt names place", "Okhema" in pg)
    pg_out = sl.shared_gathering_prompt(ws, "cipher", name_of=name_of)
    check("non-member gets empty prompt", pg_out == "")
    # Cap
    for i in range(30):
        sl.note_shared_gathering(
            ws, members=["phainon"], place="Okhema",
            snippets=[f"s{i}"],
        )
    check("gatherings capped ~24",
          len(ws.vivid["shared_gatherings"]) <= 24,
          str(len(ws.vivid["shared_gatherings"])))
    # Memories
    mgr = _FakeManager()
    sl.promote_gathering_to_memories(
        mgr,
        members=["phainon", "mydei"],
        place="Okhema",
        snippets=["the square held a quiet laugh"],
    )
    check("promote wrote two memories", len(mgr.memory.rows) == 2)
    check("promote mtype moment",
          all(r["mtype"] == "moment" for r in mgr.memory.rows))
    check("promote importance 2",
          all(r["importance"] == 2 for r in mgr.memory.rows))
    check("promote one-liner not full dump",
          all(len(r["content"]) < 200 for r in mgr.memory.rows))

    print("== Item 3+4 walk-in ==")
    ws.letters = []
    quiet = sl.walk_in_scene(ws, "phainon", chronicle_tail=None, name_of=name_of)
    check("quiet when nothing pending", quiet.get("kind") == "quiet")
    check("quiet prompt empty", sl.walk_in_prompt(quiet) == "")

    wev.compose_letter(
        ws, "tribbie", "phainon",
        "The gates asked a question only you can answer.",
    )
    letter = sl.walk_in_scene(ws, "phainon", name_of=name_of)
    check("letter_open kind", letter.get("kind") == "letter_open", str(letter))
    check("letter has from_name", bool(letter.get("from_name")))
    check("letter has excerpt", "gates" in (letter.get("excerpt") or ""))
    check("letter interrupted flag", letter.get("interrupted") is True)
    check("letter ui_summary", "mid-letter" in (letter.get("ui_summary") or "").lower()
          or "letter" in (letter.get("ui_summary") or "").lower())
    wp = sl.walk_in_prompt(letter)
    check("letter prompt non-empty", "letter" in wp.lower() and "interrupted" in wp.lower())

    # Clear letter so encounter path is visible
    ws.letters = []
    chron = [{
        "kind": "encounter",
        "text": "Phainon and Mydei trade practice blows in the square.",
    }]
    talk = sl.walk_in_scene(ws, "phainon", chronicle_tail=chron, name_of=name_of)
    check("heir_talk when two named", talk.get("kind") == "heir_talk", str(talk))
    check("heir_talk prompt mentions company",
          "mid-talk" in (talk.get("prompt_block") or "").lower()
          or "company" in (talk.get("prompt_block") or "").lower())

    chron2 = [{
        "kind": "encounter",
        "text": "A merchant carts figs past the Dawn Device.",
    }]
    mid = sl.walk_in_scene(ws, "phainon", chronicle_tail=chron2, name_of=name_of)
    check("encounter_mid without second heir",
          mid.get("kind") == "encounter_mid", str(mid))

    print("== Item 6 bond weather ==")
    ws.set_location("phainon", "Okhema")
    ws.set_location("mydei", "Okhema")
    ws.set_location("aglaea", "Okhema")
    bw = sl.bond_weather_block(ws, "phainon", name_of=name_of)
    check("phainon+mydei bond weather",
          "Bond weather" in bw and ("sparring" in bw.lower() or "rival" in bw.lower()),
          bw[:120])
    ws.set_location("mydei", "Castrum Kremnos")
    ws.set_location("aglaea", "Janusopolis")
    # Ensure no other bond pair co-located with phainon
    for cid in list(ws.agent_location):
        if cid != "phainon":
            # leave only phainon in Okhema among bond-pair mates
            if ws.location_name(cid) == "Okhema":
                ws.set_location(cid, "Aidonia")
    ws.set_location("phainon", "Okhema")
    alone = sl.bond_weather_block(ws, "phainon", name_of=name_of)
    check("alone: no bond weather", alone == "", alone[:80])

    # warmer delta fallback
    ws.set_location("cipher", "Okhema")
    ws.relationship_delta["cipher|phainon"] = 2
    warm = sl.bond_weather_block(ws, "phainon", name_of=name_of)
    check("delta warmer bond weather",
          "Bond weather" in warm and "warmer" in warm.lower(), warm[:120])

    print("== Item 10 eco notices ==")
    ws.set_location("phainon", "Okhema")
    sl.record_eco_notice(
        world=ws,
        place="Okhema",
        object_id="chimera-okhema-1",
        kind="care",
        line="A chimera leaned into a offered hand by the square.",
        visitor_action="pet",
        heir_hint="the visitor cared for a chimera here",
    )
    notices = sl.eco_notices_for_place(ws, "Okhema", limit=5)
    check("eco notice recorded", len(notices) >= 1)
    ep = sl.eco_notice_prompt(ws, "phainon")
    check("eco prompt titled", "What the land already showed" in ep, ep[:100])
    check("eco prompt mentions chimera", "chimera" in ep.lower(), ep[:120])
    ws.set_location("phainon", "Aidonia")
    ep2 = sl.eco_notice_prompt(ws, "phainon")
    check("eco silent at other place", ep2 == "")

    print("== Item 16 absence / return ==")
    # Reset ledger for a clean gap test
    ws.vivid["visitor_absences"] = {}
    sl.note_visit_touch(ws, "phainon")
    day0 = ws.vivid["visitor_absences"]["phainon"]["last_seen_day"]
    check("touch stores last_seen_day", isinstance(day0, int))
    # Advance ~7 Light days (5 periods each)
    ws.clock.advance(7 * PERIODS_PER_DAY)
    ab = sl.absence_prompt_block(ws, "phainon")
    check("absence after 7 days",
          "visitor returns after absence" in ab.lower(), ab[:100])
    check("returned_ack set",
          ws.vivid["visitor_absences"]["phainon"].get("returned_ack")
          == sl._day_index(ws))
    ab2 = sl.absence_prompt_block(ws, "phainon")
    check("absence does not repeat same day", ab2 == "")
    # Short gap: no block
    ws.vivid["visitor_absences"]["mydei"] = {
        "last_seen_day": sl._day_index(ws) - 2,
    }
    ab3 = sl.absence_prompt_block(ws, "mydei")
    check("short gap no absence block", ab3 == "")

    print("== Item 15 teaching echo ==")
    ws.set_location("anaxa", "Grove of Epiphany")
    ws.set_location("hyacine", "Grove of Epiphany")
    ws.set_location("phainon", "Okhema")
    echoes = sl.maybe_echo_teaching(
        ws, "anaxa", "the Coreflame of Reason and careful speech",
        "Grove of Epiphany",
    )
    check("echo to co-located only",
          len(echoes) == 1 and echoes[0].get("for") == "hyacine",
          str(echoes))
    check("echo marked secondhand",
          echoes and echoes[0].get("secondhand") is True)
    te = sl.teaching_echo_prompt(ws, "hyacine")
    check("hyacine gets echo prompt",
          "lesson overheard" in te.lower() or "secondhand" in te.lower(),
          te[:100])
    te2 = sl.teaching_echo_prompt(ws, "hyacine")
    check("echo consumed after use", te2 == "")
    te_p = sl.teaching_echo_prompt(ws, "phainon")
    check("distant heir no echo", te_p == "")

    skip1 = sl.maybe_echo_teaching(
        ws, "anaxa", "python programming basics", "Grove of Epiphany",
    )
    check("skips earth python topic", skip1 == [])
    skip2 = sl.maybe_echo_teaching(
        ws, "anaxa", "how a smartphone works", "Grove of Epiphany",
    )
    check("skips smartphone topic", skip2 == [])

    print("== map vignette ==")
    vg = sl.map_hour_vignette(ws, "Okhema")
    check("map vignette non-empty Okhema", bool(vg) and len(vg) > 8, vg)
    check("map vignette capped", len(vg) <= 180, str(len(vg)))

    print("== BOND_PAIRS export ==")
    check("BOND_PAIRS has phainon/mydei",
          frozenset({"phainon", "mydei"}) in sl.BOND_PAIRS)

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        for n in FAILED:
            print(f"  - {n}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
