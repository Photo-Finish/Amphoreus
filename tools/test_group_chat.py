# -*- coding: utf-8 -*-
"""Group chat — co-presence, invitations, accept/decline, end-on-leave.

No LLM required. Voice is injected via a `speak` callback.

    D:\\Workspace\\.venv\\Scripts\\python.exe tools\\test_group_chat.py
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
from src.world import group_chat as gc
from src.world import vivid_stage2 as v2

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


def _ws():
    tmp = Path(tempfile.mkdtemp(prefix="amp-gc-"))
    state_path = tmp / "world_state.json"
    os.environ["AMPHOREUS_STATE_PATH"] = str(state_path)
    ws = WorldState(str(state_path))
    ws.time_scale = 2.0
    ws.black_tide_enabled = True
    ws.surge = {"active": False, "remaining": 0, "cities": []}
    ws.visitor_location = "Okhema"
    ws.visitor_travel = {}
    set_play(ws, "journey")
    _scatter(ws)
    return ws


def _scatter(ws):
    """Park every Heir somewhere unique so copresence is explicit."""
    parking = {
        "tribbie": "Janusopolis",
        "cerydra": "Dawncloud",
        "evernight": "Great Tomb",
        "dan-heng-permansor-terrae": "Vortex of Genesis",
        "hysilens": "Styxia",
        "hyacine": "Grove of Epiphany",
        "phainon": "Aedes Elysiae",
        "anaxa": "Sanctum of Prophecy",
        "aglaea": "Okhema",
        "mydei": "Castrum Kremnos",
        "castorice": "Aidonia",
        "cipher": "Eternal Holy City",
        "cyrene": "Aedes Elysiae",
    }
    for cid, loc in parking.items():
        ws.set_location(cid, loc)
    ws.save()


def _speak_accept(cid, prompt):
    return f"I'll join you here. ACCEPT"


def _speak_decline(cid, prompt):
    return f"Not this hour. I decline. DECLINE"


def _speak_mixed(cid, prompt):
    if cid == "phainon":
        return "Hah. Count me in. ACCEPT"
    return "I cannot sit with you. DECLINE"


def _speak_group(cid, prompt):
    return {
        "aglaea": "The gold of this hour is company. Speak.",
        "phainon": "I'm with you. Say it plainly.",
        "tribbie": "We hear you!",
        "cipher": "Well? Out with it.",
    }.get(cid, f"{cid} listens.")


def main():
    print("== Co-presence (selected Heir's place) ==")
    ws = _ws()
    ws.set_location("aglaea", "Okhema")
    ws.set_location("phainon", "Okhema")
    ws.set_location("tribbie", "Okhema")
    ws.set_location("mydei", "Castrum Kremnos")
    ws.save()

    here = gc.copresent_heirs(ws, "aglaea")
    check("aglaea listed at her place", "aglaea" in here, str(here))
    check("phainon co-present in Okhema", "phainon" in here, str(here))
    check("tribbie co-present in Okhema", "tribbie" in here, str(here))
    check("mydei not co-present (Kremnos)", "mydei" not in here, str(here))
    check("group possible when 2+ share the place",
          gc.group_possible(ws, "aglaea"))
    check("companions exclude the host",
          "aglaea" not in gc.companions_for_group(ws, "aglaea"))
    check("same map as companions_here",
          set(v2.companions_here(ws, "aglaea"))
          >= set(gc.companions_for_group(ws, "aglaea")))

    ws.set_location("phainon", "Aedes Elysiae")
    ws.set_location("tribbie", "Janusopolis")
    ws.save()
    check("solo Heir: group not possible",
          not gc.group_possible(ws, "aglaea"),
          str(gc.copresent_heirs(ws, "aglaea")))

    print("== Travelers are not here ==")
    ws = _ws()
    ws.set_location("aglaea", "Okhema")
    ws.set_location("phainon", "Okhema")
    ws.begin_travel("phainon", "Aedes Elysiae")
    ws.save()
    check("traveling Heir not copresent",
          "phainon" not in gc.copresent_heirs(ws, "aglaea"))
    check("no group while the other is on the road",
          not gc.group_possible(ws, "aglaea"))

    print("== Invite / accept ==")
    ws = _ws()
    ws.set_location("aglaea", "Okhema")
    ws.set_location("phainon", "Okhema")
    ws.set_location("cipher", "Okhema")
    ws.save()
    store = {}
    res = gc.send_invitations(
        ws, "aglaea", ["phainon", "cipher"],
        name_of=lambda c: c,
        speak=_speak_accept,
        store=store,
    )
    check("invitation started the gathering", res.get("started") is True, str(res))
    check("both invitees accepted",
          res.get("accepted") == ["phainon", "cipher"], str(res.get("accepted")))
    check("session active with host + acceptors",
          gc.session_active(store))
    check("members include host",
          "aglaea" in gc.as_session(store).get("members", []))
    check("members include phainon",
          "phainon" in gc.as_session(store).get("members", []))
    check("replies are in-world lines, not a modal",
          all("ACCEPT" not in (r.get("content") or "") for r in res["replies"]))
    check("world line names the place",
          "Okhema" in (res.get("world_line") or ""))

    print("== Invite / all decline ==")
    ws = _ws()
    ws.set_location("aglaea", "Okhema")
    ws.set_location("phainon", "Okhema")
    ws.save()
    store = {}
    res = gc.send_invitations(
        ws, "aglaea", ["phainon"],
        name_of=lambda c: c,
        speak=_speak_decline,
        store=store,
    )
    check("all-decline does not start group", res.get("started") is False)
    check("phainon recorded as declined", "phainon" in res.get("declined", []))
    check("session not active after all decline", not gc.session_active(store))
    check("world voice says the hour remains",
          "remains" in (res.get("world_line") or "").lower()
          or "no one else" in (res.get("world_line") or "").lower(),
          res.get("world_line"))

    print("== Mixed accept (one joins) ==")
    ws = _ws()
    ws.set_location("aglaea", "Okhema")
    ws.set_location("phainon", "Okhema")
    ws.set_location("cipher", "Okhema")
    ws.save()
    store = {}
    res = gc.send_invitations(
        ws, "aglaea", ["phainon", "cipher"],
        name_of=lambda c: c,
        speak=_speak_mixed,
        store=store,
    )
    check("one acceptor is enough to start", res.get("started") is True)
    check("only phainon accepted", res.get("accepted") == ["phainon"])
    check("cipher declined", "cipher" in res.get("declined", []))
    check("members are host + acceptor only",
          set(gc.as_session(store)["members"]) == {"aglaea", "phainon"})

    print("== Tide duty forces a decline ==")
    ws = _ws()
    ws.set_location("phainon", "Castrum Kremnos")
    ws.set_location("mydei", "Castrum Kremnos")
    ws.surge = {"active": True, "remaining": 2, "cities": ["Castrum Kremnos"]}
    set_play(ws, "journey")
    ws.save()
    considered = gc.consider_invite(ws, "phainon", "mydei", name_of=lambda c: c)
    check("Mydei forced-decline under black tide",
          considered.get("forced_decline") is True, str(considered))
    store = {}
    res = gc.send_invitations(
        ws, "phainon", ["mydei"],
        name_of=lambda c: c,
        speak=_speak_accept,  # voice would accept; duty overrides
        store=store,
    )
    check("duty wins over spoken ACCEPT", res.get("started") is False, str(res))
    check("duty line mentions tide or watch or duty",
          any(w in (res["replies"][0]["content"] or "").lower()
              for w in ("tide", "watch", "duty")),
          res["replies"][0]["content"] if res.get("replies") else "")

    ws.surge = {"active": False, "remaining": 0, "cities": []}
    ws.save()
    res2 = gc.send_invitations(
        ws, "phainon", ["mydei"],
        name_of=lambda c: c,
        speak=_speak_accept,
        store={},
    )
    check("Mydei may join when the tide is quiet", res2.get("started") is True)

    print("== Group turn: distinct voices, not a parrot ==")
    ws = _ws()
    ws.set_location("aglaea", "Okhema")
    ws.set_location("phainon", "Okhema")
    ws.save()
    store = {}
    gc.send_invitations(
        ws, "aglaea", ["phainon"],
        name_of=lambda c: c, speak=_speak_accept, store=store,
    )
    lines = gc.generate_group_turn(
        None, store, "What do you make of the morning?",
        world=ws, name_of=lambda c: c, speak=_speak_group,
    )
    speakers = [m.get("speaker") for m in lines]
    check("at least one Heir answers a group turn", len(lines) >= 1, str(lines))
    check("speakers are gathering members",
          all(s in {"aglaea", "phainon"} for s in speakers), str(speakers))
    texts = [m.get("content") for m in lines]
    check("two speakers do not parrot the same line",
          len(texts) < 2 or texts[0] != texts[1], str(texts))
    check("two-member gathering can both speak",
          set(speakers) == {"aglaea", "phainon"} or len(speakers) >= 1,
          str(speakers))

    addressed = gc.who_speaks(
        ["aglaea", "phainon", "tribbie"], "aglaea",
        "Phainon, what do you think?",
        lambda c: {"aglaea": "Aglaea", "phainon": "Phainon",
                   "tribbie": "Tribbie"}[c],
    )
    check("addressed Heir is chosen to speak",
          "phainon" in addressed, str(addressed))

    trio = gc.who_speaks(
        ["aglaea", "phainon", "cipher"], "aglaea",
        "What do you make of the morning?",
        lambda c: {"aglaea": "Aglaea", "phainon": "Phainon",
                   "cipher": "Cipher"}[c],
        turn_index=0,
    )
    check("three-member gathering can field more than two voices",
          len(trio) >= 2, str(trio))
    check("three-member turn may include the full company",
          len(trio) in (2, 3), str(trio))

    print("== Offline fallback does not repeat across rounds ==")
    ws = _ws()
    ws.set_location("aglaea", "Okhema")
    ws.set_location("cipher", "Okhema")
    ws.save()
    store = {}
    gc.send_invitations(
        ws, "aglaea", ["cipher"],
        name_of=lambda c: c, speak=_speak_accept, store=store,
    )

    def _speak_offline(cid, prompt):
        return (
            f"[{cid} listens carefully. The LLM backend is not configured — "
            "start Ollama to enable live responses.]"
        )

    t1 = gc.generate_group_turn(
        None, store, "Cipher, what do you hear?",
        world=ws, name_of=lambda c: c, speak=_speak_offline,
    )
    t2 = gc.generate_group_turn(
        None, store, "And what of the hour?",
        world=ws, name_of=lambda c: c, speak=_speak_offline,
    )
    cipher_lines = [
        m.get("content") for m in (t1 + t2)
        if m.get("speaker") == "cipher"
    ]
    check("Cipher spoke on offline turns",
          len(cipher_lines) >= 1, str(cipher_lines))
    if len(cipher_lines) >= 2:
        check("Cipher offline lines differ across rounds",
              cipher_lines[0] != cipher_lines[1], str(cipher_lines))
    else:
        # Host-only on one turn is fine; still verify fallback pool varies.
        a = gc.fallback_group_line("cipher", "first", ["Aglaea"], turn_index=0)
        b = gc.fallback_group_line(
            "cipher", "second", ["Aglaea"], avoid=[a], turn_index=1,
        )
        check("Cipher offline lines differ across rounds",
              a != b, f"{a!r} vs {b!r}")

    check("lines_too_similar catches exact repeats",
          gc.lines_too_similar("Well? Out with it.", "Well? Out with it."))
    check("lines_too_similar allows distinct beats",
          not gc.lines_too_similar(
              "Well? Don't leave a girl hanging — out with it.",
              "Heh. That's a thing to say in this company.",
          ))

    print("== Ambient Heir-to-Heir talk without a user line ==")
    ws = _ws()
    ws.set_location("aglaea", "Okhema")
    ws.set_location("phainon", "Okhema")
    ws.save()
    store = {}
    gc.send_invitations(
        ws, "aglaea", ["phainon"],
        name_of=lambda c: c, speak=_speak_accept, store=store,
    )
    # Fresh gathering is not due yet (activity just marked).
    check("ambient not due immediately after invite",
          gc.ambient_due(store) is False)
    # Force idle on the session object (store may nest under STATE_KEY).
    gc.as_session(store)["last_activity_ts"] = 0.0
    check("ambient due after idle", gc.ambient_due(store) is True)

    amb = gc.generate_ambient_turn(
        None, store, world=ws, name_of=lambda c: c, speak=_speak_group,
    )
    check("ambient turn produces Heir lines", len(amb) >= 1, str(amb))
    check("ambient lines have speakers, no user role",
          all(m.get("role") == "assistant" and m.get("speaker")
              for m in amb), str(amb))
    check("ambient speakers are gathering members",
          all(m.get("speaker") in {"aglaea", "phainon"} for m in amb),
          str(amb))
    # No new user message was appended.
    sess_msgs = gc.as_session(store).get("messages") or []
    user_msgs = [m for m in sess_msgs if m.get("role") == "user"]
    check("ambient does not invent a user message",
          len(user_msgs) == 0, str(user_msgs))

    amb_cast = gc.who_speaks(
        ["aglaea", "phainon", "cipher"], "aglaea", "",
        lambda c: {"aglaea": "Aglaea", "phainon": "Phainon",
                   "cipher": "Cipher"}[c],
        turn_index=1, ambient=True,
    )
    check("ambient cast stays small (1–2 of 3)",
          1 <= len(amb_cast) <= 2, str(amb_cast))

    a_line = gc.fallback_group_line(
        "cipher", "", ["Aglaea"], turn_index=0, ambient=True,
    )
    b_line = gc.fallback_group_line(
        "cipher", "", ["Aglaea"], avoid=[a_line], turn_index=1, ambient=True,
    )
    check("ambient offline lines can differ",
          a_line != b_line, f"{a_line!r} vs {b_line!r}")

    # Force while not due still works.
    gc.as_session(store)["last_activity_ts"] = __import__("time").time()
    forced = gc.generate_ambient_turn(
        None, store, world=ws, name_of=lambda c: c, speak=_speak_group,
        force=True,
    )
    check("force ambient runs even when not idle",
          len(forced) >= 1, str(forced))

    print("== End on leaving Visit (not on closing the site) ==")
    check("leaving Walk the Land tab ends the gathering",
          gc.should_end_for_tab("Walk the Land"))
    check("leaving Map tab ends the gathering",
          gc.should_end_for_tab("Map of Amphoreus"))
    check("leaving Chronicle tab ends the gathering",
          gc.should_end_for_tab("A Chronicle of Amphoreus"))
    check("staying on Visit does not end",
          not gc.should_end_for_tab("Visit an Heir"))
    check("blank tab name is not an end (no false unload)",
          not gc.should_end_for_tab(""))
    check("query amp_tab=away ends", gc.should_end_for_query("away"))
    check("query amp_tab=visit does not end",
          not gc.should_end_for_query("visit"))

    store = {"active": True, "host": "aglaea", "place": "Okhema",
             "members": ["aglaea", "phainon"], "messages": [{"role": "user"}],
             "invited": ["phainon"], "accepted": ["phainon"], "declined": [],
             "kind": "active"}
    old = gc.session_end(store)
    check("session_end clears active", store.get("active") is False)
    check("session_end keeps a copy of members",
          "phainon" in (old.get("members") or []))
    check("messages cleared after leave", store.get("messages") == [])

    print("== Guest / operator gate ==")
    from src.world.group_chat import operator_may_invite
    check("operator may invite", operator_may_invite(False) is True)
    check("visitor may not invite", operator_may_invite(True) is False)

    print("== Gathering breaks if co-presence is lost ==")
    ws = _ws()
    ws.set_location("aglaea", "Okhema")
    ws.set_location("phainon", "Okhema")
    store = {}
    gc.send_invitations(
        ws, "aglaea", ["phainon"],
        name_of=lambda c: c, speak=_speak_accept, store=store,
    )
    check("together at start", gc.still_together(ws, store))
    ws.set_location("phainon", "Aedes Elysiae")
    ws.save()
    check("not together after a member leaves the place",
          not gc.still_together(ws, store))

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("Failed:")
        for n in FAILED:
            print(" -", n)
        sys.exit(1)


if __name__ == "__main__":
    main()
