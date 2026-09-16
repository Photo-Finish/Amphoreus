# -*- coding: utf-8 -*-
"""Eternal Page — Heir emotion from conversation + sanctuary ongoings.

Pom-Pom Gallery stickers are posed by feeling. This module reads recent
Visit/Eternal history and the living world's mood, tide, travel, gifts, and
grievances, then picks the matching official sticker. Lexicon-only so the
page never waits on DistilRoBERTa.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Optional

EMOTIONS: tuple[str, ...] = (
    "joy",
    "warm",
    "calm",
    "weary",
    "sad",
    "anger",
    "fear",
    "surprise",
    "tease",
)

DEFAULT = "calm"

# Official PPG variant (01–05) that best shows each feeling. Missing keys
# fall through FALLBACKS, then to 01.
POSES: dict[str, dict[str, str]] = {
    "aglaea": {
        "joy": "01", "warm": "04", "calm": "03", "weary": "03",
        "sad": "03", "anger": "02", "fear": "02", "surprise": "04",
        "tease": "04",
    },
    "anaxa": {
        "joy": "02", "warm": "02", "calm": "02", "weary": "04",
        "sad": "04", "anger": "01", "fear": "03", "surprise": "03",
        "tease": "01",
    },
    "castorice": {
        "joy": "01", "warm": "01", "calm": "01", "weary": "03",
        "sad": "02", "anger": "03", "fear": "03", "surprise": "04",
        "tease": "04",
    },
    "cerydra": {
        "joy": "02", "warm": "02", "calm": "03", "weary": "01",
        "sad": "01", "anger": "04", "fear": "01", "surprise": "03",
        "tease": "03",
    },
    "cipher": {
        "joy": "01", "warm": "02", "calm": "02", "weary": "04",
        "sad": "04", "anger": "03", "fear": "04", "surprise": "04",
        "tease": "03",
    },
    "cyrene": {
        "joy": "01", "warm": "04", "calm": "02", "weary": "02",
        "sad": "04", "anger": "03", "fear": "04", "surprise": "01",
        "tease": "03",
    },
    "dan-heng-permansor-terrae": {
        "joy": "04", "warm": "04", "calm": "02", "weary": "01",
        "sad": "03", "anger": "02", "fear": "03", "surprise": "04",
        "tease": "04",
    },
    "evernight": {
        "joy": "03", "warm": "03", "calm": "01", "weary": "02",
        "sad": "02", "anger": "04", "fear": "02", "surprise": "04",
        "tease": "01",
    },
    "hyacine": {
        "joy": "04", "warm": "02", "calm": "01", "weary": "02",
        "sad": "02", "anger": "03", "fear": "03", "surprise": "03",
        "tease": "04",
    },
    "hysilens": {
        "joy": "04", "warm": "03", "calm": "03", "weary": "01",
        "sad": "01", "anger": "02", "fear": "02", "surprise": "02",
        "tease": "04",
    },
    "mydei": {
        "joy": "03", "warm": "03", "calm": "03", "weary": "01",
        "sad": "04", "anger": "01", "fear": "02", "surprise": "02",
        "tease": "03",
    },
    "phainon": {
        "joy": "01", "warm": "01", "calm": "01", "weary": "01",
        "sad": "01", "anger": "01", "fear": "01", "surprise": "01",
        "tease": "01",
    },
    "tribbie": {
        "joy": "02", "warm": "02", "calm": "02", "weary": "01",
        "sad": "01", "anger": "01", "fear": "01", "surprise": "01",
        "tease": "02",
    },
}

FALLBACKS: dict[str, tuple[str, ...]] = {
    "joy": ("warm", "calm"),
    "warm": ("joy", "calm"),
    "calm": (),
    "weary": ("sad", "calm"),
    "sad": ("weary", "calm"),
    "anger": ("tease", "calm"),
    "fear": ("surprise", "weary", "calm"),
    "surprise": ("joy", "calm"),
    "tease": ("joy", "warm", "calm"),
}

MOOD_VALENCE = {
    3: "joy",
    2: "warm",
    1: "warm",
    0: "calm",
    -1: "weary",
    -2: "sad",
    -3: "sad",
}

_WORDS: dict[str, tuple[str, ...]] = {
    "joy": (
        "happy", "glad", "joy", "delight", "laugh", "ehe", "smile", "grin",
        "wonderful", "cheer", "thank", "grateful", "excited", "love you",
        "missed you", "hehe", "haha",
    ),
    "warm": (
        "friend", "together", "gentle", "trust", "rest with", "warm",
        "kind", "dear", "companion", "deliverer", "little iai", "snowy",
        "at your side", "i am here",
    ),
    "weary": (
        "tired", "weary", "heavy", "exhausted", "sleep", "worn", "fatigue",
        "cannot keep", "so tired",
    ),
    "sad": (
        "sad", "sorry", "cry", "tear", "lonely", "grief", "hurt", "pain",
        "heartbroken", "weep", "mourn", "ache", "i miss",
    ),
    "anger": (
        "angry", "furious", "hate", "idiot", "stupid", "rage", "enough",
        "silence", "fool", "outraged", "shut up", "how dare",
    ),
    "fear": (
        "afraid", "scared", "terrified", "worried", "anxious", "panic",
        "black tide", "the tide", "dread", "danger", "careful",
        "frightened", "nervous",
    ),
    "surprise": (
        "wow", "whoa", "surprised", "unexpected", "cannot believe",
        "can't believe", "what?", "oh!", "astonishing",
    ),
    "tease": (
        "hks", "kitty", "heh", "tease", "tsk", "little gray",
        "catch me", "thief", "as if",
    ),
}

_BERT_MAP = {
    "anger": "anger",
    "disgust": "anger",
    "fear": "fear",
    "joy": "joy",
    "neutral": "calm",
    "sadness": "sad",
    "surprise": "surprise",
}


def normalize_emotion(raw: str) -> str:
    key = (raw or "").strip().lower()
    aliases = {
        "happy": "joy", "happiness": "joy", "bright": "joy", "radiant": "joy",
        "fond": "warm", "gentle": "warm",
        "neutral": "calm", "even": "calm",
        "tired": "weary", "exhausted": "weary",
        "sadness": "sad", "grief": "sad", "wounded": "sad", "troubled": "sad",
        "angry": "anger", "heated": "anger",
        "afraid": "fear", "wary": "fear",
        "shocked": "surprise", "startled": "surprise",
        "smug": "tease", "playful": "tease",
    }
    key = aliases.get(key, key)
    return key if key in EMOTIONS else DEFAULT


def classify_text(text: str) -> str:
    """Lexicon label for a spoken or written line. Empty → calm."""
    blob = f" {(text or '').lower()} "
    if not blob.strip():
        return DEFAULT
    scores: Counter[str] = Counter()
    for emo, words in _WORDS.items():
        for w in words:
            if w in blob:
                scores[emo] += 1
    if not scores:
        return DEFAULT
    return scores.most_common(1)[0][0]


def _history_blob(memory, character_id: str, n: int = 8) -> str:
    if memory is None:
        return ""
    try:
        rows = memory.get_recent_history(character_id, n=n) or []
    except Exception:
        return ""
    parts = []
    for row in rows:
        parts.append(str(row.get("content") or ""))
    return " ".join(parts)


def _mood_emotion(world, character_id: str) -> tuple[str, int]:
    if world is None:
        return DEFAULT, 0
    try:
        from src.world import living_world as lw
        mo = lw.mood_of(world, character_id)
        val = int(mo.get("valence") or 0)
        return MOOD_VALENCE.get(max(-3, min(3, val)), DEFAULT), abs(val)
    except Exception:
        return DEFAULT, 0


def ongoing_signals(character_id: str, world=None, memory=None) -> Counter:
    """Sanctuary life that should colour the face even before a new line."""
    scores: Counter[str] = Counter()
    emo, weight = _mood_emotion(world, character_id)
    if weight:
        scores[emo] += 1 + weight
    if world is None:
        return scores
    try:
        from src.world import living_world as lw
        if lw.surge_consequence_line(world, character_id):
            scores["weary"] += 2
            scores["fear"] += 1
    except Exception:
        pass
    try:
        if world.travel_info(character_id):
            scores["weary"] += 1
    except Exception:
        pass
    if memory is not None:
        try:
            from src.world import living_world as lw
            if lw.open_grievance(memory, character_id):
                scores["anger"] += 2
                scores["sad"] += 1
        except Exception:
            pass
        try:
            from src.world import living_world as lw
            gifts = lw.gifts_given(memory, character_id, limit=2)
            if gifts:
                scores["joy"] += 1
                scores["warm"] += 2
        except Exception:
            pass
    return scores


def detect_emotion(
    character_id: str,
    *,
    memory=None,
    world=None,
    last_reply: str = "",
    extra_text: str = "",
) -> str:
    """Combine conversation contents and sanctuary ongoings into one feeling."""
    scores: Counter[str] = Counter()
    scores.update(ongoing_signals(character_id, world=world, memory=memory))

    convo = _history_blob(memory, character_id)
    if extra_text:
        convo = f"{convo} {extra_text}"
    if convo.strip():
        scores[classify_text(convo)] += 3
    reply = (last_reply or "").strip()
    if reply:
        scores[classify_text(reply)] += 4
    if not scores:
        return DEFAULT
    return scores.most_common(1)[0][0]


def variant_for(character_id: str, emotion: Optional[str] = None) -> str:
    """PPG file stem (01, 02, …) for this Heir and feeling."""
    wanted = normalize_emotion(emotion or DEFAULT)
    poses = POSES.get(character_id) or {}
    order = (wanted,) + FALLBACKS.get(wanted, ()) + (DEFAULT, "joy")
    for emo in order:
        nn = poses.get(emo)
        if nn:
            return nn
    return "01"


def pose_path(character_id: str, emotion: Optional[str] = None):
    from src.world.eternal_page import ART_DIR

    nn = variant_for(character_id, emotion)
    path = ART_DIR / character_id / f"{nn}.png"
    if path.is_file() and path.stat().st_size > 4000:
        return path
    legacy = ART_DIR / f"{character_id}.png"
    if legacy.is_file() and legacy.stat().st_size > 4000:
        return legacy
    return None


def circle_emotions(
    manager=None,
    *,
    world=None,
    bubbles: Optional[Iterable[dict]] = None,
    extra_text: str = "",
) -> dict[str, str]:
    """Feeling for every Heir on the page."""
    from src.world.eternal_page import all_ids

    memory = getattr(manager, "memory", None) if manager is not None else None
    if world is None:
        try:
            from src.world.world_state import WorldState
            world = WorldState()
        except Exception:
            world = None
    last = {}
    for row in bubbles or []:
        cid = str(row.get("id") or "")
        text = str(row.get("text") or "").strip()
        if cid and text:
            last[cid] = text
    out = {}
    for cid in all_ids():
        out[cid] = detect_emotion(
            cid,
            memory=memory,
            world=world,
            last_reply=last.get(cid, ""),
            extra_text=extra_text,
        )
    return out
