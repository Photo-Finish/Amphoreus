"""
measure_speech.py — fine-tune each Heir's speech parameters by MEASURING their
own canon dialogue (personal-memories.md), exactly as spoken in the quests.

For every Heir it collects their OWN lines and computes deterministic style
stats: line/sentence length, vocabulary complexity, ellipses, questions,
exclamations, contractions, interjections. It then writes two things into the
card:

  speech.vocabulary_level      -> a measured, plain description
  speech.sentence_structure    -> a measured, plain description
  speech.style_measured        -> {stats + a modest "voice_guide" paragraph}

The voice guide is deliberately PLAIN and factual — it is measured from the
canon, not invented drama. Nothing is "overcooked": the goal is that the model
speaks like the character does in the quest, not like a stage play.

USAGE:
    python tools/measure_speech.py                 # all 13 Heirs
    python tools/measure_speech.py --heirs tribbie # one Heir
    python tools/measure_speech.py --dry-run       # print stats, change nothing
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.heir_folders import HEIR_FOLDERS  # noqa: E402
from src.knowledge.kb_builder import CHARACTER_ALIASES  # noqa: E402

SPEAKER_RE = re.compile(r"^\s*>?\s*\*\*(.+?):\*\*\s*(.*)$")
PART_RE = re.compile(r"^### Part \d+ — `([^`]+)`")
STAGE_RE = re.compile(r"^[*(]|[*)]$|^\(.*\)$|^\*.*\*$")
SENT_SPLIT = re.compile(r"[.!?…]+")
WORD_RE = re.compile(r"[A-Za-z']+")

INTERJECTIONS = [
    "ah", "oh", "hmph", "hah", "ha", "well", "huh", "agh", "ugh", "hmm", "hey", "ahaha",
]
CONTRACTIONS = re.compile(
    r"\b(i'm|i've|i'll|i'd|don't|can't|won't|isn't|aren't|wasn't|weren't|it's|that's|"
    r"there's|here's|what's|who's|you're|you've|you'll|we're|we've|they're|let's|"
    r"didn't|couldn't|wouldn't|shouldn't|hasn't|haven't|doesn't|'re|'ve|'ll|'d)\b",
    re.I,
)


def own_lines(path: Path, aliases) -> list:
    """The Heir's own spoken lines (text only, stage directions excluded)."""
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        m = SPEAKER_RE.match(ln)
        if not m:
            continue
        speaker, text = m.group(1).strip(), m.group(2).strip()
        if not text:
            continue
        if not any(a.lower() in speaker.lower() for a in aliases):
            continue
        if STAGE_RE.match(text):
            continue
        # strip any leading asterisks/stage remnants inside the text
        text = re.sub(r"^\*+|\*+$", "", text).strip()
        if text:
            out.append(text)
    return out


def measure(lines: list) -> dict:
    words = [w for ln in lines for w in WORD_RE.findall(ln.lower())]
    n_words = len(words)
    n_lines = len(lines) or 1
    sentences = [s for ln in lines for s in SENT_SPLIT.split(ln) if s.strip()]
    s_lens = [len(WORD_RE.findall(s)) for s in sentences]
    l_lens = [len(WORD_RE.findall(ln)) for ln in lines]
    word_lens = [len(w) for w in words]

    def pct(x, n):
        return round(100.0 * x / n, 1) if n else 0.0

    text = "\n".join(lines)
    return {
        "n_lines": len(lines),
        "n_words": n_words,
        "avg_words_per_line": round(sum(l_lens) / n_lines, 1),
        "median_words_per_line": statistics.median(l_lens) if l_lens else 0,
        "avg_words_per_sentence": round(sum(s_lens) / len(s_lens), 1) if s_lens else 0,
        "pct_short_sentences_leq6": pct(sum(1 for x in s_lens if x <= 6), len(s_lens)),
        "pct_long_sentences_ge25": pct(sum(1 for x in s_lens if x >= 25), len(s_lens)),
        "avg_word_len": round(sum(word_lens) / len(word_lens), 2) if word_lens else 0,
        "pct_lines_ellipsis": pct(sum(1 for ln in lines if "..." in ln or "…" in ln), n_lines),
        "pct_lines_question": pct(sum(1 for ln in lines if "?" in ln), n_lines),
        "pct_lines_exclaim": pct(sum(1 for ln in lines if "!" in ln), n_lines),
        "pct_lines_quoted": pct(sum(1 for ln in lines if '"' in ln or "'" in ln), n_lines),
        "contractions_per_100": round(100.0 * len(CONTRACTIONS.findall(text)) / n_words, 1) if n_words else 0,
        "interjections_per_100": round(
            100.0 * sum(text.lower().count(f" {i}") + text.lower().count(i + " ") for i in INTERJECTIONS) / n_words, 1
        ) if n_words else 0,
    }


def describe(st: dict) -> dict:
    """Plain, moderate descriptions mapped from the measured numbers."""
    wps = st["avg_words_per_sentence"]
    if wps < 11:
        sentence = f"Short, simple sentences — in canon you average about {wps} words per sentence, and {st['pct_short_sentences_leq6']}% of them are very short (6 words or fewer)."
    elif wps < 20:
        sentence = f"Moderate-length sentences — in canon you average about {wps} words per sentence."
    else:
        sentence = f"Long, elaborate sentences — in canon you average about {wps} words per sentence, with {st['pct_long_sentences_ge25']}% exceeding 25 words."

    awl = st["avg_word_len"]
    if awl < 4.4:
        vocab = f"Simple, everyday words — your average word is only {awl} letters, so you speak plainly and accessibly."
    elif awl < 5.0:
        vocab = f"Clear, accessible words — your average word is about {awl} letters, ordinary and easy to follow."
    else:
        vocab = f"Rich, varied vocabulary — your average word is {awl} letters, so you choose fuller, more elaborate words."

    extras = []
    if st["pct_lines_ellipsis"] >= 8:
        extras.append(f"you often trail off with '...' ({st['pct_lines_ellipsis']}% of lines)")
    if st["pct_lines_question"] >= 20:
        extras.append(f"you frequently ask questions ({st['pct_lines_question']}% of lines)")
    if st["pct_lines_exclaim"] >= 12:
        extras.append(f"you are often emphatic ({st['pct_lines_exclaim']}% of lines)")
    if st["contractions_per_100"] >= 3:
        extras.append("you use contractions freely, which keeps you casual")
    if st["interjections_per_100"] >= 1.5:
        extras.append("you use small interjections (Ah, Oh, Hmph...) often")
    extra_text = (" " + "; ".join(extras) + ".") if extras else ""

    guide = (
        f"Voice guide (measured from your own canon dialogue): {sentence} "
        f"{vocab}{extra_text} Keep your speech exactly this way — plain, "
        "measured and in your own register. Do not become theatrical or flowery."
    )
    return {
        "vocabulary_level": vocab,
        "sentence_structure": sentence,
        "voice_guide": guide,
        "stats": st,
    }


def main():
    ap = argparse.ArgumentParser(description="Measure and apply canon speech parameters.")
    ap.add_argument("--heirs", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    heir_ids = [h.strip() for h in args.heirs.split(",") if h.strip()] or list(HEIR_FOLDERS)
    print(f"{'Heir':>26} | lines | w/line | w/sent | word-len | ...% | ?% | !% | contraction/100")
    print("-" * 100)

    for heir_id in heir_ids:
        folder = ROOT / HEIR_FOLDERS.get(heir_id, heir_id)
        memory = folder / "personal-memories.md"
        card_path = ROOT / "src" / "characters" / f"{heir_id}.json"
        if not memory.exists() or not card_path.exists():
            print(f"  ! {heir_id}: missing memory/card")
            continue
        aliases = CHARACTER_ALIASES.get(heir_id, [heir_id])
        lines = own_lines(memory, aliases)
        if len(lines) < 5:
            print(f"  ! {heir_id}: only {len(lines)} own lines — skipped")
            continue
        st = measure(lines)
        desc = describe(st)

        print(
            f"{heir_id:>26} | {st['n_lines']:>5} | {st['avg_words_per_line']:>6} | "
            f"{st['avg_words_per_sentence']:>6} | {st['avg_word_len']:>8} | "
            f"{st['pct_lines_ellipsis']:>5} | {st['pct_lines_question']:>4} | "
            f"{st['pct_lines_exclaim']:>4} | {st['contractions_per_100']:>13}"
        )

        if args.dry_run:
            continue

        card = json.loads(card_path.read_text(encoding="utf-8"))
        speech = card.setdefault("speech", {})
        speech["vocabulary_level"] = desc["vocabulary_level"]
        speech["sentence_structure"] = desc["sentence_structure"]
        speech["style_measured"] = desc
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\nDone.")


if __name__ == "__main__":
    main()
