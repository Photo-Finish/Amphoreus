"""
test_dialogue_resemblance.py — the standard for how closely an Heir model
resembles the character.

METHOD
------
For each Heir we take real contexts from the known story dialogues
(personal-memories.md). For every test case:
  1. context  = the in-story scene + the line(s) spoken just before the Heir's
                line (this is what "the dialogue suggested" the Heir respond to);
  2. expected = the Heir's ORIGINAL canon line;
  3. actual   = the Heir model's reply to that context (in character);
  4. judge    = a STRICT LLM judge (rubric: meaning / emotion / character voice,
                0-100 each, overall) scores how closely `actual` resembles
                `expected`. Pass when overall >= threshold (default 85).
  A second, objective signal (embedding cosine, all-MiniLM) is also reported.

The model is given the card's base `prompts.system_prompt` only — NOT the
voice-digest/relationships blocks — so the test line itself is never leaked.

USAGE
-----
    python tools/test_dialogue_resemblance.py                 # all 13 Heirs
    python tools/test_dialogue_resemblance.py --heirs phainon --limit 3
    python tools/test_dialogue_resemblance.py --threshold 85 --model qwen2.5:14b-instruct
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.heir_folders import HEIR_FOLDERS  # noqa: E402
from src.core.llm_client import LLMClient  # noqa: E402
from src.knowledge.kb_builder import CHARACTER_ALIASES  # noqa: E402

SPEAKER_RE = re.compile(r"^\s*>?\s*\*\*(.+?):\*\*\s*(.*)$")
PART_RE = re.compile(r"^### Part \d+ — `([^`]+)`")

REPORT_PATH = ROOT / "docs" / "RESEMBLANCE-REPORT.md"
_lock_handle = None


def acquire_lock() -> bool:
    """Single-instance guard via a Windows NAMED MUTEX (kernel object — atomic
    across processes). The terminal harness sometimes double-spawns the
    command; this guarantees only one baseline writes the report."""
    global _lock_handle
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel32.CreateMutexW.use_last_error = True  # required for get_last_error()
        _lock_handle = kernel32.CreateMutexW(None, False, "Global\\AmphoreusResemblanceBaseline")
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
            print("Another baseline is already running — exiting.")
            return False
        return True
    except Exception as err:
        print(f"lock guard unavailable ({err}) — continuing.")
        return True


def release_lock():
    global _lock_handle
    try:
        if _lock_handle:
            ctypes.windll.kernel32.ReleaseMutex(_lock_handle)
            ctypes.windll.kernel32.CloseHandle(_lock_handle)
            _lock_handle = None
    except Exception:
        pass

JUDGE_SYSTEM = (
    "You are a strict dialogue-authenticity judge for an AI character sanctuary. "
    "Compare the MODEL reply to the ORIGINAL canon reply of a character, given the "
    "scene context. Score 0-100 for each of: (1) meaning preserved, "
    "(2) emotion/tone matched, (3) character voice matched. Be strict and honest: "
    "an excellent paraphrase that keeps meaning and voice is 85-95; a reply that "
    "changes the meaning, sounds generic, or breaks character scores lower. "
    "Output ONLY a JSON object: "
    '{"meaning":0-100,"emotion":0-100,"voice":0-100,"overall":0-100,"reason":"short"}'
)


def parse_parts(path: Path):
    parts = []
    src, scene, lines = "", "", []
    for ln in path.read_text(encoding="utf-8").splitlines():
        m = PART_RE.match(ln)
        if m:
            if lines:
                parts.append((src, scene, lines))
            src, scene, lines = m.group(1), "", []
            continue
        if ln.startswith("**Context:**"):
            scene = ln.replace("**Context:**", "").strip()
            continue
        if ln.strip():
            lines.append(ln)
    if lines:
        parts.append((src, scene, lines))
    return parts


def build_cases(heir_id, parts, limit):
    aliases = CHARACTER_ALIASES.get(heir_id, [heir_id])
    cases = []
    for src, scene, lines in parts:
        for i, ln in enumerate(lines):
            m = SPEAKER_RE.match(ln)
            if not m:
                continue
            speaker, text = m.group(1).strip(), m.group(2).strip()
            if not text or not any(a.lower() in speaker.lower() for a in aliases):
                continue
            prev = [l for l in lines[max(0, i - 3):i] if SPEAKER_RE.match(l)][-2:]
            if not prev:
                continue
            context = f"(scene: {scene})\n" if scene else ""
            context += "What was said around you:\n" + "\n".join(prev)
            cases.append((context, text))
    if not cases:
        return []
    if len(cases) <= limit:
        return cases
    step = len(cases) / limit
    return [cases[int(k * step)] for k in range(limit)]


def extract_json(text: str) -> dict:
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1)
    s, e = t.find("{"), t.rfind("}")
    if s == -1 or e <= s:
        raise ValueError("no JSON in judge reply")
    return json.loads(t[s:e + 1])


def judge(llm, heir_name, ctx, expected, actual):
    user = (
        f"Scene context: {ctx}\n\n"
        f'ORIGINAL canon reply of {heir_name}: "{expected}"\n\n'
        f'MODEL reply: "{actual}"\n\n'
        "Score the model reply against the original (strict rubric)."
    )
    reply = llm.chat(
        [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}],
        temperature=0.0,
        max_tokens=320,
    )
    return extract_json(reply)


def cosine_sim(a, b, ef):
    import numpy as np
    ea, eb = ef([a, b])
    ea = np.asarray(ea).reshape(-1)
    eb = np.asarray(eb).reshape(-1)
    n = np.linalg.norm(ea) * np.linalg.norm(eb)
    return float(np.dot(ea, eb) / n) if n else 0.0


def main():
    ap = argparse.ArgumentParser(description="Dialogue-resemblance standard for the Heir models.")
    ap.add_argument("--heirs", default="")
    ap.add_argument("--limit", type=int, default=8, help="test cases per Heir")
    ap.add_argument("--threshold", type=int, default=85, help="pass bar, 0-100 (default 85)")
    ap.add_argument("--model", default="qwen2.5:14b-instruct")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=120)
    args = ap.parse_args()

    if not acquire_lock():
        return 0
    try:
        return _run(args)
    finally:
        release_lock()


def _run(args):
    heir_ids = [h.strip() for h in args.heirs.split(",") if h.strip()] or list(HEIR_FOLDERS)

    ef = None
    try:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        ef = DefaultEmbeddingFunction()
    except Exception:
        pass

    llm = LLMClient(model=args.model)
    print(f"Resemblance standard — model {args.model}, pass >= {args.threshold}, "
          f"{args.limit} cases/Heir\n")

    report_lines = [
        "# Dialogue-Resemblance Report (the Heir-model standard)",
        "",
        f"*Generated: 2026-08-10 · model `{args.model}` · pass bar ≥ {args.threshold}/100 (LLM judge)*",
        "",
        "Method: real canon contexts from `personal-memories.md` → the Heir model replies",
        "in character → a strict LLM judge scores meaning/emotion/voice (0-100 each);",
        "embedding cosine (all-MiniLM) reported as a secondary signal. Base",
        "`prompts.system_prompt` only (no voice-digest leakage).",
        "",
        "| Heir | cases | pass | avg judge | avg cosine | pass rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for heir_id in heir_ids:
        folder = ROOT / HEIR_FOLDERS.get(heir_id, heir_id)
        memory = folder / "personal-memories.md"
        card_path = ROOT / "src" / "characters" / f"{heir_id}.json"
        if not memory.exists() or not card_path.exists():
            print(f"  ! {heir_id}: missing memory/card")
            continue
        card = json.loads(card_path.read_text(encoding="utf-8"))
        name = card["meta"]["name"]
        system = card.get("prompts", {}).get("system_prompt", f"You are {name}.")
        cases = build_cases(heir_id, parse_parts(memory), args.limit)

        passed, total = 0, 0
        judges, cosines, fails = [], [], []
        for ctx, expected in cases:
            user = f"{ctx}\n\nReply as {name} in character, briefly."
            try:
                actual = llm.chat(
                    [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                ).strip()
            except Exception as err:
                print(f"  {heir_id}: LLM error {err}")
                continue
            if not actual:
                continue
            try:
                j = judge(llm, name, ctx, expected, actual)
                score = int(j.get("overall", 0))
            except Exception:
                score = 0
            total += 1
            c = cosine_sim(actual, expected, ef) if ef else 0.0
            judges.append(score)
            cosines.append(c)
            if score >= args.threshold:
                passed += 1
            else:
                fails.append((score, ctx[:80], expected[:80], actual[:80]))
            print(f"  {heir_id:>26}: judge {score:>3} | cos {c:.2f} "
                  f"{'PASS' if score >= args.threshold else 'FAIL'}")

        avg_j = sum(judges) / len(judges) if judges else 0.0
        avg_c = sum(cosines) / len(cosines) if cosines else 0.0
        rate = f"{100 * passed // max(1, total)}%"
        print(f"  {heir_id:>26}: {passed}/{total} pass | avg judge {avg_j:.0f} | "
              f"avg cos {avg_c:.2f} | {rate}")
        report_lines.append(
            f"| {name} ({heir_id}) | {total} | {passed} | {avg_j:.0f} | {avg_c:.2f} | {rate} |"
        )
        if fails:
            report_lines.append("")
            report_lines.append(f"**{name}** — failed cases (judge < {args.threshold}):")
            for s, ctx, exp, act in fails[:5]:
                report_lines.append(f"- {s}/100: ctx *{ctx}* → expected *{exp}* → model *{act}*")

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\nReport: {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
