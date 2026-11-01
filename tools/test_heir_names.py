# -*- coding: utf-8 -*-
"""Every Heir's name must be the name canon uses, and no two may be confusable.

    python tools/test_heir_names.py

This exists because I once wrote **"Eternight"** in a report when the Heir is
**Evernight**. The repository was clean — 0 misspellings, 3 844 correct — but a
project whose whole argument is fidelity should be able to prove that, not be
believed about it. So the roster is checked against the databank:

  * every id has a profile, and the roster name is canon's Playable Name (the first
    segment, for names like "Dan Heng • Permansor Terrae");
  * no two names are identical or within one edit of each other, which is how
    "Eternight"/"Evernight" would slip through a list;
  * the name actually appears in that Heir's own profile.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.world import eternal_page as ep  # noqa: E402

BANK = ROOT / "databank" / "chrysos-heirs"
PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASSED if cond else FAILED).append(name if cond else f"{name}  [{detail}]")


def playable_name(cid: str) -> str:
    p = BANK / f"{cid}.md"
    if not p.is_file():
        return ""
    m = re.search(r"\*\*Playable Name:\*\*\s*(.+)", p.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else ""


def primary(name: str) -> str:
    """'Dan Heng • Permansor Terrae' -> 'Dan Heng'; 'Anaxa (Anaxagoras)' -> 'Anaxa'."""
    return re.split(r"[•(]", name)[0].strip()


def edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main() -> int:
    ids = ep.all_ids()
    check("the roster has thirteen Heirs", len(ids) == 13, str(len(ids)))

    names: dict[str, str] = {}
    for cid in ids:
        canon = playable_name(cid)
        check(f"{cid}: has a databank profile", bool(canon), "no profile" if not canon else "")
        if not canon:
            continue
        roster = ep.short_name(cid)
        want = primary(canon)
        check(f"{cid}: roster name is canon's ({want!r})", roster == want,
              f"roster {roster!r} vs canon {want!r}")
        names[cid] = roster
        profile = (BANK / f"{cid}.md").read_text(encoding="utf-8")
        check(f"{cid}: the name appears in its own profile", want in profile)

    # Uniqueness, and no near-miss pair: a list containing both "Evernight" and
    # "Eternight" would pass a naive equality test but is plainly wrong.
    check("no two Heirs share a name", len(set(names.values())) == len(names),
          str(sorted(names.values())))
    close = []
    items = list(names.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            d = edit_distance(items[i][1].lower(), items[j][1].lower())
            if d <= 1:
                close.append(f"{items[i][1]}~{items[j][1]} (distance {d})")
    check("no two Heirs have confusable names", not close, "; ".join(close))

    # Self-test: the rule must actually catch the mistake that prompted it.
    check("the guard recognises 'Eternight' as a near-miss of 'Evernight'",
          edit_distance("evernight", "eternight") == 1)
    check("the guard treats 'Evernight' and 'Evernight' as identical",
          edit_distance("evernight", "evernight") == 0)
    check("unrelated names are not flagged",
          edit_distance("aglaea", "castorice") > 1)

    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    for f in FAILED:
        print("  FAIL", f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
