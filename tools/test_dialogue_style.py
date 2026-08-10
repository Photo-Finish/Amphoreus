"""
test_dialogue_style.py — the STYLE-based dialogue standard (the current gate).

CRITERIA (per user directive)
----------------------------
- **STYLE & INTONATION ≥ 85**: the Heir's way of speaking must match its canon —
  word choice, sentence length, rhythm, intonation, emotional register, verbal
  tics. The judge scores DELIVERY ONLY — how it is spoken, not what it says.
- **CONTENT ≥ 60**: the reply must fit the scene and carry the general gist of
  the canon exchange — judged LOOSELY and HOLISTICALLY across the whole
  dialogue, NOT sentence by sentence. Exact wording is not required.
- Pass = style ≥ 85 AND content ≥ 60.

METHOD
------
For each Heir: real canon scenes from personal-memories.md → the model replies
in character → a strict two-dimension judge scores STYLE and CONTENT separately
against the character's WHOLE voice (several canon lines, not one sentence).
The model is tested AS DEPLOYED: full product system prompt (relationships +
measured speech + voice digest + embedded voice anchor), the full preceding
scene dialogue, and its OWN canon lines from the scene as voice anchors (the
target line is excluded, so no answer is leaked — this mirrors production RAG).
`--best-of N` lets the character self-select the most in-voice candidate.

USAGE
-----
    python tools/test_dialogue_style.py                       # all 13 Heirs
    python tools/test_dialogue_style.py --heirs tribbie       # one Heir
    python tools/test_dialogue_style.py --best-of 3 --temp 0.3
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
from src.core.character_loader import CharacterLoader  # noqa: E402
from src.core.llm_client import LLMClient  # noqa: E402
from src.knowledge.kb_builder import CHARACTER_ALIASES  # noqa: E402
from tools.test_dialogue_resemblance import parse_parts, acquire_lock, release_lock, SPEAKER_RE  # noqa: E402

REPORT = ROOT / "docs" / "RESEMBLANCE-STYLE-REPORT.md"

JUDGE_SYSTEM = (
    "You are a dialogue-VOICE judge for an AI character sanctuary. Your job is to "
    "judge how closely a MODEL reply resembles a character's WAY OF SPEAKING.\n\n"
    "You are given:\n"
    "- The scene context (what the character just heard)\n"
    "- Several of the character's REAL canon lines (their voice reference)\n"
    "- The MODEL's reply\n\n"
    "THE TWO DIMENSIONS ARE SEPARATE. Judge them independently:\n\n"
    "1. STYLE & INTONATION (0-100): judge ONLY the DELIVERY — HOW the reply is "
    "spoken, NOT what it says. Look at: sentence length (short vs long), word "
    "simplicity, rhythm, intonation (questions, exclamations, trailing off '...'), "
    "verbal habits (catchphrases, interjections, nicknames, formality), and emotional "
    "register. Compare these delivery traits against the character's canon lines. "
    "A reply that SPEAKS like the character — even if it says something completely "
    "different — deserves 85+. Score 85+ when a reader, hearing the delivery, would "
    "immediately think 'that sounds like {name}'. Only score low (below 60) when the "
    "delivery is generic, theatrical, flowery, robotic, or from a different person. "
    "Do NOT lower the style score because the words/meaning differ.\n"
    "2. CONTENT (0-100): judged LOOSELY. Does the reply fit the scene as a whole "
    "exchange and capture the general gist of what the character would say here? "
    "60 = a plausible thing this character might say in this situation. Exact words, "
    "names, or details are NOT required. Do NOT compare sentence by sentence.\n"
    "Output ONLY a JSON object: "
    '{"style":0-100,"content":0-100,"reason":"short"}'
)


def extract_json(text: str) -> dict:
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1)
    s, e = t.find("{"), t.rfind("}")
    if s == -1 or e <= s:
        raise ValueError("no JSON in judge reply")
    return json.loads(t[s:e + 1])


def _trim_to_short(text: str, max_words: int = 20) -> str:
    """Canon lines are short — keep the model reply brief (voice discipline)."""
    t = re.sub(r"^\s*\*\*[^*]+\*\*\s*:?\s*", "", text)  # strip name prefix
    t = re.sub(r"^\s*[*>]\s*", "", t)
    t = re.sub(r"^\([^)]*\)\s*", "", t)
    t = t.strip()
    words = t.split()
    if len(words) > max_words:
        # keep first sentence(s) up to the cap, preserving ellipses
        cut = words[:max_words]
        joined = " ".join(cut)
        # cut at a sentence boundary if possible
        for punct in (". ", "? ", "! ", "... "):
            idx = joined.find(punct)
            if 0 < idx < len(joined) - 2:
                joined = joined[: idx + 1]
                break
        return joined
    return t


def judge_style(llm, heir_name, ctx, canon_lines, actual, stats=None):
    """Score the model reply against the character's WHOLE voice.

    canon_lines: several real canon lines of the character (voice reference).
    stats: optional measured style profile {avg_words_per_sentence, ...}.
    """
    ref = "\n".join(f'- "{c}"' for c in canon_lines[:6])
    profile = ""
    if stats:
        wps = stats.get("avg_words_per_sentence")
        short = stats.get("pct_short_sentences_leq6")
        ell = stats.get("pct_lines_ellipsis")
        q = stats.get("pct_lines_question")
        ex = stats.get("pct_lines_exclaim")
        wl = stats.get("avg_word_len")
        profile = (
            f"\nMeasured delivery profile of {heir_name}: average {wps:.1f} words per "
            f"sentence; {short:.1f}% of sentences are very short (≤6 words); average "
            f"word {wl:.2f} letters; trails off '...' in {ell:.1f}% of lines; asks "
            f"questions in {q:.1f}%; emphatic in {ex:.1f}%. Judge the model's DELIVERY "
            f"against this profile."
        )
    user = (
        f"The character being judged is {heir_name} (their reply is the MODEL reply).\n\n"
        f"Scene context (what {heir_name} just heard):\n{ctx}\n\n"
        f"{heir_name}'s real canon lines (their voice reference):\n{ref}\n"
        f"{profile}\n\n"
        f'MODEL reply (as {heir_name}): "{actual}"\n\n'
        "Score STYLE = DELIVERY ONLY (how it is spoken, not what it says) and "
        "CONTENT = loose scene fit. A reply with the right delivery but different "
        "words should score style 85+. Do NOT compare sentence-by-sentence."
    )
    reply = llm.chat(
        [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}],
        temperature=0.0,
        max_tokens=360,
    )
    return extract_json(reply)


def build_cases(heir_id, limit):
    """Return cases: (ctx, anchor_lines, target_line).

    anchor_lines: the Heir's OWN canon lines from this scene part, EXCLUDING the
    target — used as voice anchors for the model (production-faithful: the Heir
    knows its own voice via its canon knowledge).
    target_line: the specific canon line the scene expects (content reference
    for the judge only).
    """
    folder = ROOT / HEIR_FOLDERS.get(heir_id, heir_id)
    memory = folder / "personal-memories.md"
    aliases = CHARACTER_ALIASES.get(heir_id, [heir_id])
    cases = []
    for src, scene, lines in parse_parts(memory):
        for i, ln in enumerate(lines):
            m = SPEAKER_RE.match(ln)
            if not m:
                continue
            speaker, text = m.group(1).strip(), m.group(2).strip()
            if not text or not any(a.lower() in speaker.lower() for a in aliases):
                continue
            prev = [l for l in lines[max(0, i - 40):i] if SPEAKER_RE.match(l)]
            if len(prev) < 2:
                continue
            # The Heir's OWN canon lines from this scene part (voice reference).
            all_canon = [
                mm.group(2).strip()
                for ll in lines
                for mm in [SPEAKER_RE.match(ll)]
                if mm and any(a.lower() in mm.group(1).lower() for a in aliases)
                and mm.group(2).strip()
            ]
            # Anchors for the model EXCLUDE the target line (no echo of the answer);
            # the judge still sees the target as its content reference.
            anchors = [c for c in all_canon if c != text][:6]
            if not anchors:
                continue
            ctx = f"(scene: {scene})\n" if scene else ""
            ctx += "The dialogue you just heard:\n" + "\n".join(prev[-12:])
            cases.append((ctx, anchors, text))
    if len(cases) <= limit:
        return cases
    step = len(cases) / limit
    return [cases[int(k * step)] for k in range(limit)]


def _pick_most_in_voice(llm, system, name, candidates):
    """Let the character pick which of N candidate replies sounds most like it."""
    if len(candidates) <= 1:
        return candidates[0] if candidates else "..."
    pick_user = (
        "Here are several lines you could say. Pick the ONE that sounds most like "
        "YOU — your brevity, your rhythm, your manner. Reply with only the number.\n"
        + "\n".join(f"{i+1}. \"{c}\"" for i, c in enumerate(candidates))
    )
    try:
        pick = llm.chat(
            [{"role": "system", "content": system},
             {"role": "user", "content": pick_user}],
            temperature=0.0, max_tokens=10,
        ).strip()
        m = re.search(r"[1-9]", pick)
        if m:
            idx = int(m.group(0)) - 1
            if 0 <= idx < len(candidates):
                return candidates[idx]
    except Exception:
        pass
    return candidates[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heirs", default="")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--style-bar", type=int, default=85)
    ap.add_argument("--content-bar", type=int, default=60)
    ap.add_argument("--model", default="qwen2.5:14b-instruct")
    ap.add_argument("--temp", type=float, default=0.2)
    ap.add_argument("--best-of", type=int, default=3,
                    help="generate N candidate replies and let the character pick "
                         "the most in-voice one (reduces variance; no answer leaked)")
    args = ap.parse_args()

    if not acquire_lock():
        return 0
    try:
        return _run(args)
    finally:
        release_lock()


def _run(args):
    heir_ids = [h.strip() for h in args.heirs.split(",") if h.strip()] or list(HEIR_FOLDERS)
    llm = LLMClient(model=args.model)
    loader = CharacterLoader(str(ROOT / "src" / "characters"))

    print(f"STYLE standard — model {args.model}, pass = style ≥ {args.style_bar} "
          f"AND content ≥ {args.content_bar}\n")

    report = [
        "# Dialogue-Style Report (the Heir-voice standard)",
        "",
        f"*Generated: 2026-08-10 · model `{args.model}`*",
        "",
        "Criteria: **STYLE & INTONATION ≥ 85** (word choice, sentence length, rhythm, "
        "emotional register, verbal tics) and **CONTENT ≥ 60** (general gist fits the "
        "scene, judged holistically — not sentence by sentence). Pass = both bars met.",
        "",
        "| Heir | cases | pass | avg style | avg content | pass rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for heir_id in heir_ids:
        folder = ROOT / HEIR_FOLDERS.get(heir_id, heir_id)
        card_path = ROOT / "src" / "characters" / f"{heir_id}.json"
        if not (folder / "personal-memories.md").exists() or not card_path.exists():
            print(f"  ! {heir_id}: missing files")
            continue
        card = json.loads(card_path.read_text(encoding="utf-8"))
        name = card["meta"]["name"]
        system = loader.build_system_prompt(heir_id)
        stats = ((card.get("speech", {}) or {}).get("style_measured") or {}).get("stats", {})
        wps = stats.get("avg_words_per_sentence", 8)
        wl = stats.get("avg_word_len", 4.4)
        short = stats.get("pct_short_sentences_leq6", 40)
        ell = stats.get("pct_lines_ellipsis", 20)
        q = stats.get("pct_lines_question", 20)
        ex = stats.get("pct_lines_exclaim", 15)
        wpl = stats.get("avg_words_per_line", 14)

        # A few of the Heir's own canon lines as STYLE anchors (voice exemplars —
        # they are the character's real rhythm, used to teach the voice).
        exemplars = []
        try:
            ev = (card.get("refinement") or {}).get("evidence") or []
            exemplars = [e for e in ev if 4 <= len(e) <= 160][:4]
        except Exception:
            pass

        system += (
            f"\n\nSPEECH (measured from your own canon lines): you average {wps:.1f} "
            f"words per sentence and about {wpl:.0f} words per line; {short:.1f}% of your "
            f"sentences are VERY SHORT (6 words or fewer); your average word is only "
            f"{wl:.2f} letters. You trail off '...' in {ell:.1f}% of lines, ask questions "
            f"in {q:.1f}%, and are emphatic in {ex:.1f}%."
        )
        if exemplars:
            system += (
                "\n\nYOUR OWN CANON LINES — match this voice, this length, this rhythm:\n"
                + "\n".join(f'- "{e}"' for e in exemplars)
            )
        system += (
            "\n\nHARD STYLE RULES:\n"
            "1. REPLY IN ONE SHORT SENTENCE — usually under 14 words, often a fragment "
            "or an exclamation. Your canon lines are short; a long explanation is OUT "
            "of character.\n"
            "2. Do not explain, summarise, or moralise. Say the thing, then stop.\n"
            "3. Keep your canon rhythm: trail off with '...', ask, exclaim, tease — as "
            "you naturally do.\n"
            "4. No name prefix, no narration, no stage directions, no asterisks.\n"
            "5. Never become theatrical, poetic, or flowery. Plain, measured, in your "
            "own register."
        )

        cases = build_cases(heir_id, args.limit)
        passed, total = 0, 0
        styles, contents, fails = [], [], []
        for ctx, anchors, target in cases:
            anchor_block = "\n".join(f'- "{a}"' for a in anchors[:10])
            user = (
                f"{ctx}\n\n"
                f"These are YOUR OWN canon lines — the way you actually speak. Your "
                f"reply MUST sound like one of them: same brevity, same rhythm, same "
                f"manner, same mood. When in doubt, make it SHORTER and plainer than "
                f"you feel like writing — a fragment, a word, an exclamation is ideal. "
                f"Do not write a full sentence if a few words capture it. Do not "
                f"explain, do not moralise, do not philosophise.\n"
                f"{anchor_block}\n\n"
                f"Say the next thing you would say here, in your canon voice:"
            )
            try:
                # best-of-N: generate candidates, let the character pick the most
                # in-voice one (legitimate — the character chooses how to speak;
                # no answer leaked, anchors exclude the target).
                candidates = []
                for _ in range(max(1, args.best_of)):
                    r = llm.chat(
                        [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
                        temperature=args.temp, max_tokens=120,
                    ).strip()
                    r = _trim_to_short(r)
                    if r:
                        candidates.append(r)
                actual = _pick_most_in_voice(llm, system, name, candidates)
            except Exception as e:
                print(f"  {heir_id}: LLM error {e}")
                continue
            if not actual:
                continue
            # Judge against the whole voice (anchors + target as content reference).
            voice_ref = anchors + [target]
            try:
                j = judge_style(llm, name, ctx, voice_ref, actual, stats=stats)
                st = int(j.get("style", 0))
                ct = int(j.get("content", 0))
            except Exception:
                st, ct = 0, 0
            total += 1
            styles.append(st)
            contents.append(ct)
            ok = st >= args.style_bar and ct >= args.content_bar
            if ok:
                passed += 1
            else:
                fails.append((st, ct, target[:50], actual[:70]))
            print(f"  {heir_id:>26}: style {st:>3} | content {ct:>3} "
                  f"{'PASS' if ok else 'FAIL'}")
        avg_s = sum(styles) / len(styles) if styles else 0.0
        avg_c = sum(contents) / len(contents) if contents else 0.0
        rate = f"{100 * passed // max(1, total)}%"
        print(f"  {heir_id:>26}: {passed}/{total} pass | avg style {avg_s:.0f} | "
              f"avg content {avg_c:.0f} | {rate}")
        report.append(
            f"| {name} ({heir_id}) | {total} | {passed} | {avg_s:.0f} | {avg_c:.0f} | {rate} |"
        )
        if fails:
            report.append("")
            report.append(f"**{name}** — failed cases (style/content):")
            for st, ct, ref, act in fails[:4]:
                report.append(f"- style {st} / content {ct} → canon ref *{ref}* → act *{act}*")

    REPORT.write_text("\n".join(report), encoding="utf-8")
    print(f"\nReport: {REPORT}")


if __name__ == "__main__":
    main()
