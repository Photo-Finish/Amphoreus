"""
Chronicle — the factual record of the little Amphoreus.

Every event the Heirs live is appended here. It is a *log written by their
actions*, never a script — the engine hosts time; the Heirs author their days.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class Chronicle:
    """Append-only record of the Heirs' days (JSONL + rendered markdown)."""

    def __init__(self, path: str = "world_runtime/chronicle"):
        self.jsonl_path = f"{path}.jsonl"
        self.md_path = f"{path}.md"
        os.makedirs(os.path.dirname(os.path.abspath(self.jsonl_path)), exist_ok=True)

    def append(self, entry: Dict):
        """Append an event entry. entry: {time, text, kind}."""
        entry.setdefault("kind", "event")
        entry.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        with open(self.md_path, "a", encoding="utf-8") as f:
            f.write(f"**{entry['time']}** — {entry['text']}\n")

    def read(self, limit: int = 50) -> List[Dict]:
        """Read the most recent entries (newest first)."""
        if not os.path.exists(self.jsonl_path):
            return []
        entries = []
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
        return entries[-limit:][::-1]

    def count(self) -> int:
        if not os.path.exists(self.jsonl_path):
            return 0
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    def read_markdown(self, limit: int = 60) -> str:
        """Return the recent chronicle as readable markdown (newest first)."""
        entries = self.read(limit)
        if not entries:
            return "*The chronicle is yet empty. The Heirs have not begun their days.*"
        return "\n\n".join(f"**{e.get('time', '')}** — {e.get('text', '')}" for e in entries)
