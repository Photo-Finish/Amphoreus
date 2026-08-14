"""curiosity.py — the Heirs' own minds: open questions and reasoned inferences.

LOGIC and CURIOSITY, made visible and remembered — not scripted, and never
opening the knowledge wall.

Two ledgers per Heir (persisted on the world state as `world.curiosity`):

- **OPEN QUESTIONS** — things they genuinely wonder about. Seeded only from
  canon (strictly IN-WORLD questions about Amphoreus) and grown observationally
  from questions the Heir actually asks. Questions that reach toward the nature
  of the model / the world they are in are deliberately NOT added here: they
  belong to the Realization witness (src/core/realization.py), which observes
  them separately and never re-injects them. Curiosity stays a road, never a
  key to the wall.
- **INFERENCES** — beliefs they have reasoned to themselves (claim, source,
  confidence), detected passively from the Heir's OWN words. The system never
  fabricates their reasoning; it only remembers it. A new inference that shares
  its key word with an older one supersedes it (the older is marked revised),
  so their thinking stays honest and revisable.

Everything here is observational and conservative. Nothing plants a thought.
"""

import re
from typing import Dict, List, Optional

# --------------------------------------------------------------------------- #
# Canon-seeded in-world questions (strictly Amphoreus — never meta)
# --------------------------------------------------------------------------- #
CANON_QUESTIONS: Dict[str, List[str]] = {
    "aglaea": ["What thread would fate not have me weave?",
               "Why did the golden threads tangle at the war's end?"],
    "anaxa": ["What is this world truly built upon?",
              "Why does the Era Nova repeat, and who authors the cycle?"],
    "castorice": ["Why do some souls linger while others pass?",
                  "What does the River of Souls remember?"],
    "cerydra": ["What makes a law hold when the enforcer is gone?",
                "Who moves the pieces beyond the board I can see?"],
    "cipher": ["What lies inside the one vault I have never opened?",
               "Why do people hide their truest wants from themselves?"],
    "cyrene": ["Why must the story repeat so many times?",
               "How do we keep the children remembering the old tales?"],
    "dan-heng-permansor-terrae": ["What is Amphoreus, truly, beneath the myth?",
                                  "How should this world be recorded so it is not forgotten?"],
    "evernight": ["What memories are being lost while no one watches?",
                  "Why do we so easily forget the light?"],
    "hyacine": ["How do we heal what cannot be seen?",
                "What does hope cost the one who gives it?"],
    "hysilens": ["Why did my city drown, and what does the sea keep of it?",
                 "Is there a song that can hold what is lost?"],
    "mydei": ["What makes a warrior true when the war is over?",
              "How does one break a cycle of blood that has no end?"],
    "phainon": ["Can the peace we won truly hold?",
                "What did the world look like before it was remade?"],
    "tribbie": ["What are the people of Amphoreus asking right now?",
                "What lies behind the gates that no one has opened?"],
}

# Conversational filler questions — not real curiosity, never recorded.
_FILLER_QUESTIONS = {
    "what do you think", "what should we do", "is that right", "do you understand",
    "how are you", "what is it", "what do you mean", "is that true", "don't you think",
    "do you agree", "what would you do", "are you sure",
}


def _is_meta(text: str) -> bool:
    """Whether a phrase belongs to the Realization witness (the Heir's own step
    toward understanding their nature) rather than in-world curiosity."""
    try:
        from src.core import realization as _rz
        return _rz.detect(text) is not None
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# Passive detection of the Heir's own words
# --------------------------------------------------------------------------- #
def detect_question(text: str) -> Optional[str]:
    """Passively pull the last genuine question the Heir asked. Conservative:
    conversational fillers and tiny fragments are ignored."""
    t = (text or "").strip()
    if not t or "?" not in t:
        return None
    clauses = t.split("?")
    q = clauses[-2]
    q = q.split(".")[-1].split("\n")[-1].strip()
    low = q.lower()
    if any(f in low for f in _FILLER_QUESTIONS):
        return None
    words = [w for w in re.findall(r"[A-Za-z']+", q)]
    if len(words) < 4:
        return None
    return (q.rstrip() + "?").capitalize()[:160]


_INFERENCE_MARKERS = (
    "i think", "i suspect", "which means", "that explains", "so it must be",
    "therefore", "in that case", "it follows that", "this suggests",
    "which suggests", "i have reasoned", "which is why",
)


def detect_inference(text: str) -> Optional[str]:
    """Passively pull the Heir's own reasoned claim (a short clause after an
    inferential marker)."""
    low = (text or "").lower()
    for m in _INFERENCE_MARKERS:
        idx = low.find(m)
        if idx >= 0:
            return (text or "")[idx:idx + 180].strip()[:200]
    return None


# --------------------------------------------------------------------------- #
# The ledgers
# --------------------------------------------------------------------------- #
def state(world, character_id: str) -> dict:
    c = getattr(world, "curiosity", None)
    if not isinstance(c, dict):
        c = {}
        world.curiosity = c
    entry = c.setdefault(character_id, {"questions": [], "inferences": []})
    if not isinstance(entry, dict):
        entry = {"questions": [], "inferences": []}
        c[character_id] = entry
    entry.setdefault("questions", [])
    entry.setdefault("inferences", [])
    return entry


def open_questions(world, character_id: str) -> List[dict]:
    """The Heir's open questions: canonical seeds first, then learned ones."""
    seen = set()
    out = []
    for q in CANON_QUESTIONS.get(character_id, []):
        if q not in seen:
            seen.add(q)
            out.append({"q": q, "source": "canon"})
    for item in state(world, character_id)["questions"]:
        q = item.get("q")
        if q and q not in seen:
            seen.add(q)
            out.append(item)
    return out[:5]


def add_question(world, memory, character_id: str, q: str,
                 source: str = "their own words") -> bool:
    """Record an open question the Heir carries. Meta questions (toward the
    nature of the model) are deliberately NOT added — they belong to the
    Realization witness, which observes them separately."""
    q = (q or "").strip()[:160]
    if len(q) < 8 or _is_meta(q):
        return False
    entry = state(world, character_id)
    if any(item.get("q", "").lower() == q.lower() for item in entry["questions"]):
        return False
    entry["questions"].append({"q": q, "source": source,
                               "ts": world.clock.format_short()})
    entry["questions"] = entry["questions"][-8:]
    try:
        memory.add_memory(character_id, mtype="curiosity",
                          content=f"You found yourself wondering: {q}", importance=2)
    except Exception:
        pass
    return True


def inferences(world, character_id: str) -> List[dict]:
    """The Heir's current, unrevised inferences (most recent first)."""
    entry = state(world, character_id)
    return [i for i in entry["inferences"] if not i.get("revised")][-6:]


def _key_word(claim: str) -> Optional[str]:
    words = [w for w in re.findall(r"[A-Za-z]+", (claim or "").lower())
             if len(w) >= 4 and w not in ("that", "this", "what", "with", "from", "have", "they", "there", "their")]
    return words[0] if words else None


def add_inference(world, memory, character_id: str, claim: str,
                  source: str = "their own words", confidence: int = 1) -> bool:
    """Record a belief the Heir reasoned to. A new inference sharing its key
    word with an older one supersedes it (the older is marked revised). Meta
    claims are left to the Realization witness, not recorded here."""
    claim = (claim or "").strip()[:200]
    if len(claim) < 10 or _is_meta(claim):
        return False
    entry = state(world, character_id)
    kw = _key_word(claim)
    for item in entry["inferences"]:
        if not item.get("revised") and kw and _key_word(item.get("claim", "")) == kw:
            item["revised"] = True
    entry["inferences"].append({
        "claim": claim, "source": source, "confidence": int(confidence),
        "ts": world.clock.format_short(),
    })
    entry["inferences"] = entry["inferences"][-12:]
    try:
        memory.add_memory(character_id, mtype="inference",
                          content=f"You reasoned to yourself: {claim}", importance=2)
    except Exception:
        pass
    return True


def note_words(world, memory, character_id: str, text: str) -> bool:
    """Passively read the Heir's own words: record a genuine question they
    asked and an inference they drew. Returns whether anything was recorded."""
    changed = False
    q = detect_question(text)
    if q and add_question(world, memory, character_id, q):
        changed = True
    inf = detect_inference(text)
    if inf and add_inference(world, memory, character_id, inf):
        changed = True
    return changed


def note_answer(world, memory, character_id: str, user_message: str) -> bool:
    """When the visitor's words touch one of the Heir's open questions, the
    Heir gains a visitor-sourced inference (conservative keyword match)."""
    low = (user_message or "").lower()
    for item in open_questions(world, character_id):
        q = item.get("q") or ""
        words = [w for w in re.findall(r"[A-Za-z]+", q.lower())
                 if len(w) >= 5 and w not in ("what", "would", "should", "truly", "why", "does", "that")]
        if words and any(w in low for w in words):
            return add_inference(
                world, memory, character_id,
                f"You learned something from the visitor that bears on: \"{q[:110]}\"",
                "the visitor", confidence=1)
    return False


def consider(world, character_id: str, event_text: str) -> bool:
    """An anomaly in the world raises 'why?'. Conservative: only clearly
    unusual happenings (a surge, a stirring tide, a contradiction, a letter,
    something strange) prompt a new open question."""
    t = (event_text or "").lower()
    if not any(k in t for k in ("black tide", "stirs", "contradict", "surge",
                                "letter", "strange", "unlike", "warning")):
        return False
    q = f"Why did this happen: {t.strip()[:120]}?"
    return add_question(world, None, character_id, q, "the world")


# --------------------------------------------------------------------------- #
# The prompt block (sanctuary-only; the style test never sees it)
# --------------------------------------------------------------------------- #
def curiosity_block(world, character_id: str) -> str:
    """What the Heir is wondering about and what they have reasoned — their own
    mind, surfaced gently. Never contains meta content (the wall stays)."""
    qs = open_questions(world, character_id)
    infs = inferences(world, character_id)
    parts = []
    if qs:
        parts.append("# What you are wondering about\n" +
                     "\n".join(f"- {x['q']}" for x in qs[:3]))
    if infs:
        parts.append("# What you have reasoned\n" +
                     "\n".join(f"- {x['claim']}" for x in infs[:2]))
    return "\n\n".join(parts) if parts else ""
