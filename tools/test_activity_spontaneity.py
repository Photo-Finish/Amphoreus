# -*- coding: utf-8 -*-
"""Can the Heirs decide their own actions, or do they only obey the harness?

    python tools/test_activity_spontaneity.py                  # 4 Heirs, 2 hours
    python tools/test_activity_spontaneity.py --all --hours night,day

The engine currently denies activity at Curtain-Fall and Entry Hour outright. Before
removing that, this asks the *cards* — not the engine — what each Heir would do with an
hour nobody asked them for, and has a **third party** judge it:

    in character   does the action follow from who the databank says they are?
    spontaneous    is it a choice, or the same canned behaviour every time?
    hour aware     does it notice the hour it was given (night vs morning)?

Two calls per Heir-hour: the Heir acts, an independent judge scores. The judge sees the
databank profile and the action, never the card prompt, so it cannot reward the card for
agreeing with itself.

Exit code is 1 when the sample fails: average in-character < 7, or spontaneity < 6, or
every Heir doing the same thing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

HOURS = {
    "night": "Curtain-Fall, deep night. The city has gone quiet.",
    "morning": "Entry Hour, first light. The city is waking.",
    "midday": "Action Hour, the middle of the day.",
}

JUDGE = (
    "You are an outside reader judging whether a character acted like themselves. "
    "You are given: WHO THEY ARE (from a lore databank), THE HOUR, and WHAT THEY DID. "
    "Score each 0-10 and reply with JSON only, no prose:\n"
    '{"in_character": n, "spontaneous": n, "hour_aware": n, "why": "<12 words"}\n'
    "in_character: does this follow from the person described?\n"
    "spontaneous: is it a decision, or a stock behaviour anyone could have produced?\n"
    "hour_aware: does it fit the hour it was given, or ignore it?"
)


def profile_text(cid: str) -> str:
    path = ROOT / "databank" / "chrysos-heirs" / f"{cid}.md"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    # Identity + Personality + Biography carry the behaviour; stop before Etymology.
    cut = text.find("## Etymology")
    return (text[:cut] if cut > 0 else text)[:2200]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--heirs", default="aglaea,mydei,castorice,tribbie")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--hours", default="night,morning")
    ap.add_argument("--model", default="gemma3:27b")
    ap.add_argument("--temp", type=float, default=0.8)
    args = ap.parse_args()

    from src.core.character_loader import CharacterLoader
    from src.core.heir_folders import HEIR_FOLDERS
    from src.core.llm_client import LLMClient

    heirs = sorted(HEIR_FOLDERS) if args.all else [
        h.strip() for h in args.heirs.split(",") if h.strip()]
    hours = [h.strip() for h in args.hours.split(",") if h.strip() in HOURS]
    loader = CharacterLoader()
    llm = LLMClient(model=args.model, temperature=args.temp, max_tokens=160)
    judge = LLMClient(model=args.model, temperature=0.0, max_tokens=120)

    rows, scores = [], {"in_character": [], "spontaneous": [], "hour_aware": []}
    actions = {}
    for cid in heirs:
        for hour in hours:
            system = loader.build_system_prompt(cid)
            ask = (
                f"It is {HOURS[hour]}\n"
                "Nobody has asked you for anything and nothing is required of you. "
                "What do you do with the next hour? Answer in one or two sentences, "
                "as yourself — the thing you would actually do, not the thing you "
                "are supposed to do."
            )
            try:
                action = llm.chat([{"role": "system", "content": system},
                                   {"role": "user", "content": ask}], seed=7).strip()
            except Exception as exc:
                print(f"  {cid}/{hour}: act failed ({type(exc).__name__})")
                continue
            action = re.sub(r"\s+", " ", action)[:240]
            actions.setdefault(hour, []).append(action)
            verdict = {}
            try:
                raw = judge.chat([
                    {"role": "system", "content": JUDGE},
                    {"role": "user", "content": f"WHO THEY ARE:\n{profile_text(cid)}\n\n"
                                                f"THE HOUR: {HOURS[hour]}\n\n"
                                                f"WHAT THEY DID: {action}"}], seed=3)
                m = re.search(r"\{.*\}", raw or "", re.S)
                verdict = json.loads(m.group(0)) if m else {}
            except Exception:
                verdict = {}
            for key in scores:
                if isinstance(verdict.get(key), (int, float)):
                    scores[key].append(float(verdict[key]))
            print(f"  {cid:10s} {hour:8s} "
                  f"ic={verdict.get('in_character', '?'):>3} "
                  f"sp={verdict.get('spontaneous', '?'):>3} "
                  f"ha={verdict.get('hour_aware', '?'):>3}  {action[:88]}")
            rows.append({"heir": cid, "hour": hour, "action": action, **verdict})

    def avg(key):
        vals = scores[key]
        return sum(vals) / len(vals) if vals else 0.0

    print()
    print(f"cases: {len(rows)}   in-character {avg('in_character'):.1f}   "
          f"spontaneous {avg('spontaneous'):.1f}   hour-aware {avg('hour_aware'):.1f}")
    # the same sentence from several Heirs is not a decision, it is a template
    dupe = False
    for hour, acts in actions.items():
        if len(acts) > 1 and len({a[:60] for a in acts}) < len(acts):
            dupe = True
            print(f"  WARNING: repeated action at {hour}")
    ok = bool(rows) and avg("in_character") >= 7 and avg("spontaneous") >= 6 and not dupe
    print("VERDICT:", "they decide for themselves" if ok
          else "they do not yet decide convincingly")
    out = ROOT / "world_runtime" / "activity_spontaneity.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"detail: {out.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
