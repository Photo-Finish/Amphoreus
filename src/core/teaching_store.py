"""
Teaching Store — the Heirs' ledger of what the star-stranger has taught them.

The Heirs live in Amphoreus and know nothing of the world beyond the stars
(see world_knowledge.py). But the visitor may TEACH them such things — advanced
mathematics, the truths of our world, anything. Instead of a mask ("pretend
you don't know"), each Heir keeps an EPISTEMIC LEDGER: for every topic the
visitor brings, it tracks the Heir's genuine journey —

    foreign  ->  studied  ->  adopted | refuted | unsure

- foreign:   the Heir has no framework for it and does NOT fake understanding;
             they react from their own world (curiosity, skepticism, awe).
- studied:   the Heir is in dialogue — asking questions, mapping the idea onto
             their own worldview, pushing back where it collides.
- adopted / refuted / unsure: the Heir's persistent verdict, reached through
             teaching and debate, with their own reasoning.

The ledger persists across visits (`teaching.json` in the Heir's folder) and is
injected into the system prompt, so "unlocking" knowledge is EARNED and DURABLE
rather than a toggle.

Lives as `teaching.json` inside each Heir's folder:

    SkeMma720-Anaxa/teaching.json
    {
      "character_id": "anaxa",
      "seeded": true,
      "topics": {
        "calculus": {
          "state": "adopted",
          "claim": "the mathematics of change",
          "first_seen": "...",
          "updated": "...",
          "exchanges": 3,
          "questions": ["What craft does this belong to?"],
          "verdict": "adopted",
          "verdict_reason": "..."
        }
      }
    }
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .heir_folders import resolve_heir_folder

TEACHING_FILE = "teaching.json"


def topic_key(text: str) -> str:
    """Derive a stable short key for a taught topic from the visitor's words."""
    t = (text or "").strip().lower()
    m = re.search(r"teach\s+(?:you\s+)?(?:about\s+)?([^.,;!?—–]+)", t)
    if m:
        phrase = m.group(1).strip()
    else:
        m = re.search(r"(?:about|of|is)\s+([^.,;!?—–]+)", t)
        phrase = m.group(1).strip() if m else t
    phrase = re.sub(r"^(the|a|an|some|this|that)\s+", "", phrase)
    words = phrase.split()[:5]
    if not words:
        return "the-star-stranger-s-teaching"
    key = "-".join(re.sub(r"[^a-z0-9]+", "", w) or "x" for w in words)
    return key or "the-star-stranger-s-teaching"


def display_topic(topic: str) -> str:
    """Human-readable form of a topic key."""
    return topic.replace("-", " ")


class TeachingStore:
    """Per-Heir ledger of what the star-stranger has taught them."""

    def __init__(self, memory_root: str | Path = "."):
        self.memory_root = Path(memory_root)

    # ------------------------------------------------------------------ #
    def _path(self, character_id: str) -> Path:
        return resolve_heir_folder(character_id, self.memory_root) / TEACHING_FILE

    def get(self, character_id: str) -> Dict:
        """Load the Heir's teaching ledger (seeding an empty one on first use)."""
        path = self._path(character_id)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "topics" in data:
                    return data
            except Exception:
                pass
        data = {
            "character_id": character_id,
            "seeded": True,
            "seeded_at": datetime.now().isoformat(timespec="milliseconds"),
            "topics": {},
        }
        self._save(character_id, data)
        return data

    def _save(self, character_id: str, data: Dict):
        self._path(character_id).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def get_topic(self, character_id: str, key: str) -> Optional[Dict]:
        return self.get(character_id).get("topics", {}).get(key)

    def state(self, character_id: str, key: str) -> str:
        t = self.get_topic(character_id, key)
        return (t or {}).get("state", "foreign")

    def topics(self, character_id: str) -> List[Dict]:
        return list(self.get(character_id).get("topics", {}).values())

    def studying(self, character_id: str) -> List[Dict]:
        return [t for t in self.topics(character_id) if t.get("state") == "studied"]

    def resolved(self, character_id: str) -> List[Dict]:
        return [t for t in self.topics(character_id)
                if t.get("state") in ("adopted", "refuted", "unsure")]

    def latest_active_key(self, character_id: str) -> Optional[str]:
        """Key of the most recently updated studied/resolved topic (for verdict
        questions that don't name the topic again). On equal timestamps, the
        most recently inserted topic wins."""
        topics = self.get(character_id).get("topics", {})
        best, best_ts = None, ""
        for k, t in topics.items():
            if t.get("state") in ("studied", "adopted", "refuted", "unsure"):
                ts = t.get("updated", "")
                if ts >= best_ts:
                    best, best_ts = k, ts
        return best

    # ------------------------------------------------------------------ #
    # Mutations
    # ------------------------------------------------------------------ #
    def record_exchange(self, character_id: str, key: str,
                        question: str = "", claim: str = ""):
        """Log a teaching turn: creates the topic (as studied) if new, bumps
        the exchange count, and stores any question the Heir asked."""
        data = self.get(character_id)
        topics = data.setdefault("topics", {})
        now = datetime.now().isoformat(timespec="milliseconds")
        if key not in topics:
            topics[key] = {
                "state": "studied", "claim": claim,
                "first_seen": now, "updated": now,
                "exchanges": 0, "questions": [], "verdict": "",
                "verdict_reason": "",
            }
        t = topics[key]
        t["updated"] = now
        t["exchanges"] = int(t.get("exchanges", 0)) + 1
        if claim and not t.get("claim"):
            t["claim"] = claim
        q = (question or "").strip()
        if q and "?" in q and q not in t.get("questions", []):
            t.setdefault("questions", []).append(q)
        self._save(character_id, data)

    def set_verdict(self, character_id: str, key: str, verdict: str,
                    reason: str = ""):
        """Commit the Heir's verdict on a taught topic."""
        data = self.get(character_id)
        topics = data.setdefault("topics", {})
        if key not in topics:
            topics[key] = {"state": "studied", "claim": ""}
        v = verdict if verdict in ("adopted", "refuted", "unsure") else "unsure"
        topics[key]["state"] = v
        topics[key]["verdict"] = v
        if reason:
            topics[key]["verdict_reason"] = reason
        topics[key]["updated"] = datetime.now().isoformat(timespec="milliseconds")
        self._save(character_id, data)

    # ------------------------------------------------------------------ #
    # Prompt block (injected into the Heir's system prompt in chat/teach)
    # ------------------------------------------------------------------ #
    def to_prompt_block(self, character_id: str) -> str:
        """Format the ledger as a prompt section — what the star-stranger has
        taught the Heir and what they concluded about it."""
        topics = self.get(character_id).get("topics", {})
        if not topics:
            return ""
        lines = ["# What the star-stranger has taught you (the world beyond the stars)"]
        for key, t in topics.items():
            name = display_topic(key)
            st = t.get("state", "studied")
            reason = t.get("verdict_reason") or ""
            if st == "adopted":
                lines.append(f"- {name}: you have ACCEPTED this. {reason or 'It held up against your doubts.'}")
            elif st == "refuted":
                lines.append(f"- {name}: you have REJECTED this. {reason or 'It did not hold up against what you know.'}")
            elif st == "unsure":
                lines.append(f"- {name}: you remain UNCERTAIN. {reason or 'You have not decided.'}")
            else:
                lines.append(f"- {name}: you are still STUDYING this — you have been told of it and are weighing it against your world.")
        lines.append("You know nothing else of the world beyond the stars.")
        return "\n".join(lines).strip()
