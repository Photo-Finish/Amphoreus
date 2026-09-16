"""Attribute canon mission dialogue into personal vs collective memories.

Reads databank mission/script markdown. Never writes those files.
Memories are verbatim extracts plus attribution headers — no invented speech.

Prior extract (`tools/extract_personal_memories.py`) kept only a ±1 exchange
window around lines where an alias substring appeared as speaker. That
truncated scenes, dropped silent witnesses, and dumped Titan/title hits
(Oronyx, Thanatos, Aquila, Kephale, Dolimem, …) onto the wrong Heir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

SPEAKER_RE = re.compile(r"^\s*>?\s*\*\*(.+?):\*\*\s*(.*)$")
HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$")
SEPARATOR_RE = re.compile(r"^\s*---+\s*$")
TALK_TO_RE = re.compile(
    r"^\s*>?\s*\*{0,3}\(\s*Talk to (.+?)\s*\)\*{0,3}:?\*{0,3}\s*$",
    re.IGNORECASE,
)
# Wiki /Dialogue pages: :**Tribbie:** or ::**Tribbie:**
WIKI_SPEAKER_RE = re.compile(r"^:+\s*\*\*(.+?):\*\*\s*(.*)$")
WIKI_VOICE_QUOTE_RE = re.compile(r'^:+\s*[""](.+?)[""]\s*$')

# Character card id → names that may appear as speaker labels or on-stage.
# Intentionally omits Titans, titles, and places used as RAG aliases
# (Oronyx, Thanatos, Aquila, Kephale, Janus, Phagousa, Nikador, Kremnos,
# Deliverer, Empress, Trickery, Blasphemer, Rain of Sensation).
HEIR_NAMES: dict[str, tuple[str, ...]] = {
    "aglaea": ("Dux Goldweaver Aglaea", "Golden Nymph (Aglaea)", "Aglaea"),
    "anaxa": ("Bough of Rift, Anaxagoras", "Anaxagoras", "Anaxa"),
    "castorice": ("Castorice, Hand of Shadow", "Castorice"),
    "cerydra": ("Scale of Justice, Cerydra", "Dux Fatorum Cerydra", "Cerydra"),
    "cipher": ("Coin of Whimsy, Cifera", "Cipher (as Atticus)", "Cifera", "Cipher"),
    "cyrene": (
        "Mysterious Voice (Cyrene's Past Self)",
        "A Young Girl's Voice (Cyrene)",
        '"Seed of Memory" (the nascent Demiurge)',
        "Seed of Memory",
        "Demiurge",
        "Cyrene",
        "Mem",
    ),
    "dan-heng-permansor-terrae": (
        "Dan Heng • Permansor Terrae",
        "Dan Heng Permansor Terrae",
        "Permansor Terrae",
        "Dan Heng (Imbibitor Lunae)",
        "Pillar of Stone, Dan Heng",
        "Dan Heng, Pillar of Stone",
        "Terravox",
        "Dan Heng",
    ),
    "evernight": (
        "Veil of Evernight, March 7th",
        "March 7th, Veil of Evernight",
        "March 7th",
        "March 7",
        "Evernight",
    ),
    "hyacine": ("Hyacinthia", "Hyacine"),
    "hysilens": (
        "Chalice of Plenty, Helektra",
        "Helektra",
        "Hysilens",
    ),
    "mydei": ("Mydeimos, Lance of Fury", "Mydeimos", "Mydei"),
    "phainon": (
        "Throne of Worlds, Khaslana",
        "The Hero Within",
        "Hero Within",
        "Young Phainon",
        "Khaslana",
        "Phainon",
        "Snowy",
    ),
    "tribbie": (
        "Gate of Infinity, Tribios",
        "Gate of Infinity, Trianne",
        "Dux Fatorum Tribbie",
        "Tribios",
        "Trianne",
        "Trinnon",
        "Tribbie",
    ),
}

# Exact speaker labels that must never map to an Heir (Titans, memosprites, …).
REJECT_SPEAKERS = {
    "thanatos",
    "oronyx",
    "phagousa",
    "janus",
    "aquila",
    "nikador",
    "kephale",
    "kephale?",
    "seliose",
    "seliose the daythunder knight",
    "seliose, theos synthetos",
    "seliose's voice",
    "flame reaver",
    "memory's chorus",
    "flower of memory",
    "voice of memory",
    "sound of oronyx",
    "dolimem",
    "relimem",
    "miremem",
    "tisolimem",
    "tidolimem",
    "sosolimem",
    "memosnatcher",
    "terrified memosnatcher",
    "calm memosnatcher",
    "hesitant memosnatcher",
    "ichor memosprite",
    "memokeeper's embodiment",
    "gnaeus/nikador",
    "gnaeus",
    "nikador's corpse",
    "soldier of nikador",
    "gorgo, mydei's mother",
    "phainon's look-alike",
    "team phainon fairy",
    "team mydei fairy",
    "all fairies of the membrance maze",
    "enraged oronyx devotee",
    "lygus's memory",
    "lygus etched in memory",
    "cerces (memory)",
    "cerces",
    "memory solabis",
    "memory lunabis",
    "pilot's memory fragment",
    "hacker's memory fragment",
    "commander's memory fragment",
    "medic's memory fragment",
    '"bud of memory"',
    '"blossom of memory"',
    "bud of memory",
    "blossom of memory",
}

_SKIP_TITLE_RE = re.compile(
    r"(?ix)^(story\ recap|complete\ dialogue|steps|index|"
    r"structure|scope|rewards|overview|how this databank|"
    r"completion status|full chapter list|voice-over note|"
    r"key character interactions covered|end of chapter.*|"
    r".*summary$|open-world)$"
)
_MISSION_TITLE_RE = re.compile(r"(?ix)^((sub-)?mission\s+\d+|mission\s+\d+:)")
_QUICK_READ_RE = re.compile(r"(?ix)^quick\ read")

# Bare "March" is March 7th in this corpus (2 speaker hits); not the calendar month.
_EXTRA_EXACT = {
    "march": "evernight",
}

_NAME_INDEX: list[tuple[str, str]] = []
for _hid, _names in HEIR_NAMES.items():
    for _n in _names:
        _NAME_INDEX.append((_n.lower(), _hid))
_NAME_INDEX.sort(key=lambda kv: len(kv[0]), reverse=True)


def _norm_label(label: str) -> str:
    s = label.strip()
    s = s.strip('"“”')
    s = re.sub(r"\s+", " ", s)
    return s


def _norm_key(label: str) -> str:
    return _norm_label(label).lower()


def _word_in(name: str, text: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])", text, re.I) is not None


def _reject_possessive(text: str, name: str) -> bool:
    return re.search(
        rf"(?i){re.escape(name)}'s\s+(mother|father|corpse|look-alike|devotee)",
        text,
    ) is not None


def _talk_to_heading(line: str) -> str | None:
    m = TALK_TO_RE.match(line.strip())
    if m:
        return m.group(1).strip()
    return None


def is_heir_speaker_label(character_id: str, label: str) -> bool:
    return character_id in speaker_heirs(label)


def speaker_heirs(label: str) -> list[str]:
    """Return Heir card ids this speaker label belongs to (0, 1, or several)."""
    raw = _norm_label(label)
    if not raw:
        return []
    if _talk_to_heading(f"**({raw}):**") or raw.lower().startswith("talk to "):
        return []
    key = _norm_key(raw)
    if key in REJECT_SPEAKERS or key.strip('"') in REJECT_SPEAKERS:
        return []
    if key in _EXTRA_EXACT:
        return [_EXTRA_EXACT[key]]

    # ??? (Name) / ???(Name)
    m = re.match(r"^\?+\s*\((.+)\)$", raw)
    if m:
        return speaker_heirs(m.group(1))
    m = re.match(r"^(.+?)\s*\((.+)\)$", raw)
    # Keep both outer and parenthetical (e.g. Aglaea (through Tribbie)).
    pieces: list[str] = []
    if m and not raw.lower().startswith("trailblazer"):
        pieces.extend(re.split(r"\s*(?:&|,|\band\b)\s*", m.group(1), flags=re.I))
        pieces.extend(re.split(r"\s*(?:&|,|\band\b)\s*", m.group(2), flags=re.I))
    else:
        pieces = re.split(r"\s*(?:&|\band\b)\s*", raw, flags=re.I)
        # Comma-split only when it looks like a list of people, not "Name, Title"
        # — we still scan the whole phrase below.

    found: list[str] = []
    seen: set[str] = set()

    def add(hid: str) -> None:
        if hid not in seen:
            seen.add(hid)
            found.append(hid)

    def match_phrase(phrase: str) -> None:
        p = _norm_label(phrase)
        pk = _norm_key(p)
        if not p or pk in REJECT_SPEAKERS:
            return
        if pk in _EXTRA_EXACT:
            add(_EXTRA_EXACT[pk])
            return
        # Strip trailing punctuation / etched-in-memory / memory echoes.
        p_core = re.sub(
            r"(?i)\s*(etched in memory|\(memory\)|\(echo\)|\(appearing\)|"
            r"\(beyond death\)|\(imagination\)|\(\?\)|\?+|!+|\.{2,})\s*$",
            "",
            p,
        ).strip()
        pk_core = _norm_key(p_core)
        if pk_core in REJECT_SPEAKERS:
            return
        blob = pk_core
        for name, hid in _NAME_INDEX:
            if name == "mem":
                # Exact token only — never "memory", "dolimem", "memosnatcher".
                if re.search(r"(?<![a-z0-9])mem(?![a-z0-9])", blob) and "memory" not in blob:
                    if not _reject_possessive(blob, "mem"):
                        add(hid)
                continue
            hay = blob if _word_in(name, blob) else (pk if _word_in(name, pk) else "")
            if not hay:
                continue
            if _reject_possessive(blob, name) or _reject_possessive(pk, name):
                continue
            if re.search(rf"(?i)^team\s+{re.escape(name)}\s+fairy$", blob):
                continue
            add(hid)

        # "Name's Memory" (Hysilens's Memory) — the Heir's own echo.
        mmem = re.match(r"^(.+?)(?:'s)?\s+memory$", pk_core)
        if mmem:
            inner = speaker_heirs(mmem.group(1))
            for hid in inner:
                add(hid)

    for piece in pieces:
        match_phrase(piece)
    # Also match the unsplit label (Title, Name).
    if raw not in pieces:
        match_phrase(raw)
    return found


def speaker_of(line: str) -> str | None:
    m = SPEAKER_RE.match(line)
    if m:
        return m.group(1).strip()
    m = WIKI_SPEAKER_RE.match(line)
    if m:
        return m.group(1).strip()
    return None


def heirs_speaking_in_line(line: str) -> list[str]:
    sp = speaker_of(line)
    if not sp:
        return []
    return speaker_heirs(sp)


_STAGE_RE = re.compile(r"\*(.+?)\*")


def heirs_in_stage_directions(lines: list[str]) -> dict[str, str]:
    """Heir ids mentioned as actors in italic/cutscene lines (not dialogue)."""
    present: dict[str, str] = {}
    for line in lines:
        if speaker_of(line):
            continue
        if _talk_to_heading(line):
            # "Talk to Aglaea" means the visitor talks to her — she is present.
            target = _talk_to_heading(line)
            for hid in speaker_heirs(target or ""):
                present.setdefault(hid, "addressed")
            continue
        blobs = _STAGE_RE.findall(line)
        if not blobs and line.strip().startswith("(") and "Talk to" not in line:
            blobs = [line]
        text = " ".join(blobs) if blobs else ""
        if not text:
            continue
        # Scan whole-word primary names only (skip Snowy — too informal for
        # stage-direction presence; speaker labels still catch it).
        for hid, names in HEIR_NAMES.items():
            for name in names:
                if name.lower() in {"snowy", "mem"} and name.lower() == "snowy":
                    continue
                if name.lower() == "mem":
                    if re.search(r"(?<![a-z0-9])Mem(?![a-z0-9])", text) and "memory" not in text.lower():
                        present.setdefault(hid, "on-stage")
                    continue
                if _word_in(name, text) and not _reject_possessive(text.lower(), name.lower()):
                    present.setdefault(hid, "on-stage")
                    break
    return present


def heirs_in_unit(lines: list[str]) -> dict[str, str]:
    """id → role (spoke / addressed / on-stage). Spoke wins."""
    roles: dict[str, str] = {}
    for line in lines:
        for hid in heirs_speaking_in_line(line):
            roles[hid] = "spoke"
    for hid, role in heirs_in_stage_directions(lines).items():
        roles.setdefault(hid, role)
    return roles


def is_skip_title(title: str) -> bool:
    t = title.strip()
    if _SKIP_TITLE_RE.match(t):
        return True
    if re.search(r"(?i)mission\s+\d+\s+summary", t):
        return True
    if re.search(r"(?i)^end of chapter", t):
        return True
    return False


def is_container_title(title: str, level: int, rel_posix: str) -> bool:
    t = title.strip()
    if re.match(r"(?i)^complete dialogue$", t):
        return True
    # Adventure ### Dialogue is a wrapper; wiki #### Dialogue is the scene itself.
    if re.match(r"(?i)^dialogue$", t) and level <= 3:
        return True
    if _MISSION_TITLE_RE.match(t) and "summary" not in t.lower():
        return True
    if level == 1:
        return True
    if "/adventure/" in rel_posix and level == 2:
        return True
    if "wiki/" in rel_posix and level <= 2:
        return True
    return False


@dataclass
class DialogueUnit:
    source_rel: str
    heading: str
    title: str
    start_line: int  # 1-indexed, inclusive (first body line)
    end_line: int  # 1-indexed, inclusive
    lines: list[str]
    heirs: dict[str, str] = field(default_factory=dict)
    unit_id: str = ""

    @property
    def kind(self) -> str:
        n = len(self.heirs)
        if n == 0:
            return "none"
        if n == 1:
            return "personal"
        return "collective"

    @property
    def speaker_lines(self) -> list[str]:
        return [ln for ln in self.lines if speaker_of(ln)]


def _slug(text: str, max_len: int = 72) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower())
    s = s.strip("-")[:max_len].strip("-")
    return s or "untitled"


def preprocess_wiki_dialogue(text: str, default_speaker: str) -> str:
    """Normalize wiki /Dialogue markup to **Speaker:** lines. Does not invent words."""
    out: list[str] = []
    in_voice = False
    for raw in text.splitlines():
        if HEADER_RE.match(raw):
            in_voice = "voice line" in raw.lower()
            out.append(raw)
            continue
        m = WIKI_SPEAKER_RE.match(raw)
        if m:
            out.append(f"**{m.group(1).strip()}:** {m.group(2)}")
            continue
        m = WIKI_VOICE_QUOTE_RE.match(raw)
        if m and in_voice:
            out.append(f"**{default_speaker}:** {m.group(1)}")
            continue
        out.append(raw)
    return "\n".join(out) + "\n"


def _split_talk_to(heading: str, start_line: int, chunk: list[tuple[int, str]]) -> list[tuple[str, int, int, list[str]]]:
    """Split a heading body on (Talk to X) markers. Line numbers are 1-indexed."""
    if not chunk:
        return []
    groups: list[tuple[str, list[tuple[int, str]]]] = []
    current_title = heading
    current: list[tuple[int, str]] = []
    for ln, text in chunk:
        who = _talk_to_heading(text)
        if who:
            if current:
                groups.append((current_title, current))
            current_title = f"{heading} > Talk to {who}"
            current = [(ln, text)]
        else:
            current.append((ln, text))
    if current:
        groups.append((current_title, current))
    result = []
    for title, items in groups:
        lines = [t for _, t in items]
        # Drop trailing empty lines for stability; keep internal blanks.
        while lines and lines[-1].strip() == "":
            items = items[:-1]
            lines = [t for _, t in items]
        while lines and lines[0].strip() == "":
            items = items[1:]
            lines = [t for _, t in items]
        if not items:
            continue
        result.append((title, items[0][0], items[-1][0], lines))
    return result


def iter_source_units(path: Path, root: Path) -> Iterable[DialogueUnit]:
    rel = path.relative_to(root).as_posix()
    raw = path.read_text(encoding="utf-8")
    if "wiki/" in rel and path.name.endswith("-dialogue.md"):
        speaker = "Tribbie" if "tribbie" in path.name.lower() else "Unknown"
        raw = preprocess_wiki_dialogue(raw, speaker)
    lines = raw.splitlines()
    # Collect headings: (line_index_0, level, title)
    heads: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        m = HEADER_RE.match(line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    units: list[DialogueUnit] = []
    for idx, (i, level, title) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        # Direct content: until first descendant heading.
        direct_end = end
        for j, lev, _ in heads[idx + 1 :]:
            if lev <= level:
                break
            if lev > level:
                direct_end = j
                break
        if is_skip_title(title):
            continue
        if is_container_title(title, level, rel):
            # Preamble dialogue before the first child heading.
            body = [(n + 1, lines[n]) for n in range(i + 1, direct_end)]
            heading_stack = _heading_stack(heads, idx)
            for sub_title, a, b, body_lines in _split_talk_to(
                " > ".join(heading_stack + ([title] if title not in heading_stack else [])),
                i + 2,
                body,
            ):
                if not any(speaker_of(x) for x in body_lines) and not any(
                    _talk_to_heading(x) for x in body_lines
                ):
                    continue
                units.append(
                    DialogueUnit(
                        source_rel=rel,
                        heading=sub_title,
                        title=title,
                        start_line=a,
                        end_line=b,
                        lines=body_lines,
                    )
                )
            continue
        heading_stack = _heading_stack(heads, idx)
        body = [(n + 1, lines[n]) for n in range(i + 1, direct_end)]
        full_heading = " > ".join(heading_stack)
        for sub_title, a, b, body_lines in _split_talk_to(full_heading, i + 2, body):
            units.append(
                DialogueUnit(
                    source_rel=rel,
                    heading=sub_title,
                    title=title,
                    start_line=a,
                    end_line=b,
                    lines=body_lines,
                )
            )
    used_ids: dict[str, int] = {}
    for u in units:
        u.heirs = heirs_in_unit(u.lines)
        stem = Path(u.source_rel).stem
        base = f"{stem}__{_slug(u.title)}"
        used_ids[base] = used_ids.get(base, 0) + 1
        n = used_ids[base]
        u.unit_id = base if n == 1 else f"{base}-{n}"
        yield u


def _heading_stack(heads: list[tuple[int, int, str]], idx: int) -> list[str]:
    stack: list[tuple[int, str]] = []
    for j in range(idx + 1):
        _, lev, title = heads[j]
        if is_skip_title(title) or re.match(r"(?i)^complete dialogue$", title):
            continue
        while stack and stack[-1][0] >= lev:
            stack.pop()
        stack.append((lev, title))
    return [t for _, t in stack]


def excerpt_for_heir(lines: list[str], heir_id: str) -> list[str]:
    """What this Heir would remember from a shared scene (not the whole crowd)."""
    speech_idx = [i for i, ln in enumerate(lines) if heir_id in heirs_speaking_in_line(ln)]
    if speech_idx:
        lo = speech_idx[0]
        seen = 0
        j = lo - 1
        while j >= 0 and seen < 2:
            if speaker_of(lines[j]):
                seen += 1
                lo = j
            elif lines[j].strip() and not speaker_of(lines[j]):
                lo = j
            j -= 1
        hi = speech_idx[-1]
        seen = 0
        j = hi + 1
        while j < len(lines) and seen < 1:
            if speaker_of(lines[j]):
                seen += 1
                hi = j
            elif lines[j].strip():
                hi = j
            j += 1
        chunk = lines[lo : hi + 1]
        # Drop leading/trailing blanks.
        while chunk and chunk[0].strip() == "":
            chunk = chunk[1:]
        while chunk and chunk[-1].strip() == "":
            chunk = chunk[:-1]
        return chunk
    # Silent extra: only stage/talk-to lines that mark them present.
    kept = []
    for ln in lines:
        if _talk_to_heading(ln) and heir_id in speaker_heirs(_talk_to_heading(ln) or ""):
            kept.append(ln)
            continue
        if speaker_of(ln):
            continue
        stage = heirs_in_stage_directions([ln])
        if heir_id in stage:
            kept.append(ln)
    return kept


CANON_SOURCE_GLOBS = [
    "databank/missions/chapter-*.md",
    "databank/missions/adventure/v*.md",
    "databank/wiki/lore/tribbie-dialogue.md",
]

SKIP_SOURCES = [
    ("databank/missions/INDEX.md", "index / meta — no dialogue units"),
    ("databank/missions/adventure/INDEX.md", "index / meta — no dialogue units"),
    ("databank/missions/key-character-moments.md", "cross-chapter paraphrase, not verbatim dialogue"),
    ("databank/missions/_cache/", "wiki dump cache; duplicates chapter files"),
    ("databank/missions/build_ch2.py", "build script, not dialogue"),
    ("databank/missions/build_ch2_final.py", "build script, not dialogue"),
    ("databank/missions/process_ch2.py", "build script, not dialogue"),
    ("databank/missions/clean_wiki.py", "build script, not dialogue"),
    ("databank/experiment/", "operator experiment docs — not Heir memory fuel"),
]


def list_canon_sources(project_root: Path) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in CANON_SOURCE_GLOBS:
        for path in sorted(project_root.glob(pattern)):
            if path.is_file() and path.suffix.lower() == ".md" and path not in seen:
                seen.add(path)
                files.append(path)
    return files


def collect_all_units(project_root: Path) -> list[DialogueUnit]:
    units: list[DialogueUnit] = []
    for path in list_canon_sources(project_root):
        units.extend(iter_source_units(path, project_root))
    return units
