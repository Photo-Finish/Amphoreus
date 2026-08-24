# -*- coding: utf-8 -*-
"""Unit checks for visitor emotion (no torch required for lexicon path).

    python tools/test_visitor_emotion.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {detail}")


def main() -> int:
    from src.core import visitor_emotion as ve

    print("== toggle ==")
    # Isolate from operator runtime file for this process
    ve.RUNTIME_PATH = ROOT / "world_runtime" / "_test_visitor_emotion.json"
    if ve.RUNTIME_PATH.is_file():
        ve.RUNTIME_PATH.unlink()
    check("default enabled", ve.emotion_enabled() is True)
    ve.set_emotion_enabled(False)
    check("set off", ve.emotion_enabled() is False)
    ve.set_emotion_enabled(True)
    check("set on", ve.emotion_enabled() is True)

    print("== lexicon classify ==")
    # Force lexicon by disabling pipeline for these checks
    ve._pipe = None
    ve._pipe_failed = True
    joy = ve.classify("I am so happy and grateful — thank you!")
    check("joy lexicon", joy["label"] == "joy", str(joy))
    sad = ve.classify("I feel so sad and lonely today")
    check("sadness lexicon", sad["label"] == "sadness", str(sad))
    empty = ve.classify("   ")
    check("empty is neutral", empty["label"] == "neutral", str(empty))

    print("== prompt block (wall-safe) ==")
    block = ve.visitor_emotion_block("I am furious and angry at this!", force=True)
    check("block non-empty", bool(block.strip()), block[:80])
    check("no BERT jargon", "BERT" not in block and "model" not in block.lower())
    check("no Earth psych", "psychology" not in block.lower() and "diagnosis" in block)
    check("has visitor header", "# How the visitor seems" in block)
    off = ve.visitor_emotion_block("I am furious!", force=False)
    check("force off empty", off == "")

    inj = ve.maybe_inject("SYSTEM", "I love this place!", force=True)
    check("maybe_inject appends", inj.startswith("SYSTEM") and "# How the visitor seems" in inj)

    # Cleanup test runtime
    try:
        if ve.RUNTIME_PATH.is_file():
            ve.RUNTIME_PATH.unlink()
    except Exception:
        pass

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
