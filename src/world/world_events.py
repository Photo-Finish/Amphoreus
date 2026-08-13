"""world_events.py — the living texture of the little Amphoreus.

Everything that makes the world feel *vivid* without scripting the Heirs:

- **Rumors & the visitor's echo** — the world notices you. When the star-stranger
  talks with a Heir, a rumor forms and spreads to adjacent Heirs (co-located),
  degrading as it travels ("Phainon told me the stranger spoke of strange
  knowledge…").
- **Teaching that spreads** — when one Heir is taught something from beyond the
  stars and accepts it, adjacent Heirs hear a *degraded* version secondhand, and
  may raise it in their next meeting with the visitor.
- **Dynamic relationships** — Heir↔Heir bonds drift with time, encounters and
  letters (a small per-pair delta overlay on the static canon registry).
- **Letters** — Heirs who are far apart may write to each other.
- **Life projects** — each Heir pursues a long-term, canon-grounded project that
  advances day by day and is logged at milestones.
- **Canon-checked NPCs** — named, *alive* figures (dead characters are never
  added) who colour each city's daily flavour and the Keeper's errands.
- **Black-tide surges** — a journey-mode-only world event: for a few days the
  tide stirs near the edge cities, darkening weather and the news.

All of this is pure data + logic. Nothing here authors an Heir's action.
"""

import random
from typing import Dict, List, Optional

# --------------------------------------------------------------------- #
# Life projects — canon-grounded, long-term, per Heir.
# --------------------------------------------------------------------- #
PROJECTS: Dict[str, Dict] = {
    "aglaea": {"title": "The unbroken loom", "goal": "weave the city's threads back into a single pattern", "steps": 5},
    "anaxa": {"title": "A treatise on what is", "goal": "set down the Grove's truths before they are forgotten", "steps": 6},
    "castorice": {"title": "The garden of the still", "goal": "tend the graves and the mourning places of Aidonia", "steps": 5},
    "cerydra": {"title": "The scale rebalanced", "goal": "reaffirm the law of Okhema after the war", "steps": 5},
    "cipher": {"title": "One last locked door", "goal": "find the one vault even she has never opened", "steps": 4},
    "cyrene": {"title": "A story kept alive", "goal": "tell the old tales so the children remember", "steps": 4},
    "dan-heng-permansor-terrae": {"title": "The Archiver's record", "goal": "record Amphoreus as it truly was, and as it is now", "steps": 6},
    "evernight": {"title": "The garden of recollection", "goal": "gather the memories the world almost forgot", "steps": 5},
    "hyacine": {"title": "The healer's path", "goal": "teach the Twilight Courtyard's healing to a new generation", "steps": 5},
    "hysilens": {"title": "A song for the sea", "goal": "compose the requiem of the drowned city", "steps": 4},
    "mydei": {"title": "The spear that guards", "goal": "forge a new order of guardians for Kremnos", "steps": 5},
    "phainon": {"title": "A world at peace", "goal": "make sure the peace he fought for truly holds", "steps": 6},
    "tribbie": {"title": "A thousand questions", "goal": "collect the people's questions and carry them to the gates", "steps": 5},
}

# --------------------------------------------------------------------- #
# Canon-checked NPCs — ONLY characters who are alive and present in the
# sanctuary's era. (e.g. Gorgo and Krateros are NOT here: Mydei slew his
# father, and his mother died challenging Eurypon — dead characters never
# appear. Trianne is likewise absent.) Each has a home city and a flavour.
# --------------------------------------------------------------------- #
NPCS = [
    {"name": "Bartholos", "city": "Okhema", "role": "a merchant of odd goods and secrets",
     "flavor": "Bartholos trades in what others overlook, and pays his debts in information."},
    {"name": "Seliose", "city": "Grove of Epiphany", "role": "a gentle scholar of the Grove",
     "flavor": "Seliose keeps Hyacine's old notes and tends the Grove's quiet corners."},
    {"name": "Noldus", "city": "Janusopolis", "role": "a keeper of the gates",
     "flavor": "Noldus knows every threshold in Janusopolis and greets every traveler by name."},
    {"name": "Researcher Eikura Shuu", "city": "Okhema", "role": "a visiting researcher",
     "flavor": "Eikura Shuu studies Amphoreus' ruins and fills notebooks with tireless questions."},
    {"name": "Mem", "city": "Aedes Elysiae", "role": "a small companion who remembers for others",
     "flavor": "Mem drifts at the village's edge, holding memories the world has dropped."},
    {"name": "Theodosia", "city": "Styxia", "role": "a quiet undertaker's apprentice",
     "flavor": "Theodosia lays the departed to rest and speaks to them as she works."},
]

# --------------------------------------------------------------------- #
# Rumors & the visitor's echo
# --------------------------------------------------------------------- #
def add_rumor(world, character_id: str, text: str, source: str = ""):
    """Record a rumor in a Heir's ledger (freshest first, capped)."""
    ledger = world.rumors.setdefault(character_id, [])
    ledger.insert(0, {"text": text, "source": source, "fidelity": 1.0,
                      "ts": world.clock.format_short()})
    del ledger[6:]  # keep the six most recent


def rumors_for(world, character_id: str, limit: int = 3) -> List[str]:
    """The freshest rumors this Heir currently believes (fidelity >= 0.35)."""
    out = []
    for r in world.rumors.get(character_id, []):
        if r.get("fidelity", 1.0) >= 0.35 and len(out) < limit:
            out.append(r["text"])
    return out


def spread_rumors(world, from_cid: str, to_cid: str):
    """One Heir tells another what they've heard; the telling degrades it."""
    if from_cid == to_cid:
        return
    for r in world.rumors.get(from_cid, [])[:3]:
        fidelity = r.get("fidelity", 1.0) * 0.7
        if fidelity < 0.35:
            continue
        text = r["text"]
        # secondhand — the source is now the teller
        new_text = f"{world.name_of(from_cid)} told me: {text}"
        add_rumor(world, to_cid, new_text, source=from_cid)
        # keep fidelity from the original rumor, not reset
        for rr in world.rumors.get(to_cid, []):
            if rr["text"] == new_text:
                rr["fidelity"] = fidelity
                break


def visitor_echo(world, character_id: str, note: str) -> str:
    """After the star-stranger talks with a Heir, the world notices."""
    rumor = (f"The star-stranger met with {world.name_of(character_id)} — {note}")
    add_rumor(world, character_id, rumor, source="the star-stranger")
    # the Keeper's news catches it
    flash = world.ambient.setdefault("news_flash", [])
    if len(flash) < 5:
        flash.append({"text": rumor, "ts": world.clock.format_short()})
    return rumor


def teaching_rumor(world, character_id: str, topic: str):
    """A taught-and-accepted thing spreads (degraded) to adjacent Heirs."""
    rumor = (f"the star-stranger taught {world.name_of(character_id)} something "
             f"of the world beyond the stars — {topic}")
    add_rumor(world, character_id, rumor, source="the star-stranger")
    for other in adjacent(world, character_id):
        spread_rumors(world, character_id, other)


def adjacent(world, character_id: str) -> List[str]:
    """Heirs physically in the same city as `character_id` (not travelling)."""
    loc = world.location_name(character_id)
    return [c for c in world.agents_at(loc) if c != character_id
            and not world.is_traveling(c)]


# --------------------------------------------------------------------- #
# Dynamic relationships (a small drift overlay on the canon registry)
# --------------------------------------------------------------------- #
def adjust_relationship(world, a: str, b: str, delta: int):
    key = "|".join(sorted([a, b]))
    cur = world.relationship_delta.get(key, 0)
    world.relationship_delta[key] = max(-3, min(3, cur + delta))


def relationship_delta_of(world, a: str, b: str) -> int:
    return world.relationship_delta.get("|".join(sorted([a, b])), 0)


def relationships_block(world) -> str:
    """A compact 'how your bonds stand' block for the chat (drift overlay)."""
    lines = []
    for key, delta in world.relationship_delta.items():
        if delta == 0:
            continue
        a, b = key.split("|")
        na, nb = world.name_of(a), world.name_of(b)
        if delta > 0:
            lines.append(f"- You and {nb} have grown closer of late (bond +{delta}).")
        else:
            lines.append(f"- You and {nb} have drifted apart of late (bond {delta}).")
    if lines:
        return "# How your bonds stand\n" + "\n".join(lines)
    return ""


# --------------------------------------------------------------------- #
# Letters
# --------------------------------------------------------------------- #
def compose_letter(world, from_cid: str, to_cid: str, text: str):
    """A letter between Heirs — logged, kept, remembered by both."""
    entry = {
        "from": from_cid, "to": to_cid,
        "from_name": world.name_of(from_cid), "to_name": world.name_of(to_cid),
        "text": text, "ts": world.clock.format_short(),
    }
    world.letters.append(entry)
    del world.letters[:-30]
    return entry


# --------------------------------------------------------------------- #
# Life projects
# --------------------------------------------------------------------- #
def project_progress(world, character_id: str) -> int:
    return world.project_progress.get(character_id, 0)


def project_info(world, character_id: str) -> Optional[Dict]:
    p = PROJECTS.get(character_id)
    if not p:
        return None
    return {
        "title": p["title"], "goal": p["goal"],
        "steps": p["steps"],
        "progress": project_progress(world, character_id),
    }


def advance_projects(world) -> List[str]:
    """Advance each Heir's project by one step now and then. Returns milestone
    lines for the Chronicle (a completed project restarts at a new stage)."""
    milestones: List[str] = []
    for cid, p in PROJECTS.items():
        if random.random() < 0.6:  # not every day — life is uneven
            continue
        cur = world.project_progress.get(cid, 0)
        cur += 1
        world.project_progress[cid] = cur
        if cur >= p["steps"]:
            milestones.append(
                f"{world.name_of(cid)} reaches a milestone in \"{p['title']}\" — "
                f"{p['goal']}."
            )
            world.project_progress[cid] = 0  # the work continues, renewed
    return milestones


# --------------------------------------------------------------------- #
# Black-tide surges — journey mode only (the aftermath is at peace)
# --------------------------------------------------------------------- #
SURGE_DAYS = 3
EDGE_CITIES = ["Castrum Kremnos", "Styxia", "Aidonia", "Vortex of Genesis"]


def surges_enabled() -> bool:
    """Surges are a journey-mode option: in the aftermath the world is at peace."""
    import os
    return os.environ.get("SANCTUARY_MODE", "journey") != "aftermath"


def maybe_surge(world, chance: float = 0.12) -> Optional[Dict]:
    """Roll whether the black tide stirs today (journey mode only)."""
    if not surges_enabled():
        return None
    if surge_active(world):
        return world.surge
    if random.random() >= chance:
        return None
    cities = random.sample(EDGE_CITIES, k=random.randint(1, 2))
    world.surge = {"active": True, "remaining": SURGE_DAYS, "cities": cities}
    return world.surge


def surge_active(world) -> bool:
    return bool(world.surge and world.surge.get("active"))


def surge_text(world) -> str:
    if not surge_active(world):
        return ""
    cities = ", ".join(world.surge["cities"])
    return (f"The black tide stirs along {cities}. The sky darkens; the Keeper "
            f"calls the Heirs to be wary. {world.surge['remaining']} day(s) remain.")


def advance_surge(world):
    if not surge_active(world):
        return
    world.surge["remaining"] -= 1
    if world.surge["remaining"] <= 0:
        world.surge = {"active": False, "remaining": 0, "cities": []}
