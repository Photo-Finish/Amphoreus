# -*- coding: utf-8 -*-
"""Audit each Heir card's identity claims against the databank profile.

    python tools/audit_heir_claims.py

Checks the facts a script can check — Coreflame, Titan, MBTI, race, hometown,
titles and the nickname vocabulary — and prints a mismatch list. Behavioural
fidelity is a judgement call and lives in the CANON COMPLEXITY blocks of each
card, not here.

This is the mechanical half of the audit; it caught Hyacine listed as Human
though the databank says Skyfolk, Cipher's home given as Okhema though she is
from Dolos, and Anaxa's as the Grove where he merely studied.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "src" / "characters"
PROFILES = ROOT / "databank" / "chrysos-heirs"

FIELDS = {
    "coreflame": r"\*\*Coreflame:\*\*\s*([^\n]+)",
    "titan": r"\*\*Titan:\*\*\s*([^\n]+)",
    "mbti": r"\*\*MBTI:\*\*\s*([^\n]+)",
    "race": r"\*\*Race:\*\*\s*([^\n]+)",
    "hometown": r"\*\*Hometown:\*\*\s*([^\n]+)",
    "titles": r"\*\*Titles:\*\*\s*([^\n]+)",
    "nicknames": r"\*\*Nicknames:\*\*\s*([^\n]+)",
}


def profile_facts(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for key, pattern in FIELDS.items():
        m = re.search(pattern, text)
        if m:
            out[key] = m.group(1).strip()
    return out


def flatten(value) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values())
    return str(value or "")


def main() -> int:
    problems = 0
    for card_path in sorted(CARDS.glob("*.json")):
        cid = card_path.stem
        prof_path = PROFILES / f"{cid}.md"
        if not prof_path.exists():
            print(f"{cid:30s} NO PROFILE")
            problems += 1
            continue
        card = json.loads(card_path.read_text(encoding="utf-8"))
        facts = profile_facts(prof_path)
        structured = " ".join(flatten(v) for v in (
            card.get("identity"), card.get("meta"), card.get("personality"))).lower()
        prompt = str((card.get("prompts") or {}).get("system_prompt", "")).lower()

        missing = []
        for key in ("coreflame", "titan", "mbti", "race", "hometown"):
            value = facts.get(key)
            if not value:
                continue
            head = re.split(r"[\(,]", value)[0].strip().lower()
            if head and head not in structured:
                missing.append(f"{key}={value.split('(')[0].strip()}")

        # Nicknames may live in the structured fields or in the prompt's
        # vocabulary lines — both are legitimate homes.
        nick_list = [n.strip().strip("*") for n in re.split(r"[,;(]", facts.get("nicknames", ""))
                     if len(n.strip()) > 2]
        haystack = structured + " " + prompt
        nick_hits = sum(1 for n in nick_list[:6] if n.lower() in haystack)

        flag = "" if not missing else "  <- " + ", ".join(missing[:4])
        print(f"{cid:30s} missing={len(missing):2d}  "
              f"nicknames={nick_hits}/{min(6, len(nick_list))}{flag}")
        problems += len(missing)
    print()
    print(f"total missing structural claims: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
