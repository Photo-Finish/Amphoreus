# -*- coding: utf-8 -*-
"""Keyed lorebook activation — a gate in front of the vector store.

Why this exists: retrieval here is vector-only, so a question about **Kremnos** can
surface a passage about **Okhema** because they are close in embedding space, and
nothing can prevent it. The lorebook pattern (the one every mature character-chat
project converged on) is the opposite discipline: an entry listens for **keys**,
fires only when one is present, carries a **priority**, and can be **sticky** for a
few turns or **cool down** so the same passage is not shoved in twice.

This module is the mechanism, not a rewrite of retrieval. `activate()` returns what
should be pinned *before* vector results are added; the caller decides how much room
to give them.

    book = load_json(Path("databank/lorebook.json"))
    pinned = book.activate("What did Gorgo do at Kremnos?", turn=7)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

_WORD = re.compile(r"[a-z0-9']+")

# Keys shorter than this are matched as whole words only, so "ok" cannot fire
# inside "Okhema" or "broken".
_MIN_SUBSTRING_KEY = 5


def _normalise(text: str) -> str:
    return " ".join(_WORD.findall((text or "").lower()))


@dataclass
class Entry:
    """One lorebook entry."""

    keys: Sequence[str]
    text: str
    title: str = ""
    priority: int = 0
    sticky_turns: int = 0
    cooldown_turns: int = 0
    _last_fired: int = field(default=-10_000, repr=False)

    def matches(self, haystack: str) -> bool:
        for key in self.keys:
            k = _normalise(str(key))
            if not k:
                continue
            if len(k) < _MIN_SUBSTRING_KEY:
                if f" {k} " in f" {haystack} ":
                    return True
            elif k in haystack:
                return True
        return False

    def allowed(self, turn: int) -> bool:
        """Sticky entries stay for their window; others cool down after firing."""
        if self.sticky_turns and self._last_fired >= 0:
            if turn - self._last_fired <= self.sticky_turns:
                return True
        if self.cooldown_turns and turn - self._last_fired < self.cooldown_turns:
            return False
        return True

    def fire(self, turn: int) -> None:
        self._last_fired = turn


class Lorebook:
    """A set of entries that listen for keys."""

    def __init__(self, entries: Iterable[Entry] = ()):
        self.entries = list(entries)

    def __len__(self) -> int:
        return len(self.entries)

    def add(self, entry: Entry) -> None:
        self.entries.append(entry)

    def activate(self, text: str, turn: int = 0, limit: int = 4) -> list[Entry]:
        """The entries whose keys appear in `text`, most important first.

        Firing one entry does not suppress another that shares its keys: a
        question about Kremnos may legitimately want both the city and its king.
        Cooldowns are honoured so a long conversation does not repeat the same
        passage every turn.
        """
        haystack = _normalise(text)
        if not haystack:
            return []
        hits = [e for e in self.entries if e.matches(haystack) and e.allowed(turn)]
        hits.sort(key=lambda e: (-e.priority, e.title))
        chosen = hits[: max(0, limit)]
        for entry in chosen:
            entry.fire(turn)
        return chosen

    def pinned_text(self, text: str, turn: int = 0, limit: int = 4) -> str:
        """Convenience: the activated entries as one block for a prompt."""
        chosen = self.activate(text, turn=turn, limit=limit)
        if not chosen:
            return ""
        parts = []
        for entry in chosen:
            label = entry.title or ", ".join(str(k) for k in entry.keys[:2])
            parts.append(f"## {label}\n{entry.text}".strip())
        return "\n\n".join(parts)


def from_dicts(rows: Iterable[dict]) -> Lorebook:
    """Build from plain data — a JSON lorebook file, or the databank."""
    book = Lorebook()
    for row in rows:
        keys = row.get("keys") or row.get("key") or []
        if isinstance(keys, str):
            keys = [k.strip() for k in keys.split(",") if k.strip()]
        text = str(row.get("text") or "").strip()
        if not keys or not text:
            continue
        book.add(Entry(
            keys=list(keys),
            text=text,
            title=str(row.get("title") or ""),
            priority=int(row.get("priority") or 0),
            sticky_turns=int(row.get("sticky_turns") or 0),
            cooldown_turns=int(row.get("cooldown_turns") or 0),
        ))
    return book


def from_markdown(path, *, title_from_heading: bool = True) -> Lorebook:
    r"""Turn a databank profile into entries - one per ## section.

    Keys are the section's **own** words ("Coreflame & Path" -> coreflame, path), not
    the Heir's name: the Heir is always the speaker, so a name key fires every section
    at once and the passage that answers the question gets lost among them. Measured
    2026-10-28: keyed on the name, "What is your Coreflame?" pinned Appearance and
    Biography before Coreflame & Path.
    """
    from pathlib import Path as _Path

    path = _Path(path)
    skip = {"the", "and", "for", "with", "your", "their", "its", "a", "of"}

    def _keys(section: str) -> list:
        words = [w for w in _WORD.findall(section.lower()) if len(w) >= 4 and w not in skip]
        # singular/plural both fire: "relationship" should answer "relationships"
        return sorted({w for w in words} | {w[:-1] for w in words if w.endswith("s") and len(w) > 5})

    rows = []
    section, buf = "", []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if section and buf:
                rows.append({"keys": _keys(section), "title": f"{path.stem} - {section}",
                             "text": "\n".join(buf).strip(), "priority": 1})
            section, buf = line[3:].strip(), []
        elif section:
            buf.append(line)
    if section and buf:
        rows.append({"keys": _keys(section), "title": f"{path.stem} - {section}",
                     "text": "\n".join(buf).strip(), "priority": 1})
    _ = title_from_heading
    return from_dicts(rows)
