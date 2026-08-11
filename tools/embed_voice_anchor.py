"""
embed_voice_anchor.py — embed the measured speech profile + a few real canon
lines into each card's BASE `prompts.system_prompt` as a permanent voice anchor.

The dialogue-style standard (tools/test_dialogue_style.py) uses
`build_system_prompt()` which already appends relationships/speech/voice digest,
BUT the base system_prompt is the persona description the model always sees.
Adding the measured profile + canon exemplars there makes the voice anchor
permanent for BOTH the test and the deployed sanctuary.

Deliberately NO catchphrase list (that caused the model to spam "Snowy~!" in an
earlier iteration). Just profile + exemplars + discipline.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.core.heir_folders import HEIR_FOLDERS  # noqa: E402
from src.knowledge.kb_builder import CHARACTER_ALIASES  # noqa: E402
from tools.test_dialogue_resemblance import sample_canon_lines  # noqa: E402

CARDS = ROOT / "src" / "characters"
START = "\n\nVOICE (measured from your own canon lines) — this is the most important part of how you speak:"


def build_voice_block(name: str, stats: dict, exemplars: list[str]) -> str:
    wps = stats.get("avg_words_per_sentence", 8)
    wl = stats.get("avg_word_len", 4.4)
    short = stats.get("pct_short_sentences_leq6", 40)
    ell = stats.get("pct_lines_ellipsis", 20)
    q = stats.get("pct_lines_question", 20)
    ex = stats.get("pct_lines_exclaim", 15)
    wpl = stats.get("avg_words_per_line", 14)

    lines = [
        START,
        f"- You average {wps:.1f} words per sentence and about {wpl:.0f} words per line; "
        f"{short:.1f}% of your sentences are very short (6 words or fewer).",
        f"- Your average word is {wl:.2f} letters — you use simple, everyday words.",
        f"- You trail off '...' in {ell:.1f}% of lines, ask questions in {q:.1f}%, and "
        f"are emphatic in {ex:.1f}%.",
        "",
        "Rules for every reply:",
        "- Keep it SHORT — one sentence, usually under 14 words. A fragment or an "
        "exclamation is fine.",
        "- Say the thing, then stop. Never explain, summarise, or moralise.",
        "- Plain, direct, everyday words. NEVER theatrical, poetic, or flowery.",
        "- NO beautiful rhetoric: no elegant flourishes, no polished aphorisms, no "
        "poetic imagery. Write the plain, real line the character would say — even "
        "if it is rough or awkward. Eloquence is a failure, not a feature.",
        "- Never lean on a single motif or catchphrase as a crutch (e.g. repeating "
        "the same image every line) — each line is a fresh, specific thing the "
        "character would say.",
        "- No name prefix, no narration, no stage directions, no asterisks.",
        "- Never quote or repeat a canon line above verbatim — say something new "
        "in the same voice.",
    ]
    if exemplars:
        lines.append("")
        lines.append("Your own canon lines — match this voice, this length, this rhythm:")
        lines.extend(f'- "{e}"' for e in exemplars[:6])
    return "\n".join(lines)


def apply(path: Path, dry_run: bool = False) -> bool:
    with open(path, encoding="utf-8") as f:
        card = json.load(f)
    cid = path.stem
    prompts = card.get("prompts", {})
    sp = prompts.get("system_prompt", "")
    name = card.get("meta", {}).get("name", cid)
    speech = card.get("speech", {}) or {}
    stats = ((speech.get("style_measured")) or {}).get("stats")
    if not stats:
        print(f"  ! {cid}: no measured stats")
        return False

    # Canon exemplars from the Heir's OWN memories — sampled evenly across the
    # whole corpus (different scenes/moods), richer than refinement.evidence
    # (which is tiny for several Heirs and caused echo-collapse).
    exemplars = []
    try:
        aliases = CHARACTER_ALIASES.get(cid, [cid])
        wpl = (stats.get("avg_words_per_line") or 14)
        max_words = max(12, int(wpl * 1.6))
        exemplars = sample_canon_lines(
            ROOT / HEIR_FOLDERS.get(cid, cid), aliases, 6, max_words=max_words
        )
    except Exception:
        pass

    block = build_voice_block(name, stats, exemplars)

    # Remove any previously embedded voice block (idempotent).
    cleaned = re.split(r"\nVOICE \(measured from your own canon lines\).*", sp, flags=re.S)[0].rstrip()
    new_sp = cleaned + block

    if dry_run:
        print(f"  ~ {cid}: would embed voice anchor (len {len(sp)} -> {len(new_sp)})")
        return False

    if new_sp != sp:
        prompts["system_prompt"] = new_sp
        card["prompts"] = prompts
        with open(path, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {cid}: voice anchor embedded (len {len(sp)} -> {len(new_sp)})")
        return True
    print(f"  = {cid}: unchanged")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heirs", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    heirs = [h.strip() for h in args.heirs.split(",") if h.strip()]
    files = sorted(CARDS.glob("*.json"))
    if heirs:
        files = [CARDS / f"{h}.json" for h in heirs if (CARDS / f"{h}.json").exists()]

    n = 0
    for path in files:
        if apply(path, dry_run=args.dry_run):
            n += 1
    print(f"\n{len(files)} cards processed, {n} updated.")


if __name__ == "__main__":
    main()
