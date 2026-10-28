# -*- coding: utf-8 -*-
"""Offline checks for keyed lorebook activation. No GPU, no network."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.knowledge.lorebook import Entry, Lorebook, from_dicts, from_markdown  # noqa: E402

PASSED, FAILED = [], []


def check(name, cond, detail=""):
    (PASSED if cond else FAILED).append(name if cond else f"{name}  [{detail}]")


def main() -> int:
    book = from_dicts([
        {"keys": ["kremnos"], "title": "Kremnos", "text": "A fortress city of Strife.", "priority": 2},
        {"keys": ["okhema"], "title": "Okhema", "text": "The holy city.", "priority": 1},
        {"keys": ["gorgo"], "title": "Gorgo", "text": "The king who cast him out.", "priority": 3},
    ])
    check("entries loaded", len(book) == 3, str(len(book)))

    hit = book.activate("What did Gorgo do at Kremnos?")
    check("a key fires its entry", any(e.title == "Kremnos" for e in hit))
    check("a second key fires its own entry", any(e.title == "Gorgo" for e in hit))
    check("an absent key stays silent", all(e.title != "Okhema" for e in hit))
    check("priority orders the block", hit[0].title == "Gorgo", hit[0].title)

    check("no keys means nothing is pinned", book.activate("the weather is mild") == [])
    check("empty text is harmless", book.activate("") == [])

    short = Lorebook([Entry(keys=["ok"], text="tiny")])
    check("a short key does not fire inside a word", short.activate("Okhema is holy") == [])
    check("a short key fires on its own word", short.activate("ok then") != [])

    cold = Lorebook([Entry(keys=["okhema"], text="x", cooldown_turns=3)])
    check("first activation fires", cold.activate("okhema", turn=1) != [])
    check("cooldown suppresses the repeat", cold.activate("okhema", turn=2) == [])
    check("cooldown expires", cold.activate("okhema", turn=5) != [])

    sticky = Lorebook([Entry(keys=["okhema"], text="x", sticky_turns=2)])
    sticky.activate("okhema", turn=1)
    check("a sticky entry holds its window", sticky.activate("okhema", turn=2) != [])

    text = book.pinned_text("Gorgo and Kremnos")
    check("the pinned block is labelled", "## Gorgo" in text, text[:40])
    check("the pinned block carries the text", "cast him out" in text)

    prof = ROOT / "databank" / "chrysos-heirs" / "mydei.md"
    md = from_markdown(prof)
    check("a profile becomes entries", len(md) >= 3, str(len(md)))
    got = md.activate("Mydei, what is your Coreflame?")
    check("a profile section answers its question",
          any("Coreflame" in e.title for e in got), sed(got))

    test_wiring()

    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    for f in FAILED:
        print("  FAIL", f)
    return 1 if FAILED else 0


def sed(entries):
    return str([e.title for e in entries])


def test_wiring():
    print("== wiring: pinned entries lead retrieval ==")
    from src.core.context_builder import ContextBuilder

    class FakeStore:
        def query(self, cid, q, k=5, threshold=0.7):
            return [{"text": "Okhema is the holy city.", "kind": "profile",
                     "source": "vector", "score": 0.9}]

    cb = ContextBuilder(vector_store=FakeStore())
    hits = cb.retrieve("mydei", "What is your Coreflame?")
    check("a pinned entry is returned", any(h["kind"] == "lorebook" for h in hits),
          str([h["kind"] for h in hits]))
    check("it comes before the vector hit", hits[0]["kind"] == "lorebook",
          str([h["kind"] for h in hits]))
    check("the vector hit is still there", any(h["kind"] == "profile" for h in hits))
    check("an unrelated question pins nothing",
          all(h["kind"] != "lorebook" for h in cb.retrieve("mydei", "the weather is mild")))
    check("the budget is respected", len(cb.retrieve("mydei", "Coreflame and biography")) <= cb.k)
    import os
    os.environ["AMP_LOREBOOK"] = "0"
    cb2 = ContextBuilder(vector_store=FakeStore())
    check("the switch turns it off",
          all(h["kind"] != "lorebook" for h in cb2.retrieve("mydei", "What is your Coreflame?")))
    os.environ.pop("AMP_LOREBOOK", None)


if __name__ == "__main__":
    raise SystemExit(main())
