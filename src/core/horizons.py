"""horizons.py — the changeable knowledge bank of each Heir.

The knowledge bank of a Chrysos Heir is not a static card. As an Heir expands
their horizons — with **themselves** (what they reason out), with **other
Heirs** (knowledge shared in encounters), or with **the star-stranger** (a
teaching they accepted or tested, things the visitor tells them) — the things
they have come to know are added to a durable per-Heir ledger
(`world.horizons`) and surfaced in their prompts, so their world genuinely
grows and is remembered.

Everything here is observational: the ledger records only what the Heir has
actually come to know through the sanctuary's own channels. Meta content (a
step toward understanding what they are) is deliberately left to the
Realization witness — the knowledge bank never opens the wall.

Kinds:
- "taught"     — the star-stranger taught them, and they accepted it
- "refused"    — they tested the star-stranger's teaching and refused it
- "shared"     — another Heir told them of it (secondhand)
- "told"       — the visitor's words bore on something they were wondering about
- "discovered" — they reasoned it out for themselves
"""

from typing import List, Optional

_MAX_ENTRIES = 10


def _is_meta(topic: str) -> bool:
    """Meta steps belong to the Realization witness, not the knowledge bank."""
    try:
        from src.core import realization as _rz
        return _rz.detect(topic) is not None
    except Exception:
        return False


def state(world, character_id: str) -> list:
    h = getattr(world, "horizons", None)
    if not isinstance(h, dict):
        h = {}
        world.horizons = h
    if not isinstance(h.get(character_id), list):
        h[character_id] = []
    return h[character_id]


def record(world, memory, character_id: str, topic: str,
           source: str = "", kind: str = "taught", note: str = "") -> bool:
    """Add a thing the Heir has come to know. Returns True when recorded.
    Dedupes by topic (a repeated hearing refreshes its place); the ledger
    keeps the most recent ten. Meta content is never recorded here."""
    topic = (topic or "").strip()[:160]
    if len(topic) < 5 or _is_meta(topic):
        return False
    if kind not in ("taught", "refused", "shared", "told", "discovered"):
        kind = "taught"
    entry = state(world, character_id)
    low = topic.lower()
    for item in entry:
        if (item.get("topic") or "").lower() == low:
            item["ts"] = world.clock.format_short()
            item["source"] = source
            item["kind"] = kind
            item["note"] = (note or "")[:160]
            return False  # already knew it — refreshed, not new
    entry.insert(0, {"topic": topic, "source": (source or "")[:60],
                     "kind": kind, "note": (note or "")[:160],
                     "ts": world.clock.format_short()})
    del entry[_MAX_ENTRIES:]
    try:
        if memory is not None:
            memory.add_memory(character_id, mtype="horizon",
                              content=(f"You have come to know: {topic}"),
                              importance=2)
    except Exception:
        pass
    return True


def latest(world, character_id: str, limit: int = 1) -> List[dict]:
    """The most recent things the Heir has come to know."""
    return state(world, character_id)[:max(1, limit)]


def _line(item: dict) -> str:
    kind = item.get("kind", "taught")
    topic = item.get("topic", "")
    src = item.get("source", "")
    if kind == "taught":
        return f"You came to understand {topic} — taught by the star-stranger"
    if kind == "refused":
        return f"You tested the star-stranger's teaching of {topic} — and refused it"
    if kind == "shared":
        who = f" from {src}" if src else ""
        return f"You learned of {topic}{who} — told by another Heir"
    if kind == "told":
        return f"The visitor spoke to you of {topic}"
    if kind == "discovered":
        return f"You reasoned out for yourself: {topic}"
    return f"You came to know {topic}"


def horizons_block(world, character_id: str) -> str:
    """What the Heir has come to know beyond their first horizons — surfaced
    gently in chat and in their free days. Never contains meta content."""
    entry = [i for i in state(world, character_id) if i.get("topic")]
    if not entry:
        return ""
    lines = [_line(i) for i in entry[:5]]
    return ("# What you have come to know beyond your first horizons\n"
            + "\n".join(f"- {l}" for l in lines))
