# -*- coding: utf-8 -*-
"""Eternal Page — visitor gestures, visual reactions, mood (never Heir speech).

Keyboard and mouse combos pick a gesture. The Heir's answer is a face, a
VFX mark, and a living_world mood nudge. Spoken lines stay on manager.chat.
"""
from __future__ import annotations

import time
from typing import Iterable, Optional

from src.world.eternal_emotion import normalize_emotion, vfx_for

# Short pose/VFX overlay after a touch. Witness marks fade sooner.
GESTURE_TTL = 90.0
WITNESS_TTL = 45.0

# CSS class stems painted on each sticker (mk-<name>).
VFX_MARKS: tuple[str, ...] = (
    "flush",
    "vein",
    "steam",
    "sweat",
    "tear",
    "sparkle",
    "heart",
    "query",
    "bang",
    "dizzy",
    "zzz",
    "shock",
    "flower",
    "ice",
    "veil",
    "note",
    "shy",
    "glow",
)

# Factual visitor-facing reasons only — never first-person Heir lines.
GESTURES: dict[str, dict] = {
    "pet": {
        "label": "Gentle touch",
        "emotion": "warm",
        "vfx": ("flush",),
        "mood": 1,
        "reason": "a gentle touch on the Eternal Page",
        "social": False,
        "join_near": False,
    },
    "pat": {
        "label": "Pat the head",
        "emotion": "joy",
        "vfx": ("sparkle", "flush"),
        "mood": 1,
        "reason": "a pat on the head on the Eternal Page",
        "social": False,
        "join_near": False,
    },
    "poke": {
        "label": "Poke",
        "emotion": "surprise",
        "vfx": ("shock", "bang"),
        "mood": 0,
        "reason": "a poke on the Eternal Page",
        "social": False,
        "join_near": False,
    },
    "tease": {
        "label": "Tease",
        "emotion": "tease",
        "vfx": ("sparkle", "query"),
        "mood": 0,
        "reason": "a teasing poke on the Eternal Page",
        "social": False,
        "join_near": False,
    },
    "hands": {
        "label": "Hold hands",
        "emotion": "warm",
        "vfx": ("heart", "flush"),
        "mood": 1,
        "reason": "a hand-hold on the Eternal Page",
        "social": True,
        "join_near": True,
    },
    "hug": {
        "label": "Hug",
        "emotion": "warm",
        "vfx": ("heart", "flush", "shy"),
        "mood": 1,
        "reason": "a hug on the Eternal Page",
        "social": True,
        "join_near": True,
    },
    "wave": {
        "label": "Wave",
        "emotion": "joy",
        "vfx": ("sparkle",),
        "mood": 0,
        "reason": "a wave on the Eternal Page",
        "social": True,
        "join_near": False,
    },
    "comfort": {
        "label": "Comfort",
        "emotion": "warm",
        "vfx": ("flower", "flush"),
        "mood": 1,
        "reason": "a comforting touch on the Eternal Page",
        "social": False,
        "join_near": False,
    },
    "forehead": {
        "label": "Forehead tap",
        "emotion": "warm",
        "vfx": ("flush", "sparkle"),
        "mood": 1,
        "reason": "a forehead tap on the Eternal Page",
        "social": False,
        "join_near": False,
    },
    "cheek": {
        "label": "Cheek poke",
        "emotion": "surprise",
        "vfx": ("flush", "bang"),
        "mood": 0,
        "reason": "a cheek poke on the Eternal Page",
        "social": False,
        "join_near": False,
    },
    "gift": {
        "label": "Gift-touch",
        "emotion": "joy",
        "vfx": ("flower", "heart"),
        "mood": 1,
        "reason": "a gift-touch on the Eternal Page",
        "social": False,
        "join_near": False,
    },
    "bow": {
        "label": "Bow",
        "emotion": "calm",
        "vfx": ("sparkle", "glow"),
        "mood": 0,
        "reason": "a bow on the Eternal Page",
        "social": False,
        "join_near": False,
    },
}

GESTURE_IDS: frozenset[str] = frozenset(GESTURES)

# Which feeling fires — not authored speech. Shared table plus a few Heirs.
TEMPERAMENT: dict[str, dict[str, dict]] = {
    "aglaea": {
        "poke": {"emotion": "surprise"},
        "pat": {"emotion": "warm"},
        "tease": {"emotion": "tease"},
        "hug": {"emotion": "warm", "vfx": ("flush", "flower")},
    },
    "anaxa": {
        "poke": {"emotion": "tease", "vfx": ("sparkle", "query")},
        "pat": {"emotion": "calm", "vfx": ("query", "glow")},
        "tease": {"emotion": "tease", "vfx": ("query", "sparkle")},
        "gift": {"emotion": "tease"},
    },
    "castorice": {
        "poke": {"emotion": "fear", "vfx": ("sweat", "shock")},
        "hug": {"emotion": "warm", "vfx": ("shy", "flush")},
        "cheek": {"emotion": "surprise", "vfx": ("flush", "shy")},
        "hands": {"emotion": "warm", "vfx": ("heart", "shy")},
        "pat": {"emotion": "warm"},
    },
    "cerydra": {
        "poke": {"emotion": "anger", "vfx": ("vein", "steam")},
        "bow": {"emotion": "warm", "vfx": ("sparkle", "glow")},
        "pat": {"emotion": "tease"},
        "tease": {"emotion": "anger", "vfx": ("vein",)},
    },
    "cipher": {
        "poke": {"emotion": "tease"},
        "pat": {"emotion": "joy"},
        "gift": {"emotion": "tease", "vfx": ("sparkle", "heart")},
        "wave": {"emotion": "joy"},
    },
    "cyrene": {
        "poke": {"emotion": "surprise"},
        "pat": {"emotion": "warm"},
        "hug": {"emotion": "joy"},
        "hands": {"emotion": "warm"},
        "gift": {"emotion": "joy", "vfx": ("flower", "heart")},
    },
    "dan-heng-permansor-terrae": {
        "poke": {"emotion": "surprise"},
        "pat": {"emotion": "calm", "vfx": ("glow",)},
        "bow": {"emotion": "calm"},
        "comfort": {"emotion": "warm"},
        "tease": {"emotion": "calm", "vfx": ("query",)},
    },
    "evernight": {
        "poke": {"emotion": "tease", "vfx": ("sparkle", "veil")},
        "comfort": {"emotion": "warm", "vfx": ("flush", "veil")},
        "hug": {"emotion": "tease", "vfx": ("heart", "veil")},
        "pat": {"emotion": "warm"},
        "cheek": {"emotion": "tease", "vfx": ("ice", "flush")},
    },
    "hyacine": {
        "poke": {"emotion": "surprise"},
        "pat": {"emotion": "joy"},
        "comfort": {"emotion": "warm", "vfx": ("flower", "flush")},
        "hug": {"emotion": "joy"},
        "gift": {"emotion": "joy"},
    },
    "hysilens": {
        "poke": {"emotion": "surprise"},
        "gift": {"emotion": "joy", "vfx": ("note", "heart")},
        "pat": {"emotion": "warm", "vfx": ("note", "flush")},
        "comfort": {"emotion": "warm", "vfx": ("note", "flower")},
        "wave": {"emotion": "calm", "vfx": ("note", "sparkle")},
    },
    "mydei": {
        "poke": {"emotion": "anger", "vfx": ("vein", "steam")},
        "tease": {"emotion": "anger", "vfx": ("vein",)},
        "pat": {"emotion": "tease"},
        "hug": {"emotion": "warm"},
        "cheek": {"emotion": "surprise", "vfx": ("bang", "vein")},
    },
    "phainon": {
        "poke": {"emotion": "surprise"},
        "pat": {"emotion": "joy"},
        "hug": {"emotion": "joy"},
        "wave": {"emotion": "joy"},
        "gift": {"emotion": "joy"},
    },
    "tribbie": {
        "poke": {"emotion": "surprise", "vfx": ("bang", "dizzy")},
        "pat": {"emotion": "joy"},
        "tease": {"emotion": "joy"},
        "wave": {"emotion": "joy"},
        "cheek": {"emotion": "surprise", "vfx": ("flush", "dizzy")},
    },
}

# Hover-key map (parent page; ignored while typing).
KEY_GESTURES: dict[str, str] = {
    "p": "pat",
    "h": "hug",
    "f": "hands",
    "w": "wave",
    "c": "comfort",
    "g": "gift",
    "b": "bow",
    "t": "forehead",
    "k": "cheek",
}

# On-stage legend so the visitor can learn the combos.
INPUT_LEGEND: tuple[tuple[str, str], ...] = (
    ("Click", "stand near / away"),
    ("Double-click", "only them"),
    ("Drag", "rearrange"),
    ("Right-click", "more gestures"),
    ("Shift+click", "pat the head"),
    ("Ctrl+click", "poke"),
    ("Alt+click", "tease"),
    ("Shift+right-click", "hold hands"),
    ("Ctrl+right-click", "comfort"),
    ("Alt+right-click", "wave"),
    ("Shift+double-click", "forehead tap"),
    ("Ctrl+double-click", "hug"),
    ("Alt+double-click", "bow"),
    ("Ctrl+Shift+click", "gift-touch"),
    ("Alt+Shift+click", "cheek poke"),
    ("Keys while hovering", "P pat · H hug · F hands · W wave · C comfort · G gift · B bow · T forehead · K cheek"),
)

ASK_USER_LINE = "How did that feel?"


def legend_html() -> str:
    rows = "<br>".join(
        f"{_esc(src)} — {_esc(act)}" for src, act in INPUT_LEGEND
    )
    return (
        '<div class="legend" data-amp-legend="1">'
        f"{rows}"
        "</div>"
    )


def legend_caption() -> str:
    return (
        "Click near · double-click only them · drag to move · right-click for more. "
        "Shift+click pat · Ctrl+click poke · Alt+click tease · Shift+right-click hands. "
        "Hover keys: P pat, H hug, F hands, W wave, C comfort, G gift, B bow, T forehead, K cheek."
    )


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _unique(marks: Iterable[str]) -> tuple[str, ...]:
    seen = []
    allowed = set(VFX_MARKS)
    for m in marks:
        key = str(m or "").strip().lower()
        if key in allowed and key not in seen:
            seen.append(key)
    return tuple(seen)


def reaction_for(character_id: str, gesture: str) -> Optional[dict]:
    """Map a gesture to emotion / VFX / mood. No spoken line."""
    spec = GESTURES.get((gesture or "").strip().lower())
    if not spec:
        return None
    cid = str(character_id or "").strip()
    gid = (gesture or "").strip().lower()
    over = (TEMPERAMENT.get(cid) or {}).get(gid) or {}
    emotion = normalize_emotion(str(over.get("emotion") or spec["emotion"]))
    vfx = over.get("vfx")
    if vfx:
        marks = _unique(list(vfx) + list(vfx_for(emotion)))
    else:
        marks = _unique(list(spec["vfx"]) + list(vfx_for(emotion)))
    return {
        "gesture": gid,
        "label": spec["label"],
        "emotion": emotion,
        "vfx": marks,
        "mood": int(spec["mood"]),
        "reason": spec["reason"],
        "social": bool(spec["social"]),
        "join_near": bool(spec["join_near"]),
    }


def overlay_fresh(row: Optional[dict], *, now: Optional[float] = None) -> bool:
    if not isinstance(row, dict):
        return False
    try:
        ts = float(row.get("ts") or 0)
    except Exception:
        return False
    ttl = WITNESS_TTL if row.get("witness") else GESTURE_TTL
    stamp = time.time() if now is None else float(now)
    return (stamp - ts) < ttl


def prune_overlay(overlay: Optional[dict], *, now: Optional[float] = None) -> dict:
    out = {}
    for cid, row in dict(overlay or {}).items():
        if overlay_fresh(row, now=now):
            out[cid] = dict(row)
    return out


def last_gesture_of(overlay: Optional[dict], character_id: str) -> Optional[dict]:
    row = (overlay or {}).get(character_id)
    if overlay_fresh(row):
        return dict(row)
    return None


def _nudge_mood(world, character_id: str, delta: int, reason: str) -> None:
    if world is None:
        return
    try:
        from src.world import living_world as lw
        lw.set_mood(world, character_id, int(delta), reason)
        return
    except Exception:
        pass
    m = getattr(world, "mood", None)
    if not isinstance(m, dict):
        world.mood = {}
        m = world.mood
    cur = m.get(character_id) or {}
    try:
        valence = int(cur.get("valence", 0) or 0) + int(delta)
    except Exception:
        valence = int(delta)
    valence = max(-3, min(3, valence))
    ts = ""
    try:
        ts = world.clock.format_short()
    except Exception:
        ts = str(cur.get("ts") or "")
    m[character_id] = {
        "valence": valence,
        "reason": reason,
        "ts": ts,
    }


def apply_gesture(
    character_id: str,
    gesture: str,
    *,
    world=None,
    overlay: Optional[dict] = None,
    near: Optional[Iterable[str]] = None,
    now: Optional[float] = None,
) -> dict:
    """Touch on the page: VFX + pose bias + mood. Never calls chat."""
    from src.world.eternal_page import all_ids

    cid = str(character_id or "").strip()
    reacted = reaction_for(cid, gesture)
    if not reacted or cid not in all_ids():
        return {"ok": False, "id": cid, "gesture": gesture, "overlay": dict(overlay or {})}

    if world is None:
        try:
            from src.world.world_state import WorldState
            world = WorldState()
        except Exception:
            world = None

    stamp = time.time() if now is None else float(now)
    out = prune_overlay(overlay, now=stamp)
    vfx = list(reacted["vfx"])
    row = {
        "gesture": reacted["gesture"],
        "emotion": reacted["emotion"],
        "vfx": vfx,
        "reason": reacted["reason"],
        "ts": stamp,
        "witness": False,
    }
    out[cid] = row
    _nudge_mood(world, cid, reacted["mood"], reacted["reason"])

    members = [c for c in (near or []) if c in all_ids() and c != cid]
    if reacted["social"] and members:
        witness_emotion = "warm" if reacted["emotion"] in {"joy", "warm", "calm"} else reacted["emotion"]
        witness_vfx = _unique(("heart", "sparkle") if reacted["gesture"] in {"hands", "hug"} else ("sparkle",))
        for other in members:
            out[other] = {
                "gesture": reacted["gesture"],
                "emotion": witness_emotion,
                "vfx": list(witness_vfx),
                "reason": reacted["reason"],
                "ts": stamp,
                "witness": True,
            }
            _nudge_mood(world, other, 0, reacted["reason"])

    if world is not None:
        try:
            world.save()
        except Exception:
            pass

    return {
        "ok": True,
        "id": cid,
        "gesture": reacted["gesture"],
        "emotion": reacted["emotion"],
        "vfx": tuple(vfx),
        "reason": reacted["reason"],
        "join_near": reacted["join_near"],
        "social": reacted["social"],
        "overlay": out,
    }


def _q(params: dict, key: str) -> str:
    raw = params.get(key) if isinstance(params, dict) else None
    if raw is None:
        return ""
    if isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else ""
    return str(raw).strip()


def commands_from_query(params: Optional[dict]) -> list[str]:
    """Bridge query params → parse_command strings (including ep_act/ep_id)."""
    params = params or {}
    out: list[str] = []
    click = _q(params, "ep_click")
    if click:
        out.append(f"click:{click}")
    solo = _q(params, "ep_solo")
    if solo:
        out.append(f"solo:{solo}")
    pet = _q(params, "ep_pet")
    if pet:
        out.append(f"pet:{pet}")
    drag = _q(params, "ep_drag")
    if drag:
        parts = [p.strip() for p in drag.split(",")]
        if len(parts) >= 3:
            out.append(f"drag:{parts[0]}:{parts[1]}:{parts[2]}")
    act = _q(params, "ep_act").lower()
    eid = _q(params, "ep_id")
    if act and eid:
        out.append(f"{act}:{eid}")
    return out


def vfx_class_names() -> tuple[str, ...]:
    return tuple(f"mk-{name}" for name in VFX_MARKS)
