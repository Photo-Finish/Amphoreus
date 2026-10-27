# -*- coding: utf-8 -*-
"""Aesthetic taste — no LLM, no GPU, no network.

    python tools/test_aesthetic.py

Guards the taste model the appreciation prompts are built from: thirteen distinct
profiles, every axis present and in range, prompts that force a specific reading
instead of generic praise, a verdict space that includes dislike, and an operator
switch back to the old invitation.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.core import aesthetic  # noqa: E402
from src.world.eternal_page import CIRCLE  # noqa: E402

PASSED, FAILED = [], []


def check(name: str, cond: object, extra: str = "") -> None:
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}{('  ' + extra) if extra else ''}")


def main() -> int:
    print("== The module ==")
    src = (ROOT / "src" / "core" / "aesthetic.py").read_text(encoding="utf-8")
    check("no Streamlit in the taste model", "streamlit" not in src)
    check("no network in the taste model",
          not any(t in src for t in ("requests", "urllib", "http.client")))

    print("== Every Heir has taste ==")
    check("thirteen profiles", len(aesthetic.PROFILES) == 13, str(len(aesthetic.PROFILES)))
    check("all thirteen circle Heirs covered", set(aesthetic.PROFILES) == set(CIRCLE),
          str(sorted(set(CIRCLE) - set(aesthetic.PROFILES))))
    bad_axes, bad_range, empty = [], [], []
    for cid, prof in aesthetic.PROFILES.items():
        if set(prof["axes"]) != set(aesthetic.AXES):
            bad_axes.append(cid)
        for k, v in prof["axes"].items():
            if not (-2 <= int(v) <= 2):
                bad_range.append(f"{cid}.{k}={v}")
        if not prof.get("notices") or len(prof["notices"]) != 3 or not prof.get("voice"):
            empty.append(cid)
    check("every profile covers every axis", not bad_axes, ", ".join(bad_axes))
    check("every stance is in -2..2", not bad_range, ", ".join(bad_range))
    check("every profile has three notices and a vocabulary", not empty, ", ".join(empty))

    print("== The Heirs are not the same person ==")
    ids = sorted(aesthetic.PROFILES)
    identical = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if aesthetic.PROFILES[a]["axes"] == aesthetic.PROFILES[b]["axes"]:
                identical.append(f"{a}={b}")
    check("no two Heirs share a stance set", not identical, ", ".join(identical))
    distinct = {tuple(sorted(p["axes"].items())) for p in aesthetic.PROFILES.values()}
    check("at least ten distinct taste signatures", len(distinct) >= 10, str(len(distinct)))
    # A spread on each axis is what lets judgements differ in practice.
    flat = []
    for key in aesthetic.AXES:
        values = {p["axes"][key] for p in aesthetic.PROFILES.values()}
        if len(values) < 3:
            flat.append(f"{key}: {sorted(values)}")
    check("every axis is contested across the cast", not flat, ", ".join(flat))

    print("== The prompt forces a reading, not praise ==")
    brief = aesthetic.vision_brief("mydei")
    check("names the Heir's own leanings", "toward plainness" in brief or "toward craft" in brief)
    check("asks for concrete things first", "Name two or three things that are actually there" in brief)
    check("offers a negative verdict", "it leaves me cold" in brief and "it offends me" in brief)
    check("asks for a change or a reason not to", "one thing you would change" in brief)
    check("bans generic praise", "breathtaking" in brief)
    check("caps the length", "Five sentences at most" in brief)
    check("says taste is not a judgement of the visitor",
          "taste, not judgement of the visitor" in brief)
    check("tells the Heir what to look at", "where the light falls" in brief)
    music = aesthetic.music_brief("hysilens", "68 bpm, solo violin, a rising third.",
                                  label=" (a nocturne)", prompt="What does this music make you feel?")
    check("music brief carries the ear's reading", "68 bpm, solo violin" in music)
    check("music brief carries the label", "(a nocturne)" in music)
    check("music brief keeps the visitor's question",
          "What does this music make you feel?" in music)
    check("music brief asks for a verdict too", "it leaves me cold" in music)
    check("her own words appear", "the note" in music or "rhythm" in music)

    print("== Per-Heir voice ==")
    third_person = [cid for cid, p in aesthetic.PROFILES.items()
                    if " he will not" in p["refuses"] or " she will not" in p["refuses"]]
    check("no third-person 'he/she will not' left", not third_person, ", ".join(third_person))
    check("stances reach the prompt in second person",
          "You will not" in aesthetic.stance_text("anaxa"))

    print("== The operator switch ==")
    os.environ["AMP_AESTHETIC_TASTE"] = "0"
    try:
        legacy = aesthetic.vision_brief("mydei")
        check("switch off restores the old invitation",
              "share your genuine aesthetic response" in legacy)
    finally:
        os.environ.pop("AMP_AESTHETIC_TASTE", None)
    check("switch on is the default", aesthetic.enabled())
    check("an unknown Heir falls back safely",
          "share your genuine aesthetic response" in aesthetic.vision_brief("nobody"))

    print("== The engine uses it ==")
    engine = (ROOT / "src" / "core" / "agent_manager.py").read_text(encoding="utf-8")
    check("vision path uses the taste model",
          "aesthetic.vision_brief(character_id)" in engine)
    check("music path uses the taste model",
          "aesthetic.music_brief(character_id" in engine)
    check("the old constants are no longer called",
          "_APPRECIATION_VISION +" not in engine and "_APPRECIATION_MUSIC.format(" not in engine)

    print("== Two-stage picture path ==")
    mb = aesthetic.judgement_brief("mydei", "A blue hall, light on the steps, a still pool.")
    check("the judgement carries what the eye saw",
          "A blue hall, light on the steps" in mb)
    check("the judgement carries the Heir's taste", "toward plainness" in mb)
    check("the judgement still demands a verdict", "it leaves me cold" in mb)
    check("the visitor's words are kept",
          "look at this" in aesthetic.judgement_brief("mydei", "a hall", "look at this"))
    check("the perception prompt asks for no judgement",
          "No judgement" in aesthetic.PERCEPTION_SYSTEM)
    check("perception brief names what to look at",
          "where the light falls" in aesthetic.perception_brief("picture"))

    print("== The eyesight fallback ==")
    from src.core.llm_client import LLMClient

    client = LLMClient(model="x", vision_model="gemma3n")
    candidates = client._vision_candidates()
    check("the configured model is tried first", candidates[0] == "gemma3n", str(candidates))
    check("a model that can see is the fallback", len(candidates) > 1, str(candidates))
    check("a multimodal refusal is recognised",
          client._multimodal_refused(Exception(
              "model does not support multimodal requests")))
    check("other errors are not mistaken for it",
          not client._multimodal_refused(Exception("connection refused")))

    print("== Silence is not a reply ==")
    from src.core.agent_manager import _looks_like_silence

    for sample, expected in (("...", True), ("", True), ("   ", True), ("—", True),
                             ("Ah.", False), ("Hm.", False)):
        check(f"silence detector: {sample!r} -> {expected}",
              _looks_like_silence(sample) is expected)
    check("the engine retries a silent reply", "_nudge_reply(messages)" in engine)

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
