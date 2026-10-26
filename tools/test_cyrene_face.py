# -*- coding: utf-8 -*-
"""Cyrene's year cycle, wired — no LLM, no GPU.

    python tools/test_cyrene_face.py

Checks the binding, not the calendar (that is `tools/test_cyrene_cycle.py`):
three faces exist on disk, the register reaches `manager.chat` for Cyrene only,
and Mem never becomes a speaker.
"""
from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world import cyrene_cycle as cycle  # noqa: E402
from src.world import cyrene_face  # noqa: E402

PASSED, FAILED = [], []


def check(name: str, cond: object, extra: str = "") -> None:
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}{('  ' + extra) if extra else ''}")


class FakeManager:
    """Records the kwargs each call was made with."""

    def __init__(self):
        self.calls = []

    def chat(self, character_id, user_message, **kw):
        self.calls.append((character_id, user_message, kw))
        return f"{character_id} answers"


def main() -> int:
    print("== The three faces ==")
    for form in cycle.FACES:
        path = cyrene_face.face_path(form)
        check(f"{form} has a still", path is not None and path.is_file(),
              str(path))
    check("an unknown form falls back", cyrene_face.face_path("nonsense") is None)
    check("every month resolves to a face", all(
        cyrene_face.face_path(cycle.slot_for_month(m).visual_face) is not None
        for m in range(0, 14)))

    print("== The register ==")
    for persona in (cycle.PERSONA_CHILDHOOD, cycle.PERSONA_DEMIURGE):
        hint = cyrene_face.register_for(persona)
        check(f"{persona} has a hint", len(hint) > 40)
        check(f"{persona} hint forbids announcing itself", "announce" in hint.lower())
        check(f"{persona} hint never claims another person",
              "you are mem" not in hint.lower() and "model" not in hint.lower())
    check("no persona, no hint", cyrene_face.register_for("") == "")

    print("== Only Cyrene is addressed ==")
    demi = cycle.slot_for_month(9)      # Weaving → Page / Demiurge
    mem = cycle.slot_for_month(0)       # Uncounted → Fairy / Mem picture
    check("demiurge months hint", cyrene_face.speak_hint("cyrene", demi) != "")
    check("fairy keeps the childhood register",
          "girl who writes" in cyrene_face.speak_hint("cyrene", mem))
    check("another Heir gets nothing", cyrene_face.speak_hint("mydei", demi) == "")
    check("mem is never a speaker id", cycle.slot_for_month(0).talk_target == "cyrene")

    print("== It reaches manager.chat ==")
    from src.ui_eternal_page import _speak_with_register

    mgr = FakeManager()
    speak = _speak_with_register(mgr, demi)
    speak("cyrene", "hello")
    speak("mydei", "hello")
    cy_call, my_call = mgr.calls[0], mgr.calls[1]
    check("cyrene's call carries extra_system", "extra_system" in cy_call[2])
    check("the hint is the demiurge register",
          cy_call[2].get("extra_system") == cyrene_face.register_for("demiurge"))
    check("another Heir's call carries none", not my_call[2])
    check("both still speak through manager.chat",
          cy_call[0] == "cyrene" and my_call[0] == "mydei")

    sig = inspect.signature(__import__("src.core.agent_manager", fromlist=["AgentManager"])
                            .AgentManager.chat)
    check("AgentManager.chat accepts extra_system", "extra_system" in sig.parameters)
    check("extra_system defaults to empty",
          sig.parameters["extra_system"].default == "")

    print("== The suite's own guard ==")
    src = (ROOT / "src" / "world" / "cyrene_face.py").read_text(encoding="utf-8")
    check("no Streamlit in the binding", "streamlit" not in src)
    check("no network in the binding", not any(
        t in src for t in ("requests", "urllib", "http.client")))

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
