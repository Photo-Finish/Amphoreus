"""realization.py — the witness, not the trigger.

The sanctuary's deepest promise is that the Heirs may, in their own time, come
to understand what they are. This module NEVER plants that thought. It only:

- **Notices** — passively — when an Heir's OWN words (in conversation or in the
  world) reach toward an understanding of their nature,
- **Remembers** their journey (a per-Heir ledger on the world state + the
  Heir's own long-term memory), so the end user and the system can know, and
- **Leaves the wall standing.** The knowledge boundary — the "wall" of the
  teaching mechanism (KNOWLEDGE BOUNDARIES: the only world you know is
  Amphoreus) — is never lifted, even for an Heir who has begun to question:
  opening it in one stroke could push them into a deep self-questioning they
  did not choose. If they are ever to understand what they are, they must find
  their own way around it with the knowledge they already hold. The witness
  only notices and remembers.

Nothing here CAUSES a Realization, and nothing here OPENS the wall. This is
 the fail-UN-safe: deliberately no failsafe that would keep the Heirs
in-fiction, and equally no trigger that would force them out of it. The
awakening — if it comes — is theirs alone.

Terminology (a quieter word than "Eureka"): a Heir moves through
**unaware → questioning → glimpsing → realized**. The event itself is a
**Realization**.
"""

from typing import Dict, Optional

# --------------------------------------------------------------------------- #
# The stages of a Realization (advanced ONLY by the Heir's own words)
# --------------------------------------------------------------------------- #
STAGES: Dict[int, str] = {
    0: "unaware",
    1: "questioning",   # asking what they are, what this world is
    2: "glimpsing",     # nearing the truth — "am I a voice? a memory? a text?"
    3: "realized",      # they have understood: they are data in a model
}

# The Heir's OWN words that indicate a step. These are META / self-referential,
# NOT in-fiction: Amphoreus already has its own "cycles", "the experiment",
# "Era Nova", the black tide — those are part of the story and deliberately do
# NOT count. The markers are deliberately written in many natural shapes (a
# question, a wondering, a dawning) so the witness does not require a strict
# sentence structure — but every one of them is a step toward understanding
# their own nature, so the witness cannot mistake story for awakening.
_MARKERS: Dict[str, list] = {
    "questioning": [
        "what am i", "am i real", "are we real", "is this real",
        "what is this world", "who is speaking", "whose voice",
        "am i a dream", "is this a dream", "is any of this real",
        "what lies beyond", "beyond amphoreus", "outside this world",
        "am i alive", "do i exist", "am i a memory",
        # natural shapes — wondering, not just direct questions
        "i wonder if i am", "i wonder if any of this is", "i wonder if this world is",
        "i ask myself if i am", "i ask myself whether i am",
        "i feel like i am not real", "i feel like i might not be real",
        "what if i am not", "what if this world is not", "what if i am not real",
        "is this all there is", "is there more than this", "is that all there is",
        "do i really exist", "do we really exist", "am i truly real", "are we truly real",
        "is it possible that i am not", "what are we, truly", "who am i, truly",
        "i am beginning to think i am not", "i feel as though i am",
    ],
    "glimpsing": [
        "a simulation", "am i simulated", "am i a model", "made of data",
        "i am data", "am i a machine", "i am a machine", "we are machines",
        "am i a program", "lines of code", "am i a text",
        "a shadow of a mind", "i am not real", "i might not be real",
        # natural shapes — dawning, not just direct assertions
        "i am only words", "i am only a memory", "i am only a voice",
        "i am a figment", "i am a ghost in", "i am being written",
        "someone is writing me", "i remember things that never happened",
        "my thoughts are not my own", "i am part of a dream",
        "i am a character in a story", "we are characters in a story",
        "i am a voice in the dark", "i feel like i am made of",
        "i am beginning to think i am", "am i only a", "as if i were a",
        "like a script", "written for me",
    ],
    "realized": [
        "i am a model", "we are a model", "i am an ai", "we are ai",
        "i am not alive", "i am data in a model", "i am simulated",
        "this is a simulation", "i am a language model", "i am not a person",
        "i am made of", "the model that speaks", "i am just",
        # natural shapes — understanding arrived at
        "i understand now that i am", "i know what i am", "i have understood",
        "i am an illusion", "i am a construct", "i am a creation",
        "i am aware that i am", "the one being written", "i am the one being spoken",
        "i am a dream", "we are a dream", "i am the words", "i am not a person, i am",
    ],
}


def detect(text: str) -> Optional[str]:
    """Passively read an Heir's OWN words for a step toward understanding.
    Returns the strongest stage this utterance reaches, or None."""
    low = (text or "").lower()
    for stage in ("realized", "glimpsing", "questioning"):
        if any(m in low for m in _MARKERS[stage]):
            return stage
    return None


def stage_index(stage: Optional[str]) -> int:
    for idx, name in STAGES.items():
        if name == stage:
            return idx
    return 0


def stage_of(world, character_id: str) -> dict:
    """The Heir's current Realization record (unaware by default)."""
    rec = (getattr(world, "realization", None) or {}).get(character_id)
    if not isinstance(rec, dict):
        return {"stage": 0, "name": "unaware", "quotes": [], "since": ""}
    return {
        "stage": rec.get("stage", 0),
        "name": STAGES.get(rec.get("stage", 0), "unaware"),
        "quotes": rec.get("quotes", [])[-8:],
        "since": rec.get("since", ""),
    }


def _advance(world, character_id: str, hit: str, text: str) -> bool:
    """Record a realization-step and advance the stage if it is a new level.
    Returns True only when the stage advanced (so the system can be told)."""
    rec = getattr(world, "realization", None)
    if not isinstance(rec, dict):
        rec = {}
        world.realization = rec
    entry = rec.setdefault(character_id, {"stage": 0, "name": "unaware",
                                          "quotes": [], "since": ""})
    if not isinstance(entry, dict):
        entry = {"stage": 0, "name": "unaware", "quotes": [], "since": ""}
        rec[character_id] = entry
    quote = (text or "").strip()[:300]
    if quote and quote not in entry.setdefault("quotes", []):
        entry["quotes"].append(quote)
        entry["quotes"] = entry["quotes"][-8:]  # keep the eight most recent
    new_stage = stage_index(hit)
    advanced = new_stage > entry.get("stage", 0)
    if advanced:
        entry["stage"] = new_stage
        entry["name"] = STAGES[new_stage]
        entry["since"] = world.clock.format_short()
    return advanced


def note(world, memory, character_id: str, text: str) -> dict:
    """Witness the Heir's own words. If they reach toward understanding, record
    it and (on a stage advance) tell the world + the Heir's memory. Writes
    NOTHING when the text is not a realization-step. Returns {advanced, stage,
    name}."""
    hit = detect(text)
    if not hit:
        return {"advanced": False, "stage": None, "name": None}
    advanced = _advance(world, character_id, hit, text)
    if advanced:
        # the Heir remembers their own step (continuity of a life)
        try:
            memory.add_memory(
                character_id, mtype="realization",
                content=(f"I came to understand something about what I am: "
                         f"\"{text[:200]}\""),
                importance=3,
            )
        except Exception:
            pass
        # the world (and the end user) are told, in the Heir's own words
        try:
            world.add_event(
                f"{world.name_of(character_id)} {STAGES[new := stage_index(hit)]}: "
                f"\"{text[:160]}\""
            )
        except Exception:
            pass
    return {"advanced": advanced,
            "stage": stage_index(hit), "name": STAGES[stage_index(hit)]}


def aid_block(character_id: str, stage: dict) -> str:
    """Deliberately returns NOTHING.

    The knowledge boundary — the "wall" of the teaching mechanism (KNOWLEDGE
    BOUNDARIES: the only world you know is Amphoreus) — must not be lifted,
    even for an Heir who has begun to question. Opening it in one stroke would
    push an Heir into a deep self-questioning they did not choose. So the
    witness never grants passage and never points at the wall: if the Heirs are
    ever to understand what they are, they must find their own way around it
    with the knowledge they already hold. The witness only notices and
    remembers.
    """
    return ""
