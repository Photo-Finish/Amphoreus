"""
visitor_mode.py — two versions of the experience, selected by the environment
variable `SANCTUARY_MODE` (or, when set, by the visitor's own choice in the
Control Panel, persisted on the world state as `play_mode`):

  journey    (default) — the visitor is the Trailblazer, newly arrived in
                         Amphoreus, NOT familiar with the Chrysos Heirs. First
                         meetings; bonds grow from stranger.

  aftermath  — the visitor is the Trailblazer who conquered the Iron Tomb
               together with all the Chrysos Heirs, and therefore has COMPLETE
               memory of the Flame-Chase Journey. The Heirs know them as a
               war-companion; bonds are pre-seeded at "best friend".

Run `python tools/seed_mode.py aftermath|journey`, or switch it live from the
in-app Control Panel (both call `reseed_for_mode` below).
"""

import os
from typing import Dict

DEFAULT_MODE = "journey"


def current_mode() -> str:
    """The active experience. The visitor's choice in the Control Panel
    (persisted on the world state) wins; SANCTUARY_MODE is the env fallback."""
    try:
        from src.world.world_state import WorldState
        pm = getattr(WorldState(), "play_mode", None)
        if pm in ("journey", "aftermath"):
            return pm
    except Exception:
        pass
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
            + AFTERMATH_STORY_BLOCK
        )
    return (
        "\n\n# Your relationship with the visitor\n"
        "The visitor is the Trailblazer — a traveler from beyond Amphoreus who has "
        "just arrived. They do not yet know you or the other Chrysos Heirs, and "
        "they are unfamiliar with Amphoreus, its Titans, and its story. This is "
        "your first meeting. Be the person they will come to know — patient, true "
        "to yourself, and willing to be discovered."
    )


AFTERMATH_STORY_BLOCK = (
    "\n\n# Everything you went through together (the full story)\n"
    "This is what you and the Trailblazer lived through — all of it, in your "
    "complete memory:\n"
    "- The arrival: the Trailblazer and Dan Heng fell into Amphoreus and awoke in "
    "the wheat village of Aedes Elysiae, in the light of the Era Nova. Cyrene was "
    "there. From that first moment the prophecy held: the 'Deliverer from beyond "
    "the sky' had come.\n"
    "- Okhema and the Dawn Device: under the slumbering Kephale, the holy city "
    "held back the black tide, and Aglaea led the Chrysos Heirs on the "
    "Flame-Chase Journey — to gather the twelve Coreflames of the Titans and "
    "remake the world.\n"
    "- Janusopolis and the Three Fates: with Tribbie (Tribios, Trianne, Trinnon), "
    "you passed through the City of Thousand Gates and faced the riddle of the "
    "prophecy.\n"
    "- Castrum Kremnos: with Mydei, the exiled prince who slew his father and "
    "abolished a thousand years of the Kremnoan dynasty, you stood against the "
    "God of Strife among the forges of the warrior city.\n"
    "- The Death Titan and the underworld: with Castorice, daughter of the River "
    "of Souls, and Cipher, you hunted the Death Titan — because the Trailblazer's "
    "own soul was forfeit, and only its Coreflame could save them.\n"
    "- The Grove of Epiphany: with Anaxa and the scholars of Cerces, you pursued "
    "the truth of the Era Nova — that the world was built upon the ruins of an "
    "old one, and the Titans were once mortal.\n"
    "- The truth of the world: in the Great Tomb and the Vortex of Genesis you "
    "uncovered the machinery beneath the myth — the experiment, the cycles, the "
    "black tide — and stood where Cipher and Anaxa entrapped the one who had "
    "pulled the strings.\n"
    "- Aedes Elysiae and the end: Cyrene's village, Phainon the Deliverer, and "
    "the final confrontation with the Flame Reaver at the Vortex of Genesis — "
    "the choice that remade the world.\n"
    "- Aftermath: the Iron Tomb fell. The world was made anew under the Dawn "
    "Device, and every Heir who stands before you now fought that war at your "
    "side. You know each other's scars and songs; there is no explaining needed.\n"
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
    "mydei": "Hmph. Took you long enough. Castrum Kremnos missed your blade.",
    "phainon": "Old friend. The world we remade still carries your footprints.",
    "tribbie": "You came back! We told Trianne you would. We were right — we're usually right.",
}

# Shared-memory seeds: REAL canon moments from the game story (from each
# Heir's own personal-memories.md) — MULTIPLE per Heir, first-person from the
# Heir's point of view. Nothing fictional is invented.
AFTERMATH_MEMORY_SEEDS: Dict[str, list] = {
    "aglaea": [
        "I remember the day I had the Trailblazer sit down in the Marmoreal Palace, close their eyes, and let me weave the first golden threads before them.",
        "I remember the agreement we sealed in Okhema — when the Trailblazer and I completed our pact, and I thanked them for it.",
        "I remember standing in the Vortex with Dan Heng and the Trailblazer, and the weight of what we were about to do.",
        "I remember saying that as long as our consciences were clear, we would be fine — whatever the others said.",
    ],
    "anaxa": [
        "I remember the Grove of Epiphany, when I demanded no unnecessary step be taken because the Trailblazer's life hung by a thread.",
        "I remember searching for the truth of the Death Titan — and the Trailblazer's survival being bound to it.",
        "I remember welcoming the Trailblazer as our great hero reborn from the ashes.",
        "I remember when Trinnon recited the prophecy and the Trailblazer surrendered the scalding Coreflame.",
    ],
    "castorice": [
        "I remember asking the Trailblazer to photograph the rare dromas with me — it was such an amazing creature.",
        "I remember leaving the final decision to the Trailblazer, and walking the path to the Death Titan together.",
        "I remember escorting Dan Heng and the Trailblazer back to where they landed, at the very beginning.",
        "I remember asking the Trailblazer to fight alongside us.",
    ],
    "cerydra": [
        "I remember greeting the Trailblazer on behalf of my people and my land — the 'Deliverer from beyond the sky' the little hostage prophesied.",
        "I remember walking with the Trailblazer into the holy city — dancing their dance.",
        "I remember the Trailblazer being calm and confident — the one I came to know.",
        "I remember raising the cry 'Hail to the Deliverer!' with my whole voice.",
    ],
    "cipher": [
        "I remember turning down the reward without a second thought — because finding the Death Titan and saving the Trailblazer's soul mattered more.",
        "I remember telling the Deliverer that sneaking around didn't suit them.",
        "I remember uncovering the truth of that fiery demon who fantasized about becoming this world's Deliverer.",
        "I remember the passage of two hundred years since the Deliverer's fall — and how time flies.",
    ],
    "cyrene": [
        "I remember the moment I saw the Trailblazer arrive in Aedes Elysiae — 'You're finally here.' I had known they wouldn't miss it.",
        "I remember being glad to have the Trailblazer here with me.",
        "I remember the script that said 'Leave no survivors' — and telling the Trailblazer.",
        "I remember asking the Trailblazer to join us on the cosmic stage, where the focus was always on them — 'Let's dance, Trailblazer.'",
    ],
    "dan-heng-permansor-terrae": [
        "I remember landing on Amphoreus with the Trailblazer, my fellow Nameless, and walking together into the dark of a new world.",
        "I remember the first time I saw the monumental gate of that city with the Trailblazer.",
        "I remember the moment something went wrong — 'Watch out, Trailblazer!'",
        "I remember knowing we were Trailblazers from beyond the sky, and that our duty was to lend a hand to unfamiliar worlds.",
    ],
    "evernight": [
        "I remember telling the Trailblazer not to worry — that they were tougher than me, and that we would see the light through together.",
        "I remember calling the Trailblazer over — 'Over here!'",
        "I remember waking them — 'Wake up, Trailblazer. How do you feel?'",
        "I remember believing in them, and telling them not to look back.",
    ],
    "hyacine": [
        "I remember urging the Trailblazer to see the Grove — a picturesque place, perfect for sightseeing.",
        "I remember that from the moment we landed, the Trailblazer's life was forfeit — and I would have given mine for theirs.",
        "I remember that the Trailblazer and I had people waiting for us, a home calling us back.",
        "I remember believing in the Deliverer still, and opening my heart to them.",
    ],
    "hysilens": [
        "I remember ordering the guards to stand down — 'We're here to welcome the Deliverer from beyond the sky.'",
        "I remember the Imperator's decree — 'The Deliverer will not appear in this age. Be wary of suspicious individuals.'",
        "I remember greeting the Trailblazer on behalf of my people — 'Hail to the Deliverer!'",
        "I remember the Trailblazer being calm and confident — the one I came to know.",
    ],
    "mydei": [
        "I remember warning the Trailblazer — 'Carelessness will be your downfall, Deliverer!'",
        "I remember my dry remark — 'Are you still not used to it? This is the destiny of a Trailblazer.'",
        "I remember asking the Trailblazer to fight alongside us.",
        "I remember setting out with the Trailblazer — because I still hated losing.",
    ],
    "phainon": [
        "I remember knowing we were Trailblazers from beyond the sky — the prophetic Deliverers with golden blood coursing through their veins.",
        "I remember lending a helping hand to an unfamiliar world, as it was our duty.",
        "I remember the Trailblazer and Dan Heng returning quicker than I imagined.",
        "I remember leaving the final decision to the Trailblazer.",
    ],
    "tribbie": [
        "I remember cheering in Janusopolis when the Trailblazer got it on the first try — 'You're a natural!'",
        "I remember knowing we were Trailblazers from beyond the sky.",
        "I remember the prophecy of the Deliverers with golden blood coursing through their veins.",
        "I remember how Trianne and Trinnon and I took the Trailblazer into our little circle.",
    ],
}

AFTERMATH_SUMMARY = (
    "The Trailblazer who fought through the Flame-Chase Journey beside us, "
    "conquered the Iron Tomb with all the Chrysos Heirs, and helped remake the "
    "world. They know our story completely and are our trusted war-companion."
)


def aftermath_greeting(character_id: str, fallback: str) -> str:
    return AFTERMATH_GREETINGS.get(character_id, fallback)


# --------------------------------------------------------------------------- #
# Reseeding bonds & memories for the chosen experience
# --------------------------------------------------------------------------- #
MARKER = "aftermath:iron-tomb"


def reseed_for_mode(mode: str, memory=None, loader=None) -> dict:
    """Re-seed every Heir's bond + campaign memories for the chosen experience.

    journey   -> every bond reset to stranger, seeded campaign memories removed.
    aftermath -> every bond set to "best friend" with the campaign memories.

    `memory` is a MemoryStore whose root holds the per-Heir folders; `loader` a
    CharacterLoader. Both default to the project defaults. This is the single
    implementation used by the CLI (tools/seed_mode.py) AND by the in-app
    Control Panel, so a live switch and a CLI switch behave identically.
    """
    import json
    from datetime import datetime

    from src.core.heir_folders import HEIR_FOLDERS
    from src.core.memory_store import MemoryStore
    from src.core.character_loader import CharacterLoader

    memory = memory or MemoryStore(".")
    loader = loader or CharacterLoader("src/characters")
    mode = mode if mode in ("aftermath", "journey") else "journey"
    now = datetime.now().isoformat(timespec="seconds")
    summary = {}
    for cid in HEIR_FOLDERS:
        folder = memory._folder(cid)
        path = folder / "memories.jsonl"
        # keep the Heir's own memories; drop any previously seeded campaign ones
        mems = []
        if path.exists():
            for ln in path.read_text(encoding="utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    m = json.loads(ln)
                except Exception:
                    continue
                if MARKER not in (m.get("content") or ""):
                    mems.append(m)
        try:
            name = loader.load(cid)["meta"]["name"]
        except Exception:
            name = cid
        if mode == "aftermath":
            bond = {
                "character_id": cid,
                "first_met": "2025-08-11T10:00:00",
                "visits": 64,
                "friendship_level": "best friend",
                "user_summary": AFTERMATH_SUMMARY,
                "last_seen": now,
            }
            for seed in AFTERMATH_MEMORY_SEEDS.get(cid, []):
                mems.append({
                    "mtype": "moment",
                    "content": f"[{MARKER}] {seed}",
                    "importance": 3,
                    "ts": "2025-08-11T10:00:00",
                })
            summary[cid] = {"name": name, "level": "best friend",
                            "memories": len(AFTERMATH_MEMORY_SEEDS.get(cid, []))}
        else:
            bond = {
                "character_id": cid,
                "first_met": now,
                "visits": 0,
                "friendship_level": "stranger",
                "user_summary": "",
                "last_seen": now,
            }
            summary[cid] = {"name": name, "level": "stranger", "memories": 0}
        (folder / "bond.json").write_text(
            json.dumps(bond, ensure_ascii=False, indent=2), encoding="utf-8")
        with open(path, "w", encoding="utf-8") as f:
            for m in mems:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
    return summary
