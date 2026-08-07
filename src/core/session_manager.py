"""
Session Manager — Manages conversation history and context for AI Chrysos Heirs.

Usage:
    from core.session_manager import SessionManager
    session = SessionManager()
    session.add_message("phainon", "user", "Hello!")
    history = session.get_history("phainon")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConversationSession:
    """A conversation session with a specific character."""
    character_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    context: Dict = field(default_factory=dict)

    def add(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))

    def get_recent(self, n: int = 10) -> List[Message]:
        return self.messages[-n:] if len(self.messages) > n else self.messages

    def to_openai_format(self, system_prompt: str, max_history: int = 20) -> List[dict]:
        """Convert to OpenAI-compatible message format."""
        messages = [{"role": "system", "content": system_prompt}]

        recent = self.get_recent(max_history)
        for msg in recent:
            messages.append({"role": msg.role, "content": msg.content})

        return messages


class SessionManager:
    """Manages multiple conversation sessions."""

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self._sessions: Dict[str, ConversationSession] = {}

    def get_or_create(self, character_id: str) -> ConversationSession:
        """Get existing session or create new one for a character."""
        if character_id not in self._sessions:
            self._sessions[character_id] = ConversationSession(character_id=character_id)
        return self._sessions[character_id]

    def add_message(self, character_id: str, role: str, content: str):
        """Add a message to a character's session."""
        session = self.get_or_create(character_id)
        session.add(role, content)

    def get_history(self, character_id: str) -> List[Message]:
        """Get the conversation history for a character."""
        session = self.get_or_create(character_id)
        return session.messages

    def clear(self, character_id: str):
        """Clear conversation history for a character."""
        if character_id in self._sessions:
            del self._sessions[character_id]

    def set_context(self, character_id: str, key: str, value):
        """Set arbitrary context for a session (e.g., scenario, timeline)."""
        session = self.get_or_create(character_id)
        session.context[key] = value

    def get_context(self, character_id: str, key: str, default=None):
        """Get context from a session."""
        session = self.get_or_create(character_id)
        return session.context.get(key, default)
