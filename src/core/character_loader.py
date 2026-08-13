"""
Character Loader — Loads Chrysos Heir character cards from JSON and builds system prompts.

Usage:
    from core.character_loader import CharacterLoader
    loader = CharacterLoader("src/characters")
    phainon = loader.load("phainon")
    prompt = loader.build_system_prompt("phainon")
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any


class CharacterLoader:
    """Loads and manages Chrysos Heir character definitions."""

    def __init__(self, characters_dir: str = "src/characters"):
        self.characters_dir = Path(characters_dir)
        self._cache: Dict[str, dict] = {}

    def list_characters(self) -> list[str]:
        """List all available character IDs."""
        return [
            f.stem
            for f in self.characters_dir.glob("*.json")
        ]

    def load(self, character_id: str) -> dict:
        """Load a character card from JSON, caching in memory."""
        if character_id in self._cache:
            return self._cache[character_id]

        filepath = self.characters_dir / f"{character_id}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Character card not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._cache[character_id] = data
        return data

    @property
    def project_root(self) -> Path:
        """The Amphoreus project root (where the per-Heir folders live)."""
        d = Path(self.characters_dir)
        if d.is_absolute():
            return d.parent.parent
        return (Path.cwd() / d).resolve().parent.parent

    def build_system_prompt(self, character_id: str) -> str:
        """Build the system prompt from a character card."""
        card = self.load(character_id)
        prompts = card.get("prompts", {})

        # Use the explicit system_prompt if available
        system_prompt = prompts.get("system_prompt", "")

        # Append the canonical relationships web — recognisable inter-Heir
        # links (teacher/student, Imperator/subordinate, rivals, partners…).
        from src.core.relationships import build_relationships_block
        rel_block = build_relationships_block(character_id)
        if rel_block:
            system_prompt += "\n\n" + rel_block
        else:
            relationships = card.get("relationships", {})
            if relationships:
                system_prompt += "\n\nYour relationships:\n"
                for name, rel in relationships.items():
                    system_prompt += f"- {name}: {rel.get('type', 'acquaintance')}. {rel.get('description', '')}\n"

        # Append speech pattern reminders
        speech = card.get("speech", {})
        if speech:
            system_prompt += "\n\nSpeech patterns to maintain:\n"
            system_prompt += f"- Formality: {speech.get('formality', 'natural')}\n"
            system_prompt += f"- Tone: {speech.get('tone', 'neutral')}\n"
            if speech.get("catchphrases"):
                system_prompt += f"- Occasional phrases: {', '.join(speech['catchphrases'])}\n"
            # The measured voice guide (tools/measure_speech.py) — plain, factual,
            # anti-theatrical guidance derived from the Heir's own canon lines.
            voice_guide = (speech.get("style_measured") or {}).get("voice_guide")
            if voice_guide:
                system_prompt += f"- {voice_guide}\n"

        # Append how the Heir perceives the world (hearing / eyesight)
        senses = card.get("senses", {})
        if senses:
            system_prompt += "\n\nHow you perceive the world (your senses):\n"
            if senses.get("vision"):
                system_prompt += f"- Sight: {senses['vision']}\n"
            if senses.get("hearing"):
                system_prompt += f"- Hearing: {senses['hearing']}\n"
            if senses.get("notes"):
                system_prompt += f"- {senses['notes']}\n"

        # Append the Heir's own canon words (the personal-memories voice
        # digest), so the model studies what they actually said.
        try:
            from src.core.personal_memory import voice_digest
            digest = voice_digest(character_id, self.project_root)
            if digest:
                system_prompt += "\n\n" + digest
        except Exception:
            pass  # never let the digest break the prompt

        # Append the shared world-knowledge boundary: the Heirs live in
        # Amphoreus and must NEVER display real-world / modern / out-of-universe
        # knowledge (e.g. a scholar citing pseudo-differential operators). One
        # block at this choke point covers the sanctuary, the world engine and
        # the style test alike.
        try:
            from src.core.world_knowledge import world_knowledge_block
            system_prompt += "\n\n" + world_knowledge_block()
        except Exception:
            pass  # never let the boundary block break the prompt

        return system_prompt

    def get_greeting(self, character_id: str) -> str:
        """Get the character's greeting message."""
        card = self.load(character_id)
        return card.get("prompts", {}).get("greeting", "Hello.")

    def get_identity(self, character_id: str) -> dict:
        """Get the character's identity block."""
        card = self.load(character_id)
        return card.get("identity", {})

    def get_personality(self, character_id: str) -> dict:
        """Get the character's personality block."""
        card = self.load(character_id)
        return card.get("personality", {})

    def get_relationships(self, character_id: str) -> dict:
        """Get the character's relationship graph."""
        card = self.load(character_id)
        return card.get("relationships", {})

    def get_knowledge_base_path(self, character_id: str) -> Optional[str]:
        """Get the path to the character's knowledge base for RAG."""
        card = self.load(character_id)
        rag_config = card.get("rag", {})
        return rag_config.get("knowledge_base_path")

    def validate_card(self, character_id: str) -> list[str]:
        """Validate a character card and return list of issues."""
        issues = []
        card = self.load(character_id)

        required_sections = ["meta", "identity", "personality", "speech", "prompts"]
        for section in required_sections:
            if section not in card:
                issues.append(f"Missing required section: {section}")

        if "prompts" in card:
            if "system_prompt" not in card["prompts"]:
                issues.append("Missing system_prompt in prompts section")
            if "greeting" not in card["prompts"]:
                issues.append("Missing greeting in prompts section")

        return issues
