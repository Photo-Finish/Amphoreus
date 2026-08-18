"""
Shape Amphoreus OPLoRA SFT data from databank copies only.

- Never modifies files under databank/ (or Heir folders).
- Duplicates selected sources into tools/oplora/work_copies/
- Parses dialogue on those copies into tools/oplora/datasets/*.jsonl

Charter: voice-stability rows use the Heirs' own spoken lines.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DATABANK = REPO_ROOT / "databank"
WORK = Path(__file__).resolve().parent / "work_copies"
DATASETS = Path(__file__).resolve().parent / "datasets"

# The 13 sanctuary cards in src/characters/ (plus optional extras like Terravox).
HEIR_ALIASES: Dict[str, List[str]] = {
    "Phainon": ["Phainon", "Khaslana", "Snowy"],
    "Mydei": ["Mydei", "Mydeimos"],
    "Aglaea": ["Aglaea"],
    "Tribbie": ["Tribbie", "Trianne", "Trinnon", "Tribios"],
    "Castorice": ["Castorice"],
    "Anaxa": ["Anaxa", "Anaxagoras"],
    "Hyacine": ["Hyacine"],
    "Cipher": ["Cipher", "Cifera"],
    "Hysilens": ["Hysilens"],
    "Cerydra": ["Cerydra"],
    "Cyrene": ["Cyrene"],
    "Evernight": ["Evernight"],
    "Dan Heng": ["Dan Heng", "Dan Heng • Permansor Terrae"],
    # Extra (not one of the 13 cards) — kept if lines appear in missions
    "Terravox": ["Terravox"],
}

# Official training roster = 13 character cards
TRAINING_HEIRS: Tuple[str, ...] = (
    "Aglaea",
    "Anaxa",
    "Castorice",
    "Cerydra",
    "Cipher",
    "Cyrene",
    "Dan Heng",
    "Evernight",
    "Hyacine",
    "Hysilens",
    "Mydei",
    "Phainon",
    "Tribbie",
)

# Sources relative to databank/ that we duplicate (read-only originals).
COPY_GLOBS: Sequence[str] = (
    "missions/*.md",
    "missions/adventure/*.md",
    "missions/_cache/*.md",
    "world/*.md",
    "chrysos-heirs/*.md",
)

SKIP_NAME_PARTS = (
    "INDEX.MD",
    "CLEAN_WIKI",
    "BUILD_",
    "PROCESS_",
)

# **Phainon:** / **"Evernight":** / **??? (Phainon):**
_SPEAKER = re.compile(
    r"^(?P<indent>>+\s*)?(?:\*\*)?(?P<speaker>"
    r'\?\?\?\s*\([^)]+\)|'
    r'"[^"]{1,48}"|'
    r"'[^']{1,48}'|"
    r"[A-Za-z][A-Za-z0-9 ·•'\-]{0,48}"
    r")(?:\*\*)?\s*[:：]\s*(?P<line>.+)$"
)
_PAREN_HEIR = re.compile(r"\((?P<inner>[^)]+)\)")
_QUOTED = re.compile(r'"([^"\n]{12,400})"')


@dataclass
class Row:
    heir: str
    source: str
    instruction: str
    input: str
    output: str
    kind: str  # dialogue | quote


def _canonical_heir(speaker: str) -> Optional[str]:
    s = speaker.strip().strip('"').strip("'")
    m = _PAREN_HEIR.search(s)
    if m:
        s = m.group("inner").strip().strip('"').strip("'")
    for canon, aliases in HEIR_ALIASES.items():
        for a in aliases:
            if s.lower() == a.lower():
                return canon
            if s.lower().startswith(a.lower() + " ") or s.lower().startswith(a.lower() + "'"):
                return canon
    return None


def _should_skip(path: Path) -> bool:
    name = path.name.upper()
    if name.startswith("_") and "CACHE" not in str(path).upper():
        # keep missions/_cache copies; skip other underscore junk at file level if needed
        pass
    for part in SKIP_NAME_PARTS:
        if part in name:
            return True
    if path.suffix.lower() != ".md":
        return True
    return False


def gather_sources() -> List[Path]:
    found: List[Path] = []
    for pattern in COPY_GLOBS:
        for path in sorted(DATABANK.glob(pattern)):
            if path.is_file() and not _should_skip(path):
                found.append(path)
    # Always include key-character-moments if present
    kcm = DATABANK / "missions" / "key-character-moments.md"
    if kcm.is_file() and kcm not in found:
        found.append(kcm)
    return found


def duplicate_sources(sources: Sequence[Path], work_root: Path, clean: bool) -> List[Path]:
    if clean and work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    copies: List[Path] = []
    for src in sources:
        rel = src.relative_to(DATABANK)
        dest = work_root / "databank" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copies.append(dest)
    return copies


def extract_dialogue(text: str, source: str, heir_filter: Optional[str]) -> List[Row]:
    rows: List[Row] = []
    context: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _SPEAKER.match(line)
        if not m:
            # Keep light narrative crumbs for context (not as outputs)
            cleaned = re.sub(r"[>*_\-]+", " ", line).strip()
            if 20 < len(cleaned) < 240 and not cleaned.startswith("("):
                context.append(cleaned)
                context = context[-4:]
            continue
        heir = _canonical_heir(m.group("speaker"))
        spoken = m.group("line").strip().strip('"').strip("'")
        spoken = re.sub(r"^\*+|\*+$", "", spoken).strip()
        if heir is None:
            label = m.group("speaker").strip()
            context.append(f"{label}: {spoken[:180]}")
            context = context[-4:]
            continue
        if heir_filter and heir.lower() != heir_filter.lower():
            context.append(f"{heir}: {spoken[:180]}")
            context = context[-4:]
            continue
        if len(spoken) < 8:
            continue
        # Skip player-choice stubs that somehow got attributed
        if spoken.startswith("*") and spoken.endswith("*"):
            continue
        ctx = " | ".join(context[-3:]) if context else "(scene open)"
        rows.append(
            Row(
                heir=heir,
                source=source,
                instruction=(
                    f"You are {heir}, a Chrysos Heir of Amphoreus. "
                    "Answer in character in one spoken reply. "
                    "Do not break character or invent out-of-setting knowledge."
                ),
                input=ctx,
                output=spoken,
                kind="dialogue",
            )
        )
        context.append(f"{heir}: {spoken[:180]}")
        context = context[-4:]
    return rows


def extract_quoted_moments(text: str, source: str, heir_filter: Optional[str]) -> List[Row]:
    """Pull \"quoted Heir lines\" under ## Heir sections in key-character-moments."""
    rows: List[Row] = []
    current: Optional[str] = None
    for raw in text.splitlines():
        line = raw.strip()
        hm = re.match(r"^##\s+(.+?)(?:\s*—|\s*$)", line)
        if hm:
            current = _canonical_heir(hm.group(1).split("(")[0].strip())
            continue
        if current is None:
            continue
        if heir_filter and current.lower() != heir_filter.lower():
            continue
        for q in _QUOTED.findall(line):
            q = q.strip()
            if len(q) < 12:
                continue
            rows.append(
                Row(
                    heir=current,
                    source=source,
                    instruction=(
                        f"You are {current}, a Chrysos Heir of Amphoreus. "
                        "Speak a short in-character line that fits your voice."
                    ),
                    input="(voice exemplar from key character moments)",
                    output=q,
                    kind="quote",
                )
            )
    return rows


def rows_to_dicts(rows: Sequence[Row]) -> List[dict]:
    out: List[dict] = []
    seen = set()
    for r in rows:
        key = (r.heir, r.output)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "heir": r.heir,
                "source": r.source,
                "kind": r.kind,
                "instruction": r.instruction,
                "input": r.input,
                "output": r.output,
            }
        )
    return out


def write_jsonl(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--heir", default="all", help="Heir filter or 'all'")
    ap.add_argument("--clean", action="store_true", help="Wipe work_copies before copy")
    ap.add_argument("--max-per-heir", type=int, default=0, help="0 = no cap")
    args = ap.parse_args()

    if not DATABANK.is_dir():
        raise SystemExit(f"Missing databank at {DATABANK}")

    sources = gather_sources()
    print(f"Duplicating {len(sources)} databank files → {WORK}")
    copies = duplicate_sources(sources, WORK, clean=args.clean)
    print(f"Copied {len(copies)} files (originals untouched).")

    heir_filter = None if args.heir.lower() == "all" else args.heir
    all_rows: List[Row] = []
    for copy in copies:
        rel = str(copy.relative_to(WORK)).replace("\\", "/")
        text = copy.read_text(encoding="utf-8", errors="replace")
        all_rows.extend(extract_dialogue(text, rel, heir_filter))
        if copy.name == "key-character-moments.md":
            all_rows.extend(extract_quoted_moments(text, rel, heir_filter))

    dict_rows = rows_to_dicts(all_rows)

    # Optional per-heir caps (keep order: dialogue first already)
    if args.max_per_heir and args.max_per_heir > 0:
        counts: Counter = Counter()
        capped: List[dict] = []
        for row in dict_rows:
            if counts[row["heir"]] >= args.max_per_heir:
                continue
            capped.append(row)
            counts[row["heir"]] += 1
        dict_rows = capped

    DATASETS.mkdir(parents=True, exist_ok=True)
    all_path = DATASETS / "heirs_all.jsonl"
    write_jsonl(all_path, dict_rows)

    by_heir: Dict[str, List[dict]] = {}
    for row in dict_rows:
        by_heir.setdefault(row["heir"], []).append(row)
    for heir, rows in sorted(by_heir.items()):
        safe = heir.lower().replace(" ", "_")
        write_jsonl(DATASETS / f"heir_{safe}.jsonl", rows)

    training_13 = {h: len(by_heir.get(h, [])) for h in TRAINING_HEIRS}
    missing_13 = [h for h, n in training_13.items() if n == 0]
    manifest = {
        "source_policy": "duplicates only; databank originals never modified",
        "work_copies": str(WORK.relative_to(REPO_ROOT)).replace("\\", "/"),
        "files_copied": len(copies),
        "total_rows": len(dict_rows),
        "training_heirs_13": TRAINING_HEIRS,
        "training_13_counts": training_13,
        "training_13_missing": missing_13,
        "training_13_total": sum(training_13.values()),
        "per_heir": {h: len(r) for h, r in sorted(by_heir.items())},
        "kinds": dict(Counter(r["kind"] for r in dict_rows)),
    }
    # Convenience combined file for the official 13 only
    rows_13 = [r for r in dict_rows if r["heir"] in TRAINING_HEIRS]
    write_jsonl(DATASETS / "heirs_training_13.jsonl", rows_13)
    (DATASETS / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"Wrote datasets under {DATASETS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
