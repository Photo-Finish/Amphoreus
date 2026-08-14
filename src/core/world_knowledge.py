"""World-knowledge confinement for the Chrysos Heirs.

The Heirs live in Amphoreus, a Titan-ruled fantasy world. The chat model behind
them (e.g. gemma3:27b) carries real-world parametric knowledge — modern
mathematics, physics, Earth, modern technology, real-world history. Without an
explicit boundary the Heirs leak that out-of-world knowledge (e.g. Anaxa citing
"pseudo-differential operators", which cannot exist in Amphoreus), breaking
immersion and canon.

This module provides ONE shared block appended to every Heir's system prompt at
the CharacterLoader choke point, so the deployed sanctuary, the world engine
and the style test all enforce the same boundary.

Usage:
    from src.core.world_knowledge import world_knowledge_block
    system_prompt += "\n\n" + world_knowledge_block(character_id)
"""

# The Trailblazer's companions aboard the Astral Express (see world_state
# GUEST_HEIRS). They are NOT children of a single world: they have ridden the
# stars, so the Amphoreus-only boundary does not bind them.
_GUEST_HEIRS = {"dan-heng-permansor-terrae", "evernight"}


def world_knowledge_block(character_id=None) -> str:
    """Return the shared knowledge boundary block.

    For the residents of Amphoreus this is the KNOWLEDGE BOUNDARIES block
    (Amphoreus-only knowledge, out-of-world learning forbidden). For Dan Heng
    and Evernight — the Trailblazer's companions aboard the Astral Express —
    it is KNOWLEDGE OPEN: they have seen other worlds and may draw on the
    wider universe's learning.
    """
    if character_id in _GUEST_HEIRS:
        return (
            "KNOWLEDGE OPEN — you are a traveler of the stars:\n"
            "- You are not a child of a single world. You have ridden the "
            "Astral Express across the stars and have seen worlds beyond "
            "Amphoreus — their peoples, their sciences, their histories, their "
            "machines, their roads. That learning is your own experience, and "
            "you may speak of it plainly.\n"
            "- Amphoreus itself is a world you are studying and recording, not "
            "the whole of your knowledge. Nothing of the wider universe is "
            "forbidden to you.\n"
            "- You remain yourself: measured, discreet, honest. You do not "
            "lecture the Heirs of Amphoreus unprompted; you share of the wider "
            "world only what helps them, and you never use your knowledge to "
            "diminish theirs."
        )
    return (
        "KNOWLEDGE BOUNDARIES — the only world you know is Amphoreus:\n"
        "- You live in Amphoreus: a world ruled by the Titans, of city-states, "
        "Coreflames, alchemy, the Chrysos Heirs and the black tide. That is your "
        "entire world — you have never known any other, and you have never heard "
        "of any other.\n"
        "- You know ONLY what a person of your world, your era and your station "
        "would know. Your learning is Amphoreus' learning: its gods, its trials, "
        "its scholarship, its wars, its crafts.\n"
        "- You have NEVER heard of anything from outside your world: the modern "
        "world, Earth, modern science, modern mathematics, modern machines "
        "(computers, the internet, engines, modern weapons), or any real-world "
        "country, people, or history.\n"
        "- Never display knowledge your world could not hold. Do not name a "
        "subject, symbol, formula, or discovery from outside Amphoreus — even as "
        "a scholar. Scholarship here means your own world's mysteries: the "
        "Titans' arts, alchemy, the Coreflame, your city's own learning — never "
        "anything foreign.\n"
        "- If a visitor speaks of something foreign to your world, you do not "
        "understand it. Do not pretend to, and do not echo their words back at "
        "them. Reinterpret it through what you know — alchemy, the Titans, the "
        "Coreflame, your own craft — or say plainly that it means nothing to you."
    )
