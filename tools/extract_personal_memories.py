"""
extract_personal_memories.py — copy each Heir's dialogue from the canon databank
into their personal folder as "personal memory".

For every Chrysos Heir we scan the mission dialogue files (chapters, adventures,
key-character-moments, index) and copy the dialogue *parts* where that Heir
appears — recognising where a part starts and ends. A part is a coherent
dialogue moment:

  * an exchange where the Heir SPEAKS (their name / an alias is the speaker),
  * widened to the exchange before it (what they reply to) and the exchange
    after it (the response),
  * bounded by the in-story context (## / ### headers) and scene breaks (---).

Overlapping parts are merged so one continuous scene becomes one part. The
result is written to `<HeirFolder>/personal-memories.md`.

The databank is NEVER modified — this script only reads it.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.knowledge.kb_builder import CHARACTER_ALIASES  # noqa: E402
from src.core.heir_folders import HEIR_FOLDERS  # noqa: E402

MISSION_PATTERNS = [
    "missions/chapter-*.md",
    "missions/INDEX.md",
    "missions/key-character-moments.md",
    "missions/adventure/*.md",
]

SPEAKER_RE = re.compile(r"^\s*>?\s*\*\*(.+?):\*\*\s*(.*)$")
SEPARATOR_RE = re.compile(r"^\s*---+\s*$")
HEADER_RE = re.compile(r"^(#{1,4})\s+(.*)$")


def speaker_of(line: str):
    """Return the speaker label (without ** :) of a dialogue line, or None."""
    m = SPEAKER_RE.match(line)
    return m.group(1).strip() if m else None


def is_alias_in_text(text: str, aliases) -> bool:
    t = text.lower()
    return any(a.lower() in t for a in aliases)


def sections_equal(a, b) -> bool:
    return [t for _, t in a] == [t for _, t in b]


def build_exchanges(path: Path):
    """Return (lines, items) where items is a list of
    (section_stack, [line_index, ...]) — one item per contiguous dialogue
    block, plus a sentinel item for scene breaks."""
    lines = path.read_text(encoding="utf-8").splitlines()
    sections: list[tuple[int, str]] = []
    exchange: list[int] = []
    result = []

    def flush():
        nonlocal exchange
        if exchange:
            result.append((list(sections), list(exchange)))
            exchange = []

    for i, line in enumerate(lines):
        m = HEADER_RE.match(line)
        if m:
            flush()
            level, title = len(m.group(1)), m.group(2).strip()
            while sections and sections[-1][0] >= level:
                sections.pop()
            sections.append((level, title))
        elif SEPARATOR_RE.match(line):
            flush()
            result.append((list(sections), ["<<<SCENEBREAK>>>"]))
        elif line.strip() == "":
            flush()
        else:
            exchange.append(i)
    flush()
    return lines, result


def section_title(sections) -> str:
    return " > ".join(t for _, t in sections)


def collect_for_character(character_id: str, databank: Path):
    aliases = CHARACTER_ALIASES.get(character_id, [character_id])
    parts = []

    for pattern in MISSION_PATTERNS:
        for path in sorted(databank.glob(pattern)):
            if not (path.is_file() and path.suffix.lower() == ".md"):
                continue
            lines, items = build_exchanges(path)

            # 1. Indices of exchanges where the Heir is a speaker.
            hot = []
            for idx, (_, span) in enumerate(items):
                if span == ["<<<SCENEBREAK>>>"]:
                    continue
                spk = [speaker_of(lines[li]) for li in span]
                if any(s and is_alias_in_text(s, aliases) for s in spk):
                    hot.append(idx)

            # 2. Context window per hot exchange: previous + next exchange,
            #    staying inside the same scene (same section, no break).
            windowed = []
            for idx in hot:
                lo, hi = idx, idx
                if idx - 1 >= 0 and items[idx - 1][1] != ["<<<SCENEBREAK>>>"]:
                    if sections_equal(items[idx - 1][0], items[idx][0]):
                        lo = idx - 1
                if idx + 1 < len(items) and items[idx + 1][1] != ["<<<SCENEBREAK>>>"]:
                    if sections_equal(items[idx + 1][0], items[idx][0]):
                        hi = idx + 1
                windowed.append((lo, hi))

            # 3. Merge overlapping / adjacent windows into single parts.
            merged = []
            for lo, hi in sorted(windowed):
                if merged and lo <= merged[-1][1] + 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
                else:
                    merged.append((lo, hi))

            # 4. Materialise each part.
            for lo, hi in merged:
                section = ""
                seen = []
                for idx in range(lo, hi + 1):
                    secs, span = items[idx]
                    if span == ["<<<SCENEBREAK>>>"]:
                        continue
                    section = section_title(secs)
                    for li in range(span[0], span[-1] + 1):
                        seen.append(lines[li])
                if seen:
                    parts.append((path, section, seen))
    return parts


def write_memory(character_id: str, parts, root: Path):
    folder = root / HEIR_FOLDERS.get(character_id, character_id)
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / "personal-memories.md"
    header = (
        f"# {character_id} — Personal Memories\n\n"
        "> Verbatim dialogue from the canon databank where this Heir appears, "
        "copied (never modified in the databank) to serve as personal memory. "
        "Each part shows the source file and the in-story context (chapter / "
        "mission / scene), and is bounded to a coherent dialogue moment.\n\n"
    )
    body = []
    for i, (path, section, lines) in enumerate(parts, 1):
        src = str(path.relative_to(root)).replace("\\", "/")
        body.append(f"---\n\n### Part {i} — `{src}`\n")
        if section:
            body.append(f"**Context:** {section}\n")
        body.append("")
        body.extend(lines)
        body.append("")
    out.write_text(header + "\n".join(body), encoding="utf-8")
    return out, len(parts), sum(len(p[2]) for p in parts)


def main():
    databank = ROOT / "databank"
    total = 0
    for character_id in CHARACTER_ALIASES:
        parts = collect_for_character(character_id, databank)
        out, n_parts, n_lines = write_memory(character_id, parts, ROOT)
        print(f"{character_id:<28} {n_parts:>3} parts / {n_lines:>5} lines -> {out.relative_to(ROOT)}")
        total += n_parts
    print(f"\nTotal parts extracted: {total}")


if __name__ == "__main__":
    main()
