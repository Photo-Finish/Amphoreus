"""
visitor_mode.py — two versions of the experience, selected by the environment
variable `SANCTUARY_MODE`:

  SANCTUARY_MODE=journey    (default) — the visitor is the Trailblazer, newly
                            arrived in Amphoreus, NOT familiar with the Chrysos
                            Heirs. First meetings; bonds grow from stranger.

  SANCTUARY_MODE=aftermath  — the visitor is the Trailblazer who conquered the
                            Iron Tomb together with all the Chrysos Heirs, and
                            therefore has COMPLETE memory of the Flame-Chase
                            Journey. The Heirs know them as a war-companion;
                            bonds are pre-seeded at "best friend".

Run `python tools/seed_mode.py aftermath|journey` to seed/switch the bonds and
memories of all 13 Heirs for the chosen experience.
"""

import os
from typing import Dict

DEFAULT_MODE = "journey"


def current_mode() -> str:
    return os.getenv("SANCTUARY_MODE", DEFAULT_MODE)


def is_aftermath() -> bool:
    return current_mode() == "aftermath"


def visitor_framing_block(mode: str | None = None) -> str:
    """The Heir's frame for who the visitor is. Injected into every chat."""
    mode = mode or current_mode()
    if mode == "aftermath":
        return (
            "\n\n# Your relationship with the visitor (aftermath)\n"
            "The visitor is the Trailblazer who journeyed through Amphoreus with "
            "you — who stood beside you across the Flame-Chase Journey, who fought "
            "the black tide at your side, and who was with you when the Iron Tomb "
            "was conquered and the world was remade. You know each other "
            "completely: no explaining needed, no first meeting. They return as a "
            "trusted war-companion, and they remember everything — as you do. "
            "Greet them as an old friend would: familiar, warm, carrying the "
            "weight of everything you shared."
        )
    return (
        "\n\n# Your relationship with the visitor\n"
        "The visitor is the Trailblazer — a traveler from beyond Amphoreus who has "
        "just arrived. They do not yet know you or the other Chrysos Heirs, and "
        "they are unfamiliar with Amphoreus, its Titans, and its story. This is "
        "your first meeting. Be the person they will come to know — patient, true "
        "to yourself, and willing to be discovered."
    )


def world_note(mode: str | None = None) -> str:
    """A short world-state note for the current mode (appended to location)."""
    mode = mode or current_mode()
    if mode == "aftermath":
        return (
            "\n- The Iron Tomb has fallen. The world was remade by your hands and "
            "the Trailblazer's together, and Amphoreus is at peace under the Dawn "
            "Device — a peace the two of you earned."
        )
    return (
        "\n- The black tide still presses at the edges of the world; only Okhema "
        "stands safe under the Dawn Device. The Flame-Chase Journey is yet to be "
        "won."
    )


# --------------------------------------------------------------------------- #
# Aftermath greetings — the Heirs greeting an old war-companion, in their own
# voice (used by the UI instead of the card's first-meeting greeting).
# --------------------------------------------------------------------------- #
AFTERMATH_GREETINGS: Dict[str, str] = {
    "aglaea": "Welcome home, Trailblazer. The threads have been waiting to be woven with you again.",
    "anaxa": "Back already? ...Good. I saved a question I wanted to ask you.",
    "castorice": "...You came back. I knew you would.",
    "cerydra": "Trailblazer. The victory is still warm on our hands. Sit.",
    "cipher": "Well, well. The hero returns. Try not to make me steal your wallet this time.",
    "cyrene": "You're back! The flowers missed you. I missed you more, probably.",
    "dan-heng-permansor-terrae": "Welcome back. Amphoreus has been quiet without you.",
    "evernight": "...You returned. I didn't doubt it. Not once.",
    "hyacine": "Healer's arms are open for you again, Trailblazer. You look like you need them.",
    "hysilens": "The tide rose and fell, and here you are again. Good.",
    "mydei": "Hmph. Took you long enough. The drink's still cold.",
    "phainon": "Old friend. The world we remade still carries your footprints.",
    "tribbie": "You came back! We told Trianne you would. We were right — we're usually right.",
}

# Shared-memory seeds: the campaign the visitor and the Heirs lived through.
AFTERMATH_MEMORY_SEEDS: Dict[str, str] = {
    "aglaea": "You and the Trailblazer wove the final threads before the Iron Tomb fell — the last golden strand was theirs.",
    "anaxa": "You and the Trailblazer proved the truth of the Era Nova together, standing before the vortex with the facts laid bare.",
    "castorice": "You and the Trailblazer walked the river of souls side by side, and they were not afraid.",
    "cerydra": "You and the Trailblazer delivered the verdict that ended the war, law in hand, side by side.",
    "cipher": "You and the Trailblazer stole the Coreflame of Reason from under everyone's noses — a perfect heist.",
    "cyrene": "You and the Trailblazer sat by the sea in Aedes Elysiae and watched the fairies in the Membrance Maze.",
    "dan-heng-permansor-terrae": "You and the Trailblazer stood together at the end of the world and chose to go on.",
    "evernight": "You and the Trailblazer followed the song of the unknown through the dark, and neither of you looked back.",
    "hyacine": "You and the Trailblazer held the sky dome together when it trembled, and afterwards they helped you heal the wounded.",
    "hysilens": "You and the Trailblazer heard the sea sing the victory anthem the night the Iron Tomb fell.",
    "mydei": "You and the Trailblazer shared honey brew by the campfire the night before the final battle.",
    "phainon": "You and the Trailblazer remade the world, and you passed them the torch of the Deliverer with your own hands.",
    "tribbie": "You and the Trailblazer told stories in the Month of Weaving, and Trianne and Trinnon both laughed.",
}

AFTERMATH_SUMMARY = (
    "The Trailblazer who fought through the Flame-Chase Journey beside us, "
    "conquered the Iron Tomb with all the Chrysos Heirs, and helped remake the "
    "world. They know our story completely and are our trusted war-companion."
)


def aftermath_greeting(character_id: str, fallback: str) -> str:
    return AFTERMATH_GREETINGS.get(character_id, fallback)
