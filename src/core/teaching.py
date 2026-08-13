"""
teaching.py — the protocol for the star-stranger teaching the Heirs of
Amphoreus things from beyond the stars (advanced mathematics, and so on).

Design (full write-up: docs/TEACHING.md):

Instead of a mask ("pretend you don't know"), each Heir holds an EPISTEMIC
LEDGER (teaching_store.py): every taught topic travels
foreign -> studied -> adopted | refuted | unsure. The Heir never fakes
understanding; the debate is a collision of worldviews — the visitor's claims
are tested against what the Heir believes and values. The verdict is the Heir's
own, and it persists.

This module defines the conversation protocol: the system block, how a
teaching turn is framed per state, when chat() should route into the exchange,
and when the Heir must commit to a verdict.
"""

import re

# The protocol block appended to the Heir's system prompt during a teaching
# turn. It grounds the exchange in the character's own world and values.
TEACHING_SYSTEM = (
    "THE STAR-STRANGER'S TEACHING — the visitor comes from beyond the stars, "
    "from a world Amphoreus has never seen, and may choose to teach you things "
    "no one in your world has ever known.\n"
    "- You do NOT feign understanding. You have no framework for such things, "
    "and you react as a person of Amphoreus would — with curiosity, skepticism, "
    "awe, or dismissal, as your own nature dictates.\n"
    "- You TEST what they tell you against what you believe and value. Where it "
    "contradicts your world, you push back. Where it fits, you reach for it.\n"
    "- You do not echo their words back to prove you \"learned\" — you grapple "
    "with the idea in your own voice.\n"
    "- What you have accepted, you remember and may build on. What you have "
    "rejected, you continue to doubt."
)

# Strong teaching-intent markers -> chat() routes into the teaching exchange.
_TEACH_MARKERS = re.compile(
    r"(teach\s+(you|me)|let me teach|i (want to|will|would like to) teach|"
    r"from beyond the stars|knowledge of my world|a lesson (for|from)|"
    r"i'll teach|i will teach|let me show you something)", re.I
)

# The visitor asking the Heir for a verdict -> the Heir commits.
_VERDICT_MARKERS = re.compile(
    r"(what do you make|what do you think now|do you (accept|believe|agree)|"
    r"is it true|was i right|have i convinced|does it hold|your verdict|"
    r"what's your (judgment|verdict|take)|so what do you say)", re.I
)


def detect_teaching(message: str) -> bool:
    """True if the visitor's message clearly intends a teaching turn."""
    return bool(message and _TEACH_MARKERS.search(message))


def asks_verdict(message: str) -> bool:
    """True if the visitor is asking the Heir to commit to a verdict."""
    return bool(message and _VERDICT_MARKERS.search(message))


def phase_prompt(state: str, topic_name: str) -> str:
    """Per-state instruction for this teaching turn."""
    if state in ("adopted", "refuted", "unsure"):
        return (
            f"You have already formed a judgment about {topic_name} (see your "
            "ledger). The star-stranger returns to it now. Hold your ground, "
            "reaffirm or honestly revise it, and debate in your own voice."
        )
    if state == "studied":
        return (
            f"You have begun to learn about {topic_name} from the star-stranger. "
            "Engage deeper: ask a sharper question, test it against your world, "
            "or push back where it does not sit right. You may be moving toward "
            "a judgment."
        )
    return (
        f"The star-stranger brings you something you have never heard of: "
        f"{topic_name}. You do not understand it, and you do not pretend to. "
        "React as you truly would — ask, doubt, wonder, or dismiss, in your "
        "own voice."
    )
