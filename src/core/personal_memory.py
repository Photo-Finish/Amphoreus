"""
personal_memory.py — lets the model study a Heir's personal memories.

Each Heir's folder contains `personal-memories.md` — their verbatim canon
dialogue extracted by `tools/extract_personal_memories.py`. This module turns
that file into a compact **voice digest**: a representative sample of the
Heir's OWN spoken lines (matched by their aliases), spread across their whole
story, injected into the system prompt so the model hears their real voice.

Parsing is cached (per Heir + file mtime) so per-chat cost stays trivial.
"""

import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

from src.knowledge.kb_builder import CHARACTER_ALIASES
from src.core.heir_folders import HEIR_FOLDERS

SPEAKER_RE = re.compile(r"^\s*>?\s*\*\*(.+?):\*\*\s*(.*)$")
PART_HEADER_RE = re.compile(r"^###\s+Part\s+\d+")
CONTEXT_RE = re.compile(r"^\*\*Context:\*\*")
SEPARATOR_RE = re.compile(r"^\s*---+\s*$")


def memory_file(character_id: str, root: Path) -> Optional[Path]:
    folder = root / HEIR_FOLDERS.get(character_id, character_id)
    f = folder / "personal-memories.md"
    return f if f.exists() else None


@lru_cache(maxsize=None)
def _parse_cached(path_str: str, mtime: float) -> List[List[str]]:
    """Parse personal-memories.md into parts (list of dialogue lines)."""
    path = Path(path_str)
    parts: List[List[str]] = []
    current: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if SEPARATOR_RE.match(line):
            if current:
                parts.append(current)
                current = []
            continue
        if PART_HEADER_RE.match(line) or CONTEXT_RE.match(line):
            continue
        if line.strip() == "":
            continue
        current.append(line)
    if current:
        parts.append(current)
    return parts


def read_parts(character_id: str, root: Path) -> List[List[str]]:
    f = memory_file(character_id, root)
    if f is None:
        return []
    return _parse_cached(str(f), f.stat().st_mtime)


def own_speaker_lines(character_id: str, root: Path) -> List[Tuple[str, str]]:
    """Return (line, part_context) for every line where the Heir speaks."""
    aliases = CHARACTER_ALIASES.get(character_id, [character_id])
    out: List[Tuple[str, str]] = []
    for part in read_parts(character_id, root):
        for line in part:
            m = SPEAKER_RE.match(line)
            if not m:
                continue
            speaker = m.group(1).strip()
            if any(a.lower() in speaker.lower() for a in aliases):
                out.append((line, ""))
    return out


def voice_digest(
    character_id: str,
    root: Path,
    max_lines: int = 22,
    aliases: Optional[List[str]] = None,
) -> str:
    """A representative sample of the Heir's own canon lines.

    Lines are sampled evenly across the Heir's whole story (the parts are
    ordered chapter by chapter), so the digest spans their life — not just
    their first scene.
    """
    lines = own_speaker_lines(character_id, root)
    if not lines:
        return ""

    sampled = lines
    if len(lines) > max_lines:
        # Evenly spread indices across the full ordered list.
        idxs = {int(i * (len(lines) - 1) / (max_lines - 1)) for i in range(max_lines)}
        sampled = [lines[i] for i in sorted(idxs)]

    quoted_lines = []
    for l, _ in sampled:
        m = SPEAKER_RE.match(l)
        if not m:
            continue
        text = m.group(2).strip().replace("**", "")
        if text:
            quoted_lines.append(f'> "{text}"')
    quoted = "\n".join(quoted_lines)
    if not quoted:
        return ""

    return (
        "# Your own words — study these (verbatim from the canon)\n\n"
        "The lines below are things you have actually said in the canon. "
        "Let them shape your voice, your cadence, and your heart.\n\n"
        f"{quoted}"
    )
