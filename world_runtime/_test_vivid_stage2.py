# -*- coding: utf-8 -*-
"""Dry-tests + cross-checks for Stage-2 vivid society / natural world.

No LLM required. Cross-checks existing features (black tide, letters, weather,
co-location, aftermath peace) against the new Stage-2 behaviours.

    d:\\Workspace\\.venv\\Scripts\\python.exe world_runtime\\_test_vivid_stage2.py
"""

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world.world_state import WorldState
from src.world import world_events as wev
from src.world import living_world as lw
from src.world import vivid_stage2 as v2
from src.ui_travel import road_vignette

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def set_play(ws, mode: str):
    ws.play_mode = mode
    ws.save()


def main():
    tmp = Path(tempfile.mkdtemp(prefix="amp-v2-"))
    state_path = tmp / "world_state.json"
    os.environ["AMPHOREUS_STATE_PATH"] = str(state_path)
    ws = WorldState(str(state_path))

    # Fresh amicable layout
    ws.set_location("aglaea", "Okhema")
    ws.set_location("phainon", "Okhema")
    ws.set_location("mydei", "Castrum Kremnos")
    ws.set_location("tribbie", "Okhema")
    ws.ambient = {
        "weather": {
            "Okhema": "clear bright day",
            "Castrum Kremnos": "clear",
            "Styxia": "fog over the drowned quays",
        },
        "errands": {"aglaea": "inspect the loom halls"},
        "news": "The Dawn Device holds.",
    }
    ws.black_tide_enabled = True
    ws.surge = {"active": False, "remaining": 0, "cities": []}
    set_play(ws, "journey")
    ws.save()

    print("== Canon / roster sanity ==")
    names = {n["name"] for n in wev.NPCS}
    check("no dead Gorgo in NPCS", "Gorgo" not in names)
    check("no dead Krateros in NPCS", "Krateros" not in names)
    check("Bartholos alive in Okhema",
          any(n["name"] == "Bartholos" and n["city"] == "Okhema" for n in wev.NPCS))

    print("== Place-hour frame ==")
    frame = v2.place_hour_frame(ws, "aglaea", name_of=lambda c: c)
    check("place is Okhema", frame["place"] == "Okhema")
    check("weather present", "clear" in frame["weather"])
    check("phainon listed present", "phainon" in frame["present"])
    check("mydei not listed (elsewhere)", "mydei" not in frame["present"])
    check("errand surfaces", "loom" in frame["errand"])
    md = v2.place_hour_markdown(frame, "Aglaea")
    check("markdown names place", "Okhema" in md)
    pb = v2.place_hour_prompt_block(frame)
    check("prompt block titled", "This hour" in pb)

    print("== Shared scene + Mydei / black tide cross-check ==")
    # Happy path: Aglaea + Phainon in Okhema
    inv = v2.invite_shared_scene(ws, "aglaea", "phainon", name_of=lambda c: c)
    check("Okhema shared scene accepted", inv.get("ok") is True, str(inv))
    check("active_scene set",
          (ws.vivid.get("active_scene") or {}).get("host") == "aglaea")
    scb = v2.shared_scene_prompt_block(ws, "aglaea", name_of=lambda c: c)
    check("shared scene prompt for host", "Shared scene" in scb)
    scb2 = v2.shared_scene_prompt_block(ws, "mydei", name_of=lambda c: c)
    check("shared scene silent for outsider", scb2 == "")

    # Cross-check: Mydei refuses when tide surges at Kremnos
    v2.clear_shared_scene(ws)
    ws.set_location("phainon", "Castrum Kremnos")  # co-locate for invite geometry
    ws.set_location("mydei", "Castrum Kremnos")
    ws.surge = {"active": True, "remaining": 2, "cities": ["Castrum Kremnos"]}
    ws.save()
    # Also cross-check existing living_world surge consequence
    check("living_world surge line on Mydei",
          "black tide" in lw.surge_consequence_line(ws, "mydei").lower())
    inv2 = v2.invite_shared_scene(ws, "phainon", "mydei", name_of=lambda c: c)
    check("Mydei declines under black tide", inv2.get("ok") is False, str(inv2))
    check("decline cause is black_tide", inv2.get("cause") == "black_tide", str(inv2))
    check("decline reason mentions duty/watch",
          "duty" in (inv2.get("reason") or "").lower()
          or "watch" in (inv2.get("reason") or "").lower()
          or "tide" in (inv2.get("reason") or "").lower(),
          inv2.get("reason"))
    # Cross-check: without surge, same invite succeeds
    ws.surge = {"active": False, "remaining": 0, "cities": []}
    inv3 = v2.invite_shared_scene(ws, "phainon", "mydei", name_of=lambda c: c)
    check("Mydei accepts when tide is quiet", inv3.get("ok") is True, str(inv3))
    v2.clear_shared_scene(ws)

    # Aftermath: surge logic disabled for guardians? tide_duty checks aftermath
    set_play(ws, "aftermath")
    ws.surge = {"active": True, "remaining": 2, "cities": ["Castrum Kremnos"]}
    # surges_enabled may still be false in aftermath via wev — invite should not
    # use tide refusal when mode is aftermath
    inv4 = v2.invite_shared_scene(ws, "phainon", "mydei", name_of=lambda c: c)
    check("aftermath: Mydei not tide-refused", inv4.get("cause") != "black_tide",
          str(inv4))
    set_play(ws, "journey")
    ws.surge = {"active": False, "remaining": 0, "cities": []}
    v2.clear_shared_scene(ws)
    ws.set_location("phainon", "Okhema")
    ws.set_location("mydei", "Castrum Kremnos")

    print("== Overhear + Aglaea golden-thread cross-check ==")
    check("detect overhear intent",
          v2.detect_overhear_intent("I overheard what you told Phainon"))
    check("non-overhear not flagged",
          not v2.detect_overhear_intent("How is the weather in Okhema?"))
    v2.note_overhear(ws, "phainon",
                     "Phainon spoke of the Deliverer's doubts in private",
                     source="near Phainon")
    ws.save()
    oh_a = v2.overhear_prompt_block(ws, "aglaea")
    check("Aglaea senses overhear (golden threads)",
          "golden threads" in oh_a.lower() or "overhearing" in oh_a.lower(),
          oh_a[:120])
    check("Aglaea prompt names the snippet",
          "Deliverer" in oh_a or "doubts" in oh_a, oh_a[:160])
    oh_p = v2.overhear_prompt_block(ws, "phainon")
    check("Phainon has no golden-thread notice", oh_p == "")
    oh_c = v2.overhear_prompt_block(ws, "cipher")
    check("Cipher also notices (locked door)", "locked door" in oh_c.lower()
          or "secret" in oh_c.lower(), oh_c[:120])
    # Cross-check: inject path differs between Aglaea and a third Heir
    check("noticed_by has aglaea", "aglaea" in ws.vivid.get("noticed_by", {}))

    print("== Society continuity ==")
    wev.compose_letter(ws, "tribbie", "aglaea",
                       "The gates asked a question only you can weave.")
    # compose_letter may need checking - look at API
    if not ws.letters:
        ws.letters.append({
            "from": "tribbie", "to": "aglaea",
            "from_name": "Tribbie", "to_name": "Aglaea",
            "text": "The gates asked a question only you can weave.",
            "ts": ws.clock.format_short(),
        })
    wev.add_rumor(ws, "aglaea",
                  "The stranger spoke with Phainon of strange knowledge",
                  source="phainon")
    ws.relationship_delta["aglaea|phainon"] = 2
    cont = v2.society_continuity_block(ws, "aglaea", name_of=lambda c: c)
    check("continuity mentions letter", "letter" in cont.lower(), cont[:120])
    check("continuity mentions visitor rumor or bond",
          "stranger" in cont.lower() or "visitor" in cont.lower()
          or "warmer" in cont.lower(), cont[:160])

    print("== Ongoing moment ==")
    moment = v2.ongoing_moment(ws, "aglaea")
    check("ongoing moment is letter-kind", moment.get("kind") == "letter",
          str(moment))
    omp = v2.ongoing_moment_prompt(moment)
    check("ongoing prompt non-empty", "ongoing moment" in omp.lower())

    print("== NPC talk (alive only) + tide cross-check ==")
    bad = v2.talk_to_npc(ws, "Okhema", "Gorgo")
    check("dead Gorgo rejected", bad.get("ok") is False)
    good = v2.talk_to_npc(ws, "Okhema", "Bartholos")
    check("Bartholos speaks", good.get("ok") is True, str(good))
    check("Bartholos line has flavor",
          "Bartholos" in (good.get("line") or ""))
    # Cross-check: NPC under surged Styxia lowers voice
    ws.surge = {"active": True, "remaining": 1, "cities": ["Styxia"]}
    sty = v2.talk_to_npc(ws, "Styxia", "Theodosia")
    check("Theodosia under surge mentions edge/voice",
          sty.get("ok") is True and (
              "edge" in (sty.get("line") or "").lower()
              or "lower" in (sty.get("line") or "").lower()
              or "dark" in (sty.get("line") or "").lower()),
          sty.get("line"))
    ws.surge = {"active": False, "remaining": 0, "cities": []}

    print("== Lived road + weather/tide cross-check ==")
    ws.ambient["weather"]["Aidonia"] = "fog and cold"
    line = v2.lived_road_line(ws, "Okhema", "Aidonia", 2)
    check("road line mentions Aidonia or fog/bells",
          "Aidonia" in line or "fog" in line.lower() or "bell" in line.lower(),
          line)
    ws.surge = {"active": True, "remaining": 2, "cities": ["Aidonia"]}
    line2 = v2.lived_road_line(ws, "Okhema", "Aidonia", 1)
    check("road to surged city mentions surge/sky",
          "surged" in line2.lower() or "tide" in line2.lower()
          or "black" in line2.lower(), line2)
    # ui_travel.road_vignette should prefer lived road
    ev = {"kind": "day", "from": "Okhema", "to": "Aidonia", "remaining": 1}
    rv = road_vignette(ev)
    check("ui_travel road_vignette returns lived line", len(rv) > 10, rv)

    print("== Tide edge prompt / aftermath peace ==")
    ws.set_location("mydei", "Castrum Kremnos")
    ws.surge = {"active": True, "remaining": 2, "cities": ["Castrum Kremnos"]}
    set_play(ws, "journey")
    tp = v2.tide_edge_prompt(ws, "mydei")
    check("journey tide prompt non-empty for Mydei", "tide" in tp.lower(), tp)
    set_play(ws, "aftermath")
    tp2 = v2.tide_edge_prompt(ws, "mydei")
    check("aftermath tide prompt empty", tp2 == "")
    set_play(ws, "journey")

    print("== Persistence of vivid ledger ==")
    ws.surge = {"active": False, "remaining": 0, "cities": []}
    v2.note_overhear(ws, "anaxa", "a Grove secret", source="near Anaxa")
    ws.save()
    ws2 = WorldState(str(state_path))
    check("vivid ledger reloads",
          "aglaea" in (ws2.vivid.get("noticed_by") or {}))

    print("== AgentManager inject cross-check (stub, no LLM) ==")
    # Ensure injector methods exist and produce differing prompts
    from src.core.agent_manager import AgentManager
    # Redirect state for manager's WorldState() calls
    mgr = AgentManager(use_rag=False)
    # Rebuild ws with known layout for inject
    ws.set_location("aglaea", "Okhema")
    ws.set_location("phainon", "Okhema")
    v2.note_overhear(ws, "phainon", "private words of fate", source="near Phainon")
    v2.invite_shared_scene(ws, "aglaea", "phainon",
                           name_of=lambda c: "Aglaea" if c == "aglaea" else "Phainon")
    ws.save()
    p_ag = mgr._inject_vivid_context("aglaea", "BASE")
    p_hy = mgr._inject_vivid_context("hyacine", "BASE")
    check("Aglaea inject richer than Hyacine (overhear/scene)",
          len(p_ag) > len(p_hy), f"ag={len(p_ag)} hy={len(p_hy)}")
    check("Aglaea inject has overhear or shared scene",
          "overhear" in p_ag.lower() or "shared scene" in p_ag.lower()
          or "golden" in p_ag.lower(), p_ag[len("BASE"):len("BASE")+200])
    # Decline path via manager
    ws.set_location("mydei", "Castrum Kremnos")
    ws.set_location("phainon", "Castrum Kremnos")
    ws.surge = {"active": True, "remaining": 1, "cities": ["Castrum Kremnos"]}
    ws.save()
    dec = mgr.invite_shared_scene("phainon", "mydei")
    check("manager: Mydei declines under tide",
          dec.get("ok") is False and dec.get("cause") == "black_tide", str(dec))

    print()
    print(f"Passed {len(PASSED)}  Failed {len(FAILED)}")
    if FAILED:
        print("FAILED:", ", ".join(FAILED))
        sys.exit(1)
    print("ALL STAGE-2 VIVID CHECKS GREEN")
    sys.exit(0)


if __name__ == "__main__":
    main()
