"""Dry tests for the travel-as-phone-messages layer (src/ui_travel.py).

Checks the event diffing, the road wording, the per-Heir in-voice reactions,
and the phone-idiom HTML. Cycle-safe: touches no cards/loader/style gate.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui_travel import (
    travel_status, diff_travel, road_vignette, travel_event_text,
    heir_travel_reaction, travel_status_html, travel_note_html,
)

_ALL_HEIRS = [
    "tribbie", "cerydra", "evernight", "dan-heng-permansor-terrae", "hysilens",
    "hyacine", "phainon", "anaxa", "aglaea", "mydei", "castorice", "cipher",
    "cyrene",
]


class _FakeWS:
    def __init__(self, place):
        self._place = place

    def visitor_place(self):
        return self._place


def _check(name, cond):
    if not cond:
        raise AssertionError("FAIL: " + name)
    print("  ok  " + name)


def test_status():
    print("[status]")
    _check("travel_status at", travel_status(_FakeWS({"kind": "at", "at": "Okhema"}))
           == {"kind": "at", "at": "Okhema"})
    _check("travel_status traveling",
           travel_status(_FakeWS({"kind": "traveling", "to": "Styxia",
                                  "from": "Okhema", "remaining": 3}))
           == {"kind": "traveling", "to": "Styxia", "from": "Okhema", "remaining": 3})
    _check("travel_status fallback", travel_status(_FakeWS(None))["kind"] == "at")


def test_diff():
    print("[diff_travel]")
    at_o = {"kind": "at", "at": "Okhema"}
    at_s = {"kind": "at", "at": "Styxia"}
    tr = {"kind": "traveling", "to": "Styxia", "from": "Okhema", "remaining": 3}
    tr2 = {"kind": "traveling", "to": "Styxia", "from": "Okhema", "remaining": 2}
    tr_other = {"kind": "traveling", "to": "Kremnos", "from": "Okhema", "remaining": 5}

    _check("no change -> []", diff_travel(at_o, at_o) == [])
    _check("at -> traveling = set_out",
           diff_travel(at_o, tr) == [{"kind": "set_out", "from": "Okhema",
                                      "to": "Styxia", "remaining": 3}])
    _check("road-day passed",
           diff_travel(tr, tr2) == [{"kind": "day", "from": "Okhema",
                                     "to": "Styxia", "remaining": 2}])
    _check("arrived at destination",
           diff_travel(tr, at_s) == [{"kind": "arrived", "from": "Okhema",
                                      "to": "Styxia"}])
    _check("turned back (cancelled)",
           diff_travel(tr, at_o) == [{"kind": "cancel", "from": "Okhema",
                                      "to": "Styxia"}])
    _check("instant short move",
           diff_travel(at_o, at_s) == [{"kind": "moved", "from": "Okhema",
                                        "to": "Styxia"}])
    _check("changed destination mid-road = cancel + set_out",
           diff_travel(tr, tr_other) == [
               {"kind": "cancel", "from": "Okhema", "to": "Styxia"},
               {"kind": "set_out", "from": "Okhema", "to": "Kremnos",
                "remaining": 5}])
    _check("first sighting, already at town -> []",
           diff_travel(None, at_o) == [])


def test_text():
    print("[travel_event_text / road_vignette]")
    t1 = travel_event_text({"kind": "set_out", "from": "Okhema", "to": "Styxia",
                            "remaining": 3})
    _check("set_out wording", "set out from Okhema" in t1 and "3 day(s)" in t1)
    t2 = travel_event_text({"kind": "day", "from": "Okhema", "to": "Styxia",
                            "remaining": 2})
    _check("day wording", "A day passes" in t2 and "2 day(s) left" in t2)
    _classic = [
        "olive terraces", "caravanserai", "fog lifts", "ford a river",
        "courier's bell", "wild thyme", "goat-herd", "ridge-line",
        "watchtower", "Fireflies",
    ]
    _lived = [
        "Between ", "On the road to", "Leaving ", "Rain needles",
        "Thunder walks", "Fog takes", "surged sky", "black tide",
        "olive terraces", "clean Amphoreus", "wayside", "bells",
    ]
    _check("day includes a road vignette",
           any(v in t2 for v in _classic + _lived))
    t3 = travel_event_text({"kind": "arrived", "to": "Styxia"})
    _check("arrived wording", "arrive in Styxia" in t3 and "Signal restored" in t3)
    t4 = travel_event_text({"kind": "cancel", "from": "Okhema"})
    _check("cancel wording", "turn back" in t4)
    t5 = travel_event_text({"kind": "moved", "to": "Kremnos"})
    _check("moved wording", "walk into Kremnos" in t5)
    _check("empty for unknown kind", travel_event_text({"kind": "nope"}) == "")
    _check("vignette deterministic",
           road_vignette({"from": "Okhema", "to": "Styxia", "remaining": 2})
           == road_vignette({"from": "Okhema", "to": "Styxia", "remaining": 2}))
    _check("vignette varies across roads",
           road_vignette({"from": "Okhema", "to": "Styxia", "remaining": 2})
           != road_vignette({"from": "Kremnos", "to": "Vortex", "remaining": 9}))


def test_reactions():
    print("[heir_travel_reaction]")
    for cid in _ALL_HEIRS:
        so = heir_travel_reaction(cid, "set_out", {"to": "Styxia"})
        ar = heir_travel_reaction(cid, "arrived", {"to": "Styxia"})
        _check(f"{cid} set_out reaction present", bool(so.strip()))
        _check(f"{cid} arrived reaction present", bool(ar.strip()))
        _check(f"{cid} no placeholder left", "{" not in so and "{" not in ar)
    _check("moved uses arrived voice",
           heir_travel_reaction("anaxa", "moved") == heir_travel_reaction("anaxa", "arrived"))
    _check("cancel gives a line",
           bool(heir_travel_reaction("tribbie", "cancel").strip()))
    _check("day gives nothing", heir_travel_reaction("tribbie", "day") == "")
    _check("unknown heir -> ''", heir_travel_reaction("nobody", "set_out") == "")


def test_html():
    print("[travel_status_html / travel_note_html]")
    h_home = travel_status_html({"kind": "at", "at": "Okhema"})
    h_road = travel_status_html({"kind": "traveling", "to": "Styxia",
                                 "from": "Okhema", "remaining": 3})
    _check("home bar has full signal", "full signal" in h_home)
    _check("home bar shows the city", "Okhema" in h_home)
    _check("road bar shows ROAMING", "ROAMING" in h_road)
    _check("road bar shows days left", "3 day(s) left" in h_road)
    _check("road bar is roaming class", "amp-travelbar roaming" in h_road)
    _n = travel_note_html("a <b> & c")
    _check("note escapes raw markup", "<b>" not in _n and "&amp;" in _n)
    _check("note wraps in travelnote", _n.startswith(
        '<div class="amp-travelnote">'))


if __name__ == "__main__":
    test_status()
    test_diff()
    test_text()
    test_reactions()
    test_html()
    print("ALL UI-TRAVEL TESTS PASSED")
