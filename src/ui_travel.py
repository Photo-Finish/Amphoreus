"""The star-stranger's road, rendered as phone messages.

The end user experiences Amphoreus through the "Visit an Heir" chat, which
reads like a cellphone thread. This module turns the visitor's physical
travel (``world_state.visitor_travel``) into that phone idiom:

  A — a status bar pinned above the chat (full signal in town / roaming),
  B — travel event bubbles in the thread (set out / a day passes / arrive),
  D — the Heir you are talking to reacts to your journey, in their own voice.

Everything here is presentation + per-Heir flavour. No cards, no loader, no
style gate — the 8192 cycle is untouched (cycle-safe).
"""

from typing import Dict, List, Optional


# --------------------------------------------------------------------------- #
# Status / diff of the visitor's physical position
# --------------------------------------------------------------------------- #
def travel_status(ws) -> dict:
    """Where the visitor is right now (at a city, or on the road)."""
    try:
        st = ws.visitor_place()
        if not isinstance(st, dict):
            raise ValueError("no position")
        return st
    except Exception:
        return {"kind": "at", "at": "Okhema"}


def diff_travel(prev: Optional[dict], curr: dict) -> List[dict]:
    """What happened between two snapshots of the visitor's position.

    Returns a list of events (oldest first):
      {"kind": "set_out",  "from", "to", "remaining"}
      {"kind": "day",      "from", "to", "remaining"}   (one road-day passed)
      {"kind": "arrived",  "from", "to"}
      {"kind": "cancel",   "from", "to"}
      {"kind": "moved",    "from", "to"}                 (instant short move)
    """
    prev = prev or {"kind": "at", "at": "Okhema"}
    curr = curr or {"kind": "at", "at": "Okhema"}
    evs: List[dict] = []
    pk, ck = prev.get("kind"), curr.get("kind")
    if pk == "at" and ck == "at":
        if prev.get("at") != curr.get("at"):
            evs.append({"kind": "moved", "from": prev.get("at"), "to": curr.get("at")})
    elif pk == "at" and ck == "traveling":
        evs.append({"kind": "set_out", "from": prev.get("at"), "to": curr.get("to"),
                    "remaining": int(curr.get("remaining", 0))})
    elif pk == "traveling" and ck == "traveling":
        if prev.get("to") != curr.get("to"):
            evs.append({"kind": "cancel", "from": prev.get("from"), "to": prev.get("to")})
            evs.append({"kind": "set_out", "from": curr.get("from"), "to": curr.get("to"),
                        "remaining": int(curr.get("remaining", 0))})
        elif int(curr.get("remaining", 0)) < int(prev.get("remaining", 0)):
            evs.append({"kind": "day", "from": curr.get("from"), "to": curr.get("to"),
                        "remaining": int(curr.get("remaining", 0))})
    elif pk == "traveling" and ck == "at":
        if curr.get("at") == prev.get("to"):
            evs.append({"kind": "arrived", "from": prev.get("from"), "to": prev.get("to")})
        else:
            evs.append({"kind": "cancel", "from": prev.get("from"), "to": prev.get("to")})
    return evs


# --------------------------------------------------------------------------- #
# The road's own voice — one-line glimpses, deterministic per rerun
# --------------------------------------------------------------------------- #
_ROAD_FLAVOR = [
    "You pass olive terraces silver in the dusk.",
    "A caravanserai of merchants shares its fire with you.",
    "The fog lifts over the valley and the road unrolls ahead.",
    "You ford a river by starlight; the water is cold and quick.",
    "A courier's bell rings past you, bound the other way.",
    "Wild thyme and dust — the road smells of high summer.",
    "You barter bread with a goat-herd at a wayside shrine.",
    "Thunder walks the ridge-line to your left, then passes on.",
    "A ruined watchtower keeps watch over the empty miles.",
    "Fireflies thread the hedgerows like a second, gentler sky.",
]


def road_vignette(ev: dict) -> str:
    """A deterministic one-line glimpse of the road (stable across reruns).

    Stage 2: prefer a lived, weather/tide-aware line when the world is available;
    fall back to the classic flavor pool.
    """
    try:
        from src.world.world_state import WorldState
        from src.world import vivid_stage2 as _v2
        ws = WorldState()
        return _v2.lived_road_line(
            ws, ev.get("from", ""), ev.get("to", ""),
            int(ev.get("remaining", 0) or 0))
    except Exception:
        pass
    key = "%s|%s|%s" % (ev.get("from", ""), ev.get("to", ""), ev.get("remaining", 0))
    _seed = sum(ord(c) * (i + 1) for i, c in enumerate(key))
    return _ROAD_FLAVOR[_seed % len(_ROAD_FLAVOR)]


def travel_event_text(ev: dict) -> str:
    """The phone-message wording of one travel event."""
    k = ev.get("kind")
    if k == "set_out":
        return ("🧭 You set out from {f} for {t} — {n} day(s) on the road. "
                "Messages will wait until you reach signal.").format(
            f=ev.get("from", "?"), t=ev.get("to", "?"), n=ev.get("remaining", 0))
    if k == "day":
        return ("🌄 A day passes on the road to {t} — {n} day(s) left. "
                "{v}").format(t=ev.get("to", "?"), n=ev.get("remaining", 0),
                              v=road_vignette(ev))
    if k == "arrived":
        return ("🏛️ You arrive in {t}. 📶 Signal restored — your messages "
                "come through again.").format(t=ev.get("to", "?"))
    if k == "cancel":
        return "↩️ You turn back and return to {f}.".format(f=ev.get("from", "?"))
    if k == "moved":
        return ("🧭 You walk into {t}. 📶 Signal restored — your messages "
                "come through again.").format(t=ev.get("to", "?"))
    return ""


# --------------------------------------------------------------------------- #
# D — the Heir you are talking to reacts to your road, in their own voice
# --------------------------------------------------------------------------- #
_HEIR_REACT_SETOUT = {
    "tribbie": "You're going all the way there? Send word when you arrive — I'll be watching the road.",
    "cerydra": "The road is long. Keep your blade loose and your word shorter. I'll expect you when I expect you.",
    "evernight": "Safe travels across the starlit dark. I will keep the lamp burning.",
    "dan-heng-permansor-terrae": "The Trailblaze goes where it will. Walk well — and send word when you reach shelter.",
    "hysilens": "I will keep the watch here. May the currents carry you swiftly.",
    "hyacine": "The wind is with you. I'll light a candle for your road — send word when you arrive.",
    "phainon": "Go on, then. I'll hold the fort — and hold you to your promise to write.",
    "anaxa": "Every road is a hypothesis tested by the traveller. Report your findings on arrival.",
    "aglaea": "The threads of fate stretch with you. I will be weaving your safe return into the pattern.",
    "mydei": "A journey worth taking. If the road gives you trouble, give it back twice over.",
    "castorice": "The road between cities is quiet — few souls walk there. Walk without fear; I will be listening.",
    "cipher": "Off you go? I'll make sure everyone hears you're coming. Or not. Depends on the price.",
    "cyrene": "Oh! A journey! Bring me back a story — the best kind of treasure.",
}

_HEIR_REACT_ARRIVED = {
    "tribbie": "You made it! Tell me everything — what did the road look like?",
    "cerydra": "You've arrived. Good. Rest — the city keeps while you catch your breath.",
    "evernight": "You are safely arrived. The stars saw you all the way.",
    "dan-heng-permansor-terrae": "Well arrived. The Express would be proud of the legs on you.",
    "hysilens": "You stand on new ground now. Let the currents of that place teach you its name.",
    "hyacine": "You're there — and the candle is still burning. Come find me when you can.",
    "phainon": "Arrived, then. I told you the road would be kind. Now — how was it?",
    "anaxa": "Arrived. Good — the hypothesis holds. What did the journey itself teach you?",
    "aglaea": "You have arrived, and the threads have held. Welcome to where you stand.",
    "mydei": "You made it. Good. Now the real work — what did you conquer on the way?",
    "castorice": "You have crossed the distance. The quiet between cities has let you go — as it should.",
    "cipher": "Oh good, you're here. I was getting bored without a new rumour about you.",
    "cyrene": "You're here, you're here! Did you bring the story?",
}

_CANCEL_REACTIONS = [
    "Turned back? The road will still be there tomorrow — and so will I.",
    "A wise traveller knows when the road is not theirs. Come back when you are ready.",
]


def heir_travel_reaction(character_id: str, kind: str,
                         ev: Optional[dict] = None) -> str:
    """The Heir's in-voice text about your journey ('' when none applies)."""
    if kind in ("arrived", "moved"):
        return _HEIR_REACT_ARRIVED.get(character_id, "")
    if kind == "set_out":
        return _HEIR_REACT_SETOUT.get(character_id, "")
    if kind == "cancel":
        _seed = sum(ord(c) * (i + 1) for i, c in enumerate(str(ev or {})))
        return _CANCEL_REACTIONS[_seed % len(_CANCEL_REACTIONS)]
    return ""


# --------------------------------------------------------------------------- #
# Phone-idiom HTML: the status bar (A) and the carrier-notice bubbles (B)
# --------------------------------------------------------------------------- #
def _esc(s) -> str:
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def travel_status_html(status: dict) -> str:
    """Phone-style status bar: full signal in town, roaming on the road."""
    _bars = ('<span class="amp-signal"><i style="height:4px"></i>'
             '<i style="height:7px"></i><i style="height:10px"></i>'
             '<i style="height:12px"></i></span>')
    if status.get("kind") == "traveling":
        return (
            '<div class="amp-travelbar roaming">'
            '<span class="amp-dot"></span>'
            + _bars +
            '<span class="amp-txt">ROAMING &nbsp;·&nbsp; {} &rarr; {}'
            ' &nbsp;·&nbsp; {} day(s) left</span>'
            '<span class="amp-sub">📡 messages may be delayed</span>'
            '</div>'
        ).format(_esc(status.get("from")), _esc(status.get("to")),
                 int(status.get("remaining", 0)))
    return (
        '<div class="amp-travelbar">'
        + _bars +
        '<span class="amp-txt">📍 {}</span>'
        '<span class="amp-sub">📶 full signal</span>'
        '</div>'
    ).format(_esc(status.get("at", "Okhema")))


def travel_note_html(text: str) -> str:
    """A centred, muted carrier-notice bubble for a travel event."""
    return '<div class="amp-travelnote">{}</div>'.format(_esc(text))
