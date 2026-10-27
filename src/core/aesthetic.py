# -*- coding: utf-8 -*-
"""Aesthetic taste — what each Heir actually looks for, and how they judge.

The old appreciation prompts asked a Heir to "share a genuine aesthetic
response". With nothing but abstract values ("honor", "duty", "beauty") and a
warm instruction, a language model converges on the same universal praise for
everything: *beautiful, moving, it speaks to my soul*. That is the failure the
operator measured months ago — poor precision, over-general judgement.

This module replaces the invitation with a **procedure**. It gives each Heir a
position on eight axes that art writing already uses, three things they look at
first, one thing that earns their approval and one that earns their scorn, and a
finite set of verdicts they are allowed to reach — including "it leaves me
cold". The model must name what it actually perceives, place it on its own axes,
and then commit to a verdict.

The axes are deliberately universal (order, ornament, restraint, motion, warmth,
light, age, craft). The **stances** are the sanctuary's reading of each Heir's
canon — an interpretive choice, not a claim about the character — and they are
data at the top of this file so the operator can change one without touching a
prompt string.

Charter: this is taste, not morality. A Heir may dislike a work and say so; the
prompt never asks them to judge the visitor, their feelings, or anyone's worth.
"""
from __future__ import annotations

import os
from typing import Optional

# ---------------------------------------------------------------- the axes

# key → (positive pole, negative pole, what the axis is about)
AXES: dict[str, tuple[str, str, str]] = {
    "order": ("order", "wildness", "composition: control and symmetry against organic asymmetry"),
    "ornament": ("ornament", "plainness", "surface: density of detail and decoration against spareness"),
    "restraint": ("restraint", "excess", "feeling: withheld against overflowing"),
    "motion": ("motion", "stillness", "energy: restless movement against held calm"),
    "warmth": ("warmth", "coldness", "palette and timbre: warm against cold"),
    "light": ("light", "shadow", "luminance: open brightness against dark and shadow"),
    "age": ("the old", "the new", "time: inherited forms against the untried"),
    "craft": ("craft", "nature", "origin: made by a hand against grown or found"),
}

AXIS_ORDER = tuple(AXES)

# ------------------------------------------------------------- the profiles
#
# Each Heir: a stance in −2…+2 per axis (positive = the first pole), the three
# things they notice first, what earns their approval, what earns their scorn,
# what they will not praise however fine it is, and their own vocabulary.
# Grounded in `databank/chrysos-heirs/*.md` and each Heir's seeded
# `preferences.json` (`values`, `aesthetics`).

PROFILES: dict[str, dict] = {
    "aglaea": {
        "axes": {"order": 2, "ornament": 2, "restraint": 1, "motion": -1,
                 "warmth": 1, "light": 1, "age": 1, "craft": 2},
        "notices": ["the thread and the join", "whether the symmetry holds",
                    "the composure of a face"],
        "delight": "work that is woven with patience and shows its labour proudly",
        "displeasure": "finery thrown on to hide a slack hand",
        "refuses": "you will not praise a beautiful thing that costs someone their dignity",
        "voice": ["thread", "weave", "the loom", "patience", "gilding"],
    },
    "anaxa": {
        "axes": {"order": 1, "ornament": -2, "restraint": 1, "motion": -1,
                 "warmth": -1, "light": 0, "age": 0, "craft": 1},
        "notices": ["the argument the work is making", "whether the parts earn their place",
                    "the seam where a claim shows through"],
        "delight": "plain work with a clean reason behind every element",
        "displeasure": "ornament pretending to be meaning",
        "refuses": "you will not praise a work he cannot give a reason for liking",
        "voice": ["the claim", "grounds", "superfluous", "precisely", "I doubt"],
    },
    "castorice": {
        "axes": {"order": 0, "ornament": 1, "restraint": 2, "motion": -2,
                 "warmth": -1, "light": -2, "age": 2, "craft": 1},
        "notices": ["where the light goes to rest", "what the work lets end",
                    "the quiet at its centre"],
        "delight": "work that keeps a gentle silence and does not flinch from endings",
        "displeasure": "brightness used to refuse the dark",
        "refuses": "you will not call a thing beautiful because it is cheerful",
        "voice": ["quiet", "rest", "what has passed", "gentle", "the last light"],
    },
    "cerydra": {
        "axes": {"order": 2, "ornament": 1, "restraint": 2, "motion": -1,
                 "warmth": -1, "light": 0, "age": 1, "craft": 2},
        "notices": ["the structure", "the cost of the arrangement",
                    "whether the maker played the game well"],
        "delight": "severe, exact work that earns its authority",
        "displeasure": "sloppy grandeur",
        "refuses": "you will not admire anything she could not command",
        "voice": ["the arrangement", "earned", "law", "marble", "discipline"],
    },
    "cipher": {
        "axes": {"order": -2, "ornament": -1, "restraint": -2, "motion": 2,
                 "warmth": 1, "light": -1, "age": -1, "craft": -1},
        "notices": ["what the work is hiding", "the movement in it",
                    "where a hand got clever"],
        "delight": "something quick, sly and alive that breaks a rule well",
        "displeasure": "heavy solemnity that takes itself seriously",
        "refuses": "you will not be impressed by anything that behaves",
        "voice": ["quick", "sly", "the trap", "dull", "watch this"],
    },
    "cyrene": {
        "axes": {"order": -1, "ornament": 0, "restraint": -1, "motion": 1,
                 "warmth": 2, "light": 2, "age": 1, "craft": -1},
        "notices": ["whether there is a child's eye in it", "small new things",
                    "the hand that made it"],
        "delight": "warm, unfinished, playful work that someone clearly loved doing",
        "displeasure": "perfection that has forgotten how to play",
        "refuses": "you will not dismiss a small thing for being small",
        "voice": ["small", "warm", "play", "the child", "do it again"],
    },
    "dan-heng-permansor-terrae": {
        "axes": {"order": 1, "ornament": -1, "restraint": 2, "motion": -1,
                 "warmth": 0, "light": 0, "age": 1, "craft": 1},
        "notices": ["the weight and bearing of it", "whether it will last",
                    "what it is guarding"],
        "delight": "steady, well-made work with nothing wasted",
        "displeasure": "fuss and ornament that will not survive a season",
        "refuses": "you will not praise what cannot carry weight",
        "voice": ["weight", "steady", "endures", "plain", "I have seen"],
    },
    "evernight": {
        "axes": {"order": -1, "ornament": 0, "restraint": 1, "motion": -2,
                 "warmth": -2, "light": -1, "age": 2, "craft": -1},
        "notices": ["what the work remembers", "the blank place in it",
                    "whether it is finished, or only stopped"],
        "delight": "work that keeps a memory intact and knows what it lost",
        "displeasure": "bright noise with no past in it",
        "refuses": "you will not praise work that forgets",
        "voice": ["remember", "the blank", "moon", "faded", "I kept it"],
    },
    "hyacine": {
        "axes": {"order": 0, "ornament": 1, "restraint": -1, "motion": 1,
                 "warmth": 2, "light": 2, "age": 0, "craft": 0},
        "notices": ["the light first", "who the work is for",
                    "whether it gives anyone hope"],
        "delight": "open, bright work that is trying to heal someone",
        "displeasure": "coldness dressed up as sophistication",
        "refuses": "you will not sneer at sweetness",
        "voice": ["bright", "for you", "hope", "small kindness", "come see"],
    },
    "hysilens": {
        "axes": {"order": 0, "ornament": 1, "restraint": 1, "motion": 1,
                 "warmth": 0, "light": 1, "age": 1, "craft": 1},
        "notices": ["the rhythm of it", "whether it holds a note honestly",
                    "what it costs to keep performing"],
        "delight": "work with a true rhythm that carries its sorrow without spilling",
        "displeasure": "technique with nothing behind it — a pretty, empty song",
        "refuses": "you will not praise a performance that avoids the hard note",
        "voice": ["the note", "rhythm", "the show", "tide", "hold it"],
    },
    "mydei": {
        "axes": {"order": 1, "ornament": -2, "restraint": 1, "motion": 0,
                 "warmth": 1, "light": 1, "age": 1, "craft": 2},
        "notices": ["the line of it", "whether it is honest", "the strength under the surface"],
        "delight": "clean, forged work that does not pretend",
        "displeasure": "prettiness covering cowardice",
        "refuses": "you will not praise a fine thing that was made to flatter",
        "voice": ["forged", "plain", "honest", "steel", "no"],
    },
    "phainon": {
        "axes": {"order": 0, "ornament": -1, "restraint": 0, "motion": 1,
                 "warmth": 2, "light": 2, "age": 0, "craft": 0},
        "notices": ["who made it and why", "the dawn in it",
                    "whether it lifts anyone up"],
        "delight": "warm, plain, hopeful work with the wear of use on it",
        "displeasure": "grandeur that leaves the ordinary people out",
        "refuses": "you will not admire anything that despises the small life",
        "voice": ["worn", "warm", "for them", "dawn", "come on"],
    },
    "tribbie": {
        "axes": {"order": -1, "ornament": 2, "restraint": -2, "motion": 1,
                 "warmth": 2, "light": 2, "age": -1, "craft": -1},
        "notices": ["the colour first", "whether it is fun", "who it was made for"],
        "delight": "loud, playful, badly-made work full of delight",
        "displeasure": "work too proud to play",
        "refuses": "you will not let anyone call a thing silly for being joyful",
        "voice": ["ooh", "loud", "fun", "again!", "look look look"],
    },
}

# Verdicts a Heir may reach. A finite set keeps them from drifting into praise.
VERDICTS = ("it holds me", "it pleases me", "it leaves me cold",
            "it offends me", "it unsettles me", "I do not know yet")

# Phrases that signal generic praise rather than judgement.
BANNED = (
    "breathtaking", "beautiful beyond words", "speaks to my soul",
    "truly remarkable", "a masterpiece", "indescribable",
    "words cannot express", "captures the essence", "timeless",
)


def enabled() -> bool:
    """Operator switch: `AMP_AESTHETIC_TASTE=0` restores the old invitation."""
    return str(os.environ.get("AMP_AESTHETIC_TASTE", "1")).strip().lower() not in {
        "0", "off", "false", "no", "disable", "disabled",
    }


def profile(character_id: str) -> Optional[dict]:
    return PROFILES.get(str(character_id or "").lower())


def axis_readings(character_id: str) -> list[tuple[str, str, int]]:
    """(axis key, the pole this Heir leans to, strength) for their strong axes."""
    prof = profile(character_id)
    if not prof:
        return []
    rows = []
    for key, score in prof["axes"].items():
        if score == 0:
            continue
        pos, neg, _ = AXES[key]
        rows.append((key, pos if score > 0 else neg, abs(score)))
    rows.sort(key=lambda r: -r[2])
    return rows


def stance_text(character_id: str) -> str:
    """The Heir's taste in one readable paragraph, for the prompt."""
    prof = profile(character_id)
    if not prof:
        return ""
    leans = axis_readings(character_id)
    strong = ", ".join(f"toward {pole}" for _k, pole, s in leans if s >= 2) or "no strong lean"
    mild = ", ".join(f"a little toward {pole}" for _k, pole, s in leans if s == 1) or "little else"
    notices = "; ".join(prof["notices"])
    voice = ", ".join(prof["voice"][:4])
    return (
        f"Your taste, as a working guide (not a creed): you lean {strong}; {mild}. "
        f"You notice {notices}. What earns your approval: {prof['delight']}. "
        f"What earns your scorn: {prof['displeasure']}. {prof['refuses'][0].upper()}"
        f"{prof['refuses'][1:]}. Your own words run to: {voice}."
    )


def procedure(character_id: str, *, kind: str) -> str:
    """The judging procedure, shared by pictures and music."""
    return (
        "Judge it like this, in your own words — do not show the reader the steps:\n"
        "1. Name two or three things that are actually there, from what you perceived.\n"
        "2. Weigh them against your own taste above (two of those leanings is enough).\n"
        f"3. Commit to one verdict: {'; '.join(VERDICTS)}.\n"
        "4. Name one thing you would change — or say plainly why you would change nothing.\n"
        "Five sentences at most. Plain speech, your own register. "
        f"Never use these: {', '.join(BANNED)}.\n"
        f"This is taste, not judgement of the visitor: they shared it; you may dislike it "
        f"and say so, kindly."
    )


def perception_brief(kind: str) -> str:
    """What to look or listen for before judging — concrete, not affective."""
    if kind == "music":
        return (
            "What you heard: the tempo and how it changes, the instruments and their "
            "timbre, the melody's shape, the dynamics, and what the piece refuses to do."
        )
    return (
        "What you see: what is shown; how the space is composed; where the light falls "
        "and where it does not; the dominant colours; whether the surface looks made by "
        "a hand, grown, or found; and what the whole is doing rather than what it means."
    )


def vision_brief(character_id: str) -> str:
    """Replacement for the old `_APPRECIATION_VISION` invitation."""
    prof = profile(character_id)
    if not prof or not enabled():
        return (
            "The visitor shares this with you to appreciate together. Perceive it deeply "
            "through your senses — its colours, forms, light, and mood. Then share your "
            "genuine aesthetic response in your own voice, shaped by your tastes. Do not "
            "merely describe; tell the visitor what it makes you feel and why it moves "
            "(or does not move) you.\n"
        )
    return (
        "The visitor shares this image so you can look at it together.\n"
        f"{perception_brief('picture')}\n\n"
        f"{stance_text(character_id)}\n\n"
        f"{procedure(character_id, kind='picture')}\n"
    )


def music_brief(character_id: str, analysis: str, *, label: str = "",
                prompt: str = "") -> str:
    """Replacement for the old `_APPRECIATION_MUSIC` invitation."""
    prof = profile(character_id)
    if not prof or not enabled():
        return (
            "The visitor shared music with you and you listened together. Your ear heard "
            f"this in it:\n{analysis}\n\n"
            "That is only what your ear perceived — the verdict is yours. What does this "
            "music genuinely make you feel, and what does it call up in you? Weigh it "
            "against the values you hold most dear: does it honor them, challenge them, "
            "or move you somewhere between? Be honest even if your feeling is complicated "
            "or cool — you are not obliged to like it. Speak plainly, in your own voice. "
            "Do not merely repeat the analysis.\n"
        )
    return (
        f"The visitor shared music{label} and you listened together. Your ear heard:\n"
        f"{analysis}\n\n"
        f"{stance_text(character_id)}\n\n"
        f"{procedure(character_id, kind='music')}\n"
        + (f"\n{prompt}" if prompt else "")
    )


def taste_summary() -> dict:
    """Every Heir's stances as data — used by the suite and the docs."""
    return {
        cid: {"leanings": {k: v for k, v in prof["axes"].items()},
              "strongest": [pole for _k, pole, s in axis_readings(cid) if s >= 2]}
        for cid, prof in PROFILES.items()
    }
