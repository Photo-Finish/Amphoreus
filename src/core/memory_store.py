"""
Memory Store — persistent per-character memory for the Chrysos Heirs.

Each Heir's personal folder (see `heir_folders.py`) IS their memory database:

    NeiKos496-Phainon/
    ├── bond.json        # relationship with the visitor (friendship level, visits, summary)
    ├── history.jsonl    # conversation history (append-only, JSON per line)
    ├── memories.jsonl   # long-term memories (shared / preference / moment / world / sensory …)
    └── preferences.json # managed by PreferenceStore (aesthetics, tastes, likes, dislikes)

JSONL is append-only (fast, crash-safe) and human-inspectable — the folders
remain readable as the Heirs' living records. Thread-safe (locks per Heir) so
the chat UI and the world engine can share them.
"""

import json
import os
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .heir_folders import resolve_heir_folder

# Friendship progression
FRIENDSHIP_LEVELS = ["stranger", "acquaintance", "friend", "close friend", "best friend"]

# Memory types
MTYPE_SHARED = "shared"        # something the visitor shared about themselves
MTYPE_PREFERENCE = "preference"  # a preference / like / dislike the visitor revealed
MTYPE_MOMENT = "moment"        # a significant shared moment
MTYPE_WORLD = "world"          # an event witnessed in the little Amphoreus
MTYPE_INSIDE = "inside_joke"   # an inside joke between Heir and visitor
MTYPE_SENSORY = "sensory"      # something the Heir saw or heard (eyesight / hearing)

# File names inside each Heir's folder
BOND_FILE = "bond.json"
HISTORY_FILE = "history.jsonl"
MEMORIES_FILE = "memories.jsonl"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class MemoryStore:
    """Per-Heir JSON/JSONL memory, stored inside each Heir's personal folder."""

    def __init__(self, memory_root: str | Path = "."):
        """
        Args:
            memory_root: directory that contains the per-Heir folders
                         (default: the project root, where the folders live).
        """
        self.memory_root = Path(memory_root)
        self._locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)

    # ------------------------------------------------------------------ #
    # Paths
    # ------------------------------------------------------------------ #
    def _folder(self, character_id: str) -> Path:
        return resolve_heir_folder(character_id, self.memory_root)

    def _lock(self, character_id: str) -> threading.Lock:
        return self._locks[character_id]

    # ------------------------------------------------------------------ #
    # Bond
    # ------------------------------------------------------------------ #
    def record_visit(self, character_id: str) -> Dict:
        """Record a visit; returns the (updated) bond record."""
        with self._lock(character_id):
            path = self._folder(character_id) / BOND_FILE
            if path.exists():
                try:
                    bond = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    bond = {}
            else:
                bond = {}
            now = _now()
            if not bond:
                bond = {
                    "character_id": character_id,
                    "first_met": now,
                    "visits": 0,
                    "friendship_level": "stranger",
                    "user_summary": "",
                    "last_seen": now,
                }
            bond["visits"] = bond.get("visits", 0) + 1
            bond["last_seen"] = now
            bond = self._recompute_friendship(character_id, bond)
            path.write_text(
                json.dumps(bond, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return bond

    def get_bond(self, character_id: str) -> Optional[Dict]:
        path = self._folder(character_id) / BOND_FILE
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def update_user_summary(self, character_id: str, summary: str):
        with self._lock(character_id):
            bond = self.get_bond(character_id) or {}
            bond["user_summary"] = summary
            (self._folder(character_id) / BOND_FILE).write_text(
                json.dumps(bond, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    def _recompute_friendship(self, character_id: str, bond: Dict) -> Dict:
        """Friendship grows with visits, conversation, and shared memories."""
        turns = self.history_count(character_id)
        mem = sum(
            1
            for m in self._read_memories(character_id)
            if m.get("mtype") != MTYPE_WORLD
        )
        visits = bond.get("visits", 1)
        score = visits + turns // 6 + mem * 2
        if score >= 40:
            level = "best friend"
        elif score >= 20:
            level = "close friend"
        elif score >= 8:
            level = "friend"
        elif score >= 3:
            level = "acquaintance"
        else:
            level = "stranger"
        bond["friendship_level"] = level
        return bond

    # ------------------------------------------------------------------ #
    # History
    # ------------------------------------------------------------------ #
    def add_history(self, character_id: str, role: str, content: str):
        with self._lock(character_id):
            entry = {"role": role, "content": content, "ts": _now()}
            with open(self._folder(character_id) / HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_recent_history(self, character_id: str, n: int = 30) -> List[Dict]:
        entries = self._read_history(character_id)
        return entries[-n:]

    def history_count(self, character_id: str) -> int:
        return len(self._read_history(character_id))

    # ------------------------------------------------------------------ #
    # Long-term memories
    # ------------------------------------------------------------------ #
    def add_memory(
        self,
        character_id: str,
        mtype: str,
        content: str,
        importance: int = 2,
    ):
        with self._lock(character_id):
            entry = {
                "mtype": mtype,
                "content": content,
                "importance": importance,
                "ts": _now(),
            }
            with open(self._folder(character_id) / MEMORIES_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_memories(
        self,
        character_id: str,
        mtype: Optional[str] = None,
        limit: int = 40,
        min_importance: int = 0,
    ) -> List[Dict]:
        entries = self._read_memories(character_id)
        filtered = [
            e
            for e in entries
            if (mtype is None or e.get("mtype") == mtype)
            and e.get("importance", 0) >= min_importance
        ]
        return filtered[-limit:]

    def get_world_memories(self, character_id: str, limit: int = 10) -> List[Dict]:
        return self.get_memories(character_id, mtype=MTYPE_WORLD, limit=limit)

    def memory_count(self, character_id: str) -> int:
        return len(self._read_memories(character_id))

    # ------------------------------------------------------------------ #
    # Consolidation — old history becomes durable memory
    # ------------------------------------------------------------------ #
    def consolidate(self, character_id: str, keep_recent: int = 20, max_chars: int = 400):
        """Fold history older than the recent window into a single memory entry."""
        with self._lock(character_id):
            entries = self._read_history(character_id)
            if len(entries) <= keep_recent:
                return 0

            old = entries[: len(entries) - keep_recent]
            recent = entries[len(entries) - keep_recent :]

            parts = []
            for e in old:
                role = "Visitor" if e.get("role") == "user" else "You"
                text = str(e.get("content", "")).strip().replace("\n", " ")
                if len(text) > 120:
                    text = text[:120] + "…"
                parts.append(f"{role}: {text}")
            summary = " · ".join(parts)
            if len(summary) > max_chars:
                summary = summary[:max_chars] + "…"

            mem_entry = {
                "mtype": MTYPE_SHARED,
                "content": summary,
                "importance": 1,
                "ts": _now(),
            }
            # rewrite history.jsonl with only the recent window
            path = self._folder(character_id) / HISTORY_FILE
            with open(path, "w", encoding="utf-8") as f:
                for e in recent:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
            # append the folded memory
            with open(self._folder(character_id) / MEMORIES_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(mem_entry, ensure_ascii=False) + "\n")
            return len(old)

    # ------------------------------------------------------------------ #
    # Reset / introspection
    # ------------------------------------------------------------------ #
    def clear_character(self, character_id: str):
        """Erase the Heir's memory of the visitor (keeps preferences.json)."""
        with self._lock(character_id):
            folder = self._folder(character_id)
            for name in (BOND_FILE, HISTORY_FILE, MEMORIES_FILE):
                p = folder / name
                if p.exists():
                    os.remove(p)

    def stats(self) -> Dict:
        """Global memory statistics (across all Heir folders)."""
        heirs = 0
        turns = 0
        mems = 0
        for folder in self.memory_root.iterdir():
            if not folder.is_dir():
                continue
            if (folder / BOND_FILE).exists():
                heirs += 1
            if (folder / HISTORY_FILE).exists():
                turns += sum(1 for _ in open(folder / HISTORY_FILE, encoding="utf-8"))
            if (folder / MEMORIES_FILE).exists():
                mems += sum(1 for _ in open(folder / MEMORIES_FILE, encoding="utf-8"))
        return {"heirs_with_bonds": heirs, "history_turns": turns, "memories": mems}

    def close(self):
        pass

    # ------------------------------------------------------------------ #
    # Internal readers
    # ------------------------------------------------------------------ #
    def _read_history(self, character_id: str) -> List[Dict]:
        path = self._folder(character_id) / HISTORY_FILE
        return _read_jsonl(path)

    def _read_memories(self, character_id: str) -> List[Dict]:
        path = self._folder(character_id) / MEMORIES_FILE
        return _read_jsonl(path)


def _read_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    result = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        result.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return result
