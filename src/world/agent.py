"""
Heir Agent — the autonomy loop of a single Chrysos Heir in the little Amphoreus.

Each Heir is an autonomous agent: it perceives the world, decides freely what
to do (through its own voice), acts, and remembers. Nothing is scripted — the
system only hosts time, space, and memory. The Heir's will is its own.
"""

import random
import re
from typing import Dict, List, Optional

from ..core.character_loader import CharacterLoader
from ..core.llm_client import LLMClient
from ..core.memory_store import MemoryStore
from .world_state import WorldState, LOCATIONS
from .schedules import scheduled_entry
from .map_data import travel_days, travel_description


class HeirAgent:
    """One autonomous Chrysos Heir living in the little Amphoreus."""

    def __init__(
        self,
        character_id: str,
        loader: CharacterLoader,
        llm: LLMClient,
        memory: MemoryStore,
        world: WorldState,
    ):
        self.character_id = character_id
        self.loader = loader
        self.llm = llm
        self.memory = memory
        self.world = world
        card = loader.load(character_id)
        self.name = card["meta"]["name"]
        self.base_prompt = loader.build_system_prompt(character_id)

    # ------------------------------------------------------------------ #
    # Perception (with senses — what the Heir sees and hears)
    # ------------------------------------------------------------------ #
    def _perceive(self) -> str:
        loc = self.world.location_name(self.character_id)
        here = [a for a in self.world.agents_at(loc) if a != self.character_id]
        here_names = [self._name_of(a) for a in here]
        others = (
            f"You can see {', '.join(here_names)} here." if here_names
            else "You are alone here for now."
        )

        # The Heir's weekly routine at this hour — their usual occupation.
        sched_loc, sched_act = scheduled_entry(
            self.character_id, self.world.clock.day, self.world.clock.period
        )
        routine = f"\nYour usual routine at this hour: {sched_act}, in {sched_loc}."

        # Travel status
        tinfo = self.world.travel_info(self.character_id)
        travel_note = ""
        if tinfo:
            companion = ""
            if self.world.is_accompanied(self.character_id):
                companion = " The star-stranger walks beside you, sharing the road."
            travel_note = (
                f"\nYou are on the road to {tinfo['to']} — "
                f"{tinfo['remaining_days']} day(s) of travel remain. "
                "You are not in any city right now."
                f"{companion}"
            )

        recent = self.world.recent_events_text(limit=4)
        recent_text = f"\nRecently in Amphoreus:\n{recent}" if recent else ""
        # The day's errand and news, laid by the Keeper (Ambient Director).
        errand = self.world.ambient_errand(self.character_id)
        errand_text = f"\nA request reached you today: {errand}" if errand else ""
        news = self.world.ambient_news()
        news_text = f"\nNews from the wider world: {news}" if news else ""
        memories = self.memory.get_world_memories(self.character_id, limit=3)
        mem_text = ""
        if memories:
            mem_text = "\nWhat you have lived through lately:\n" + "\n".join(
                f"- {m['content']}" for m in memories
            )

        # The living texture — what you've heard, your long work, any letters.
        from . import world_events as wev
        rumors = wev.rumors_for(self.world, self.character_id, limit=3)
        rumor_text = ""
        if rumors:
            rumor_text = "\nWhat you have heard lately:\n" + "\n".join(
                f"- {r}" for r in rumors
            )
        proj = wev.project_info(self.world, self.character_id)
        proj_text = ""
        if proj:
            proj_text = (f"\nYour long work: \"{proj['title']}\" — {proj['goal']} "
                         f"({proj['progress']}/{proj['steps']} steps).")
        letters = [l for l in self.world.letters if l.get("to") == self.character_id]
        letter_text = ""
        if letters:
            latest = letters[-1]
            letter_text = (f"\nA letter waits from {latest['from_name']}: "
                           f"\"{latest['text'][:120]}\"")

        senses = self.world.sensory_text(loc)
        return (
            f"It is {self.world.clock.format_short()}."
            f"\nYou are at {loc} — {self.world.location_desc(loc)}."
            f"{routine}"
            f"{travel_note}"
            f"\n{senses}"
            f"\n{others}"
            f"{errand_text}"
            f"{news_text}"
            f"{rumor_text}"
            f"{proj_text}"
            f"{letter_text}"
            f"{recent_text}"
            f"{mem_text}"
        )

    def _name_of(self, character_id: str) -> str:
        try:
            return self.loader.load(character_id)["meta"]["name"]
        except Exception:
            return character_id

    # ------------------------------------------------------------------ #
    # Decision — the Heir acts freely, within the honest geography of the world
    # ------------------------------------------------------------------ #
    def decide(self) -> Dict:
        """Ask the Heir what they do now, spontaneously. Returns {action, location?, person?}."""
        perceive = self._perceive()
        system = (
            self.base_prompt
            + "\n\nYou live in Amphoreus now, at rest after the long war. "
            "This is your life. You act of your own free will — no one scripts your days. "
            "Speak in your own voice."
        )
        user = (
            f"{perceive}\n\n"
            "What do you do now? Decide freely and spontaneously. "
            "Reply with 1–2 short sentences describing your action — what you do, "
            "and (only if you choose to go somewhere or seek someone) where you go "
            "or whom you seek. You may also choose to rest or stay quietly where you are.\n\n"
            "Remember the geography is real: if you decide to travel to a city that is "
            "far away, the journey itself will take days, and during it you will see no one. "
            "Staying with your usual routine, or with whoever is here, costs nothing."
        )
        reply = self.llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.9,
            max_tokens=160,
        ).strip()
        return self._parse_action(reply)

    def _parse_action(self, reply: str) -> Dict:
        action = re.sub(r"\s+", " ", reply).strip()
        # Where do they go? (only if a known location is named)
        target_loc = None
        for loc in LOCATIONS:
            if loc.lower() in action.lower():
                target_loc = loc
                break
        # Whom do they seek? (only if another Heir is named)
        target_person = None
        for cid in self.world.agent_location:
            name = self._name_of(cid)
            if name and (name.lower() in action.lower() or cid in action.lower()):
                target_person = cid
                break
        return {"action": action, "location": target_loc, "person": target_person}

    # ------------------------------------------------------------------ #
    # Acting
    # ------------------------------------------------------------------ #
    def act(self, decision: Dict):
        """Apply the Heir's decision to the world, honouring commuting time."""
        if self.world.is_traveling(self.character_id):
            return  # already on the road; the engine advances the journey
        current = self.world.location_name(self.character_id)

        if decision.get("location"):
            target = decision["location"]
            if target != current:
                self.world.begin_travel(self.character_id, target)
        elif decision.get("person"):
            # Seek that person — go to their location (commuting time applies)
            target_loc = self.world.location_name(decision["person"])
            if target_loc != current:
                self.world.begin_travel(self.character_id, target_loc)

        self.world.add_event(f"{self.name}: {decision['action']}")

    # ------------------------------------------------------------------ #
    # Encounter reaction — a free exchange between Heirs
    # ------------------------------------------------------------------ #
    def _relationship_hints(self) -> str:
        """Who else is present, and how the Heir relates to them (canon)."""
        from src.core.relationships import get_relationships
        rels = {r["name"].lower(): r for r in get_relationships(self.character_id)}
        hints = []
        for cid in self.world.agent_location:
            if cid == self.character_id:
                continue
            name = self._name_of(cid)
            if not name:
                continue
            rel = rels.get(name.lower())
            if rel:
                hints.append(f"- {name} is here — {rel['role']} to you.")
        if not hints:
            return ""
        return "Those present and your relation to them:\n" + "\n".join(hints) + "\n"

    def react(self, others_lines: List[str]) -> str:
        """Given what others just said, reply freely and in character."""
        perceive = self._perceive()
        system = self.base_prompt + "\n\nYou are speaking with fellow Heirs, freely and in your own voice."
        hints = self._relationship_hints()
        transcript = "\n".join(others_lines)
        user = (
            f"{perceive}\n"
            + (f"{hints}" if hints else "")
            + f"\nWhat is being said around you:\n{transcript}\n\n"
            "What do you say or do in reply? Reply briefly, in character (1–3 sentences)."
        )
        return self.llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.85,
            max_tokens=140,
        ).strip()

    # ------------------------------------------------------------------ #
    # Remembering
    # ------------------------------------------------------------------ #
    def remember(self, event_text: str, importance: int = 1):
        """The Heir keeps this as a memory of their days."""
        self.memory.add_memory(
            self.character_id,
            mtype="world",
            content=event_text,
            importance=importance,
        )

    def remember_encounter(self, other_name: str, exchange: str):
        self.memory.add_memory(
            self.character_id,
            mtype="world",
            content=f"Exchanged words with {other_name}: {exchange[:240]}",
            importance=2,
        )
