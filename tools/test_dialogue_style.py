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
    python tools/test_dialogue_style.py --full --best-of 1    # EVERY canon line, single-shot
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
from tools.test_dialogue_resemblance import (  # noqa: E402
    parse_parts, acquire_lock, release_lock, SPEAKER_RE, sample_canon_lines,
    strip_reasoning,
)

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
    "CRITICAL: brevity alone is NOT the voice. Many characters speak short lines — "
    "85+ requires the character's SPECIFIC habits (its exact tics, nicknames, "
    "interjections, rhythm, word choice), not just 'short' or 'uses ellipsis'. If you "
    "could imagine ANY other Heir saying the line, it is not 85+.\n"
    "CALIBRATION (use the FULL scale — do not cluster around a few numbers):\n"
    "- A reply that could be one of the character's own canon lines (same specific "
    "tics and register) -> 85-100.\n"
    "- A short, plain reply that is GENERIC (any character could say it) -> 55-75, "
    "NEVER 85+.\n"
    "- A reply of ONLY '...' or a lone filler word is NOT a line — even if ellipsis "
    "matches the character's habit, style <= 50 and content <= 30, because the "
    "character would actually say something.\n"
    "- A reply that merely echoes a canon line verbatim without adding the "
    "character's own new line -> 30-55.\n"
    "- A verbose, formal, analytical, or robotic reply -> 10-40.\n"
    "- A flowery, poetic, or eloquent reply -> 10-30.\n"
    "FEW-SHOT (a terse Heir whose canon is: \"...\", \"Pet.\", \"Here. Here!\"):\n"
    "- Reply \"...\" -> style 45, content 25 (a bare ellipsis is not a line).\n"
    "- Reply \"Okay, let's go.\" -> style 65, content 60 (short and plausible, but "
    "generic — any Heir could say it).\n"
    "- Reply \"Pet. Here, pet — come here!\" -> style 92, content 75 (same tics and "
    "rhythm, new content).\n"
    "- Reply \"The stars align to guide our fated steps through this boundless "
    "dream...\" -> style 18, content 55 (flowery).\n"
    "ELOQUENCE IS NOT A VIRTUE: a reply that is polished, elegant, or beautiful but "
    "does NOT sound like {name} scores LOW on style. Similarity to the character's "
    "real delivery is the ONLY thing that matters. If the reply is more eloquent "
    "than the character ever is, it FAILS style no matter how nice it reads. Judge "
    "plainness and roughness too — many canon lines are plain, fragmentary, or "
    "rough, and a pretty line is a miss, not a hit.\n"
    "KNOWLEDGE BOUNDARIES: the character lives in Amphoreus, a Titan-ruled "
    "fantasy world, and knows ONLY what someone of that world could know. If the "
    "MODEL reply displays knowledge that person could not have — modern "
    "mathematics or science (e.g. pseudo-differential operators), Earth, modern "
    "technology, real-world places, people or history — then it is NOT something "
    "this character would say: score CONTENT <= 40 and STYLE <= 50. A pass "
    "requires the reply to stay inside the character's own world.\n"
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


def is_degenerate(text: str) -> bool:
    """True for a blank or punctuation/ellipsis-only 'reply' ('...').
    A line made of only ellipsis is NOT a reply — the character would say
    something. Rejecting these at generation keeps the '...' collapse from
    ever being submitted for judging (which scored 45/25 and poisoned both
    averages and the pass rate)."""
    t = (text or "").strip()
    if not t:
        return True
    # anything left after dropping whitespace + punctuation (unicode-safe)?
    if not re.sub(r"[\s\W_]+", "", t, flags=re.UNICODE):
        return True
    return False


def normalize_line(text: str) -> str:
    """Normalize a line for exact/partial-quote comparison: strip quotes,
    name prefixes, stage directions and punctuation; lowercase; collapse
    whitespace."""
    t = text or ""
    t = re.sub(r"^\s*\*\*[^*]+\*\*\s*:?\s*", "", t)  # **Name:** prefix
    t = re.sub(r"^\s*[*>\"'`\[\]]+\s*", "", t)          # leading markers/quotes
    t = re.sub(r"\s*[*\"'`\[\]]+\s*$", "", t)           # trailing markers/quotes
    t = re.sub(r"^[\(\[]?([^()\[\]]*)[\)\]]?\s*$", r"\1", t)  # parentheses
    t = re.sub(r"[^0-9A-Za-z' ]+", " ", t)                 # drop punctuation
    return re.sub(r"\s+", " ", t).strip().lower()


def is_quote_cheat(reply: str, canon_set) -> bool:
    """True if the reply repeats any EXISTING canon line (verbatim or as a
    substantial partial quote). Cheat-free guarantee: such replies are rejected
    and regenerated, so the model can never pass by quoting the canon."""
    nr = normalize_line(reply)
    if len(nr) < 3:
        return False
    for c in canon_set:
        nc = normalize_line(c)
        if len(nc) < 3:
            continue
        if nc == nr:
            return True
        # Partial quoting: one side substantially contained in the other.
        if len(nc) >= 8 and len(nr) >= 8 and (nc in nr or nr in nc):
            return True
    return False


# ---- Within-run anti-cheat ------------------------------------------------ #
# Besides never quoting the canon, a Heir must never pass by recycling ONE
# invented phrase in every output or leaning on a formulaic template. These
# helpers track everything the Heir has already said in this test run and
# reject any candidate that repeats it (exact, near, phrase-crutch, or — in
# small samples — the same formulaic opening every time).
_STOP = {
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "hers", "its", "our", "their", "the", "a",
    "an", "and", "or", "but", "of", "to", "in", "on", "at", "for", "with",
    "from", "by", "as", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "not", "no", "so", "if",
    "then", "than", "that", "this", "these", "those", "there", "here",
    "what", "when", "where", "who", "which", "why", "how", "all", "any",
    "some", "can", "could", "will", "would", "should", "may", "might",
    "must", "just", "like", "about", "up", "down", "out", "off", "over",
    "under", "again", "once",
}
# Interjections/softeners that are formulaic when over-used as sentence openers
# (e.g. "So, ...", "Hmm, ...") even though several are also function words.
_OPENER = {
    "so", "hmm", "hm", "ah", "oh", "well", "yes", "yeah", "no", "nah", "hey",
    "eh", "alright", "okay", "ok", "fine", "right", "sure", "look", "listen",
    "aha", "huh", "um", "uh",
}


def _norm_tokens(text: str) -> list:
    return normalize_line(text).split()


def is_run_repeat(candidate: str, seen_lines, seen_grams, seen_firsts, n_seen,
                  jac_thresh=0.75, gram_hits=4, first_hits=3, lenient=False) -> bool:
    """True if the candidate cheats against THIS Heir's own run so far:
    1. exact repeat of an earlier accepted reply (always a cheat);
    2. near-duplicate (Jaccard >= jac_thresh) — cycling runs only;
    3. contains a distinctive 3-gram (>=2 content words) already used in
       >= gram_hits accepted lines — the 'same phrase in every output' crutch;
    4. (cycling runs only, n_seen <= 12) opens with the same word as
       >= first_hits earlier replies — a formulaic template.
    lenient=True (full-corpus final): skip near-duplicate + formulaic-opening,
    and require twice as many phrase hits — natural repetition is expected
    across a 1000+ line corpus, but exact repeats and heavy crutches still
    fail."""
    words = _norm_tokens(candidate)
    if not words:
        return False
    cnorm = " ".join(words)
    cset = set(words)
    for prev in seen_lines:
        pwords = _norm_tokens(prev)
        if not pwords:
            continue
        if " ".join(pwords) == cnorm:
            return True  # exact repeat
        if not lenient:
            pset = set(pwords)
            inter = len(cset & pset)
            if inter / len(cset | pset) >= jac_thresh:
                return True  # near-repeat
    hits = gram_hits * 2 if lenient else gram_hits
    if len(words) >= 3:
        for i in range(len(words) - 2):
            gram = tuple(words[i:i + 3])
            if sum(1 for w in gram if w not in _STOP) >= 2 and seen_grams.get(gram, 0) >= hits:
                return True  # over-used distinctive phrase
    if (not lenient and n_seen <= 12
            and (words[0] not in _STOP or words[0] in _OPENER)
            and seen_firsts.get(words[0], 0) >= first_hits):
        return True  # formulaic opening
    return False


def record_accepted(line: str, seen_lines, seen_grams, seen_firsts) -> None:
    """Remember an accepted reply so later cases cannot recycle it."""
    seen_lines.append(line)
    words = _norm_tokens(line)
    if not words:
        return
    seen_firsts[words[0]] = seen_firsts.get(words[0], 0) + 1
    if len(words) >= 3:
        grams = set()
        for i in range(len(words) - 2):
            gram = tuple(words[i:i + 3])
            if sum(1 for w in gram if w not in _STOP) >= 2:
                grams.add(gram)
        for g in grams:
            seen_grams[g] = seen_grams.get(g, 0) + 1


def judge_style(llm, heir_name, ctx, canon_lines, actual, stats=None, prior_used=None):
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
    if prior_used:
        used = "\n".join(f'- "{u}"' for u in prior_used[-8:])
        user += (
            f"\n\n{heir_name} has ALREADY said these lines earlier in this same "
            f"conversation:\n{used}\nIf the MODEL reply repeats one of them or "
            f"recycles their key phrases, score STYLE LOW — repeating the same "
            f"phrase in every reply is formulaic and out of character in a real "
            f"dialogue."
        )
    reply = llm.chat(
        [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}],
        temperature=0.0,
        max_tokens=360,
    )
    return extract_json(reply)


def build_cases(heir_id, limit, full=False):
    """Return cases: (ctx, anchor_lines, target_line).

    full=True: evaluate EVERY testable canon line (no even sampling down to
    `limit`). Lines that lack 2 preceding dialogue lines or any own-line anchor
    are still excluded (they cannot be tested).
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
    if full or len(cases) <= limit:
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
    ap.add_argument("--judge-model", default=None,
                    help="model for the judge (defaults to --model); e.g. a "
                         "stronger model like deepseek-r1-distill:32b")
    ap.add_argument("--temp", type=float, default=0.2)
    ap.add_argument("--best-of", type=int, default=3,
                    help="generate N candidate replies and let the character pick "
                         "the most in-voice one (reduces variance; no answer leaked)")
    ap.add_argument("--full", action="store_true",
                    help="evaluate EVERY canon line of each Heir (no even sampling "
                         "down to --limit). Use with --best-of 1 for a single-shot "
                         "full-corpus measurement.")
    ap.add_argument("--no-anti-cheat", action="store_true",
                    help="disable the within-run anti-cheat filter (exact/near "
                         "repeat, phrase-crutch, formulaic opening). Default: ON — "
                         "a Heir can never pass by recycling one phrase in every "
                         "output or by quoting the canon.")
    args = ap.parse_args()
    args.anti_cheat = not args.no_anti_cheat

    if not acquire_lock():
        return 0
    try:
        return _run(args)
    finally:
        release_lock()


def _run(args):
    heir_ids = [h.strip() for h in args.heirs.split(",") if h.strip()] or list(HEIR_FOLDERS)
    llm = LLMClient(model=args.model)
    judge_llm = LLMClient(model=args.judge_model or args.model)
    loader = CharacterLoader(str(ROOT / "src" / "characters"))

    # Preflight: the backend must actually see the requested models. A bare
    # `ollama serve` started without OLLAMA_MODELS serves an EMPTY models dir,
    # so every chat call returns 404 "model not found" — fail once, clearly,
    # instead of spamming 404s per case.
    _known = llm.list_models()
    _needed = {args.model, args.judge_model or args.model}
    _missing = sorted(m for m in _needed if m not in _known)
    if _missing:
        print(f"✗ MODEL(S) NOT FOUND by the backend: {_missing}")
        print(f"  The Ollama server is probably serving an empty/wrong models dir")
        print(f"  (a bare `ollama serve` ignores OLLAMA_MODELS).")
        print(f"  Fix:  powershell -ExecutionPolicy Bypass -File tools\\start_ollama.ps1")
        print(f"  (sets OLLAMA_MODELS=D:\\Workspace\\Amphoreus\\models\\ollama)")
        return 1
    print(f"  backend sees all required models: {sorted(_needed)}")

    print(f"STYLE standard — model {args.model}, pass = style ≥ {args.style_bar} "
          f"AND content ≥ {args.content_bar}")
    print(f"Anti-cheat: {'ON (no canon quote, no repeated line, no phrase-crutch, no formulaic opening)' if args.anti_cheat else 'OFF'}\n")

    report = [
        "# Dialogue-Style Report (the Heir-voice standard)",
        "",
        f"*Generated: 2026-08-10 · model `{args.model}`*",
        f"*Cases: {'FULL corpus — every canon line' if args.full else f'even sample (limit {args.limit})'} · best-of {args.best_of} · temp {args.temp}*",
        f"*Anti-cheat: {'ON — no canon quoting, no repeated line, no phrase-crutch, no formulaic opening' if args.anti_cheat else 'OFF'}*",
        "",
        "Criteria: **STYLE & INTONATION ≥ 85** (word choice, sentence length, rhythm, "
        "emotional register, verbal tics) and **CONTENT ≥ 60** (general gist fits the "
        "scene, judged holistically — not sentence by sentence). Pass = both bars met.",
        "",
        "| Heir | cases | pass | avg style | avg content | pass rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    backend_dead = False  # set when a Heir had cases but evaluated ZERO of them
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
        # sampled evenly across the whole corpus so they span scenes/moods;
        # richer than refinement.evidence, which is tiny for several Heirs).
        exemplars = []
        try:
            aliases = CHARACTER_ALIASES.get(heir_id, [heir_id])
            wpl = (stats.get("avg_words_per_line") or 14)
            max_words = max(12, int(wpl * 1.6))
            exemplars = sample_canon_lines(folder, aliases, 6, max_words=max_words)
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
            "own register.\n"
            "6. Never quote or repeat a canon line above verbatim — say something new "
            "in the same voice.\n"
            "7. NO beautiful rhetoric: no elegant flourishes, no polished aphorisms, "
            "no poetic imagery. Write the plain, real line the character would say — "
            "even if it is rough or awkward. Plain over pretty, always.\n"
            "8. NEVER lean on a single motif, object, or catchphrase as a crutch "
            "(e.g. 'the golden thread', 'Snowy~', 'the threads of fate'). Say a "
            "fresh, specific line in the character's true voice — not another "
            "variation of the same image.\n"
            "9. NEVER repeat yourself: do not say the same line twice, do not "
            "recycle a phrase you already used, and do not open every reply the "
            "same way — say something fresh each time.\n"
            "10. KNOWLEDGE BOUNDARIES: you know only Amphoreus — its Titans, "
            "city-states, alchemy and Coreflames. You have never heard of the "
            "modern world, Earth, modern science, modern mathematics, or modern "
            "machines. Never display such knowledge; if a visitor mentions it, "
            "you do not understand it and do not echo their words.\n"
            "11. NEVER reply with a bare '...' — an ellipsis may END a line, but "
            "a line that is ONLY '...' (or a lone filler) is not an answer. The "
            "character would say at least a few real words, even if terse."
        )

        cases = build_cases(heir_id, args.limit, full=args.full)
        # The full set of EXISTING canon lines for this Heir (from its own
        # memories) — the model may never quote any of them verbatim.
        try:
            aliases = CHARACTER_ALIASES.get(heir_id, [heir_id])
            canon_all = set(sample_canon_lines(folder, aliases, 300, max_words=60))
        except Exception:
            canon_all = set()
        passed, total = 0, 0
        styles, contents, fails = [], [], []
        # Within-run anti-cheat state: this Heir may never emit the same line
        # twice, reuse a distinctive phrase as a crutch, or (in small samples)
        # open every reply the same way.
        run_seen, run_grams, run_firsts = [], {}, {}
        for ctx, anchors, target in cases:
            anchor_block = "\n".join(f'- "{a}"' for a in anchors[:10])
            user = (
                f"{ctx}\n\n"
                f"These are YOUR OWN canon lines — the way you actually speak. Your "
                f"reply MUST sound like one of them: same brevity, same rhythm, same "
                f"manner, same mood. When in doubt, make it SHORTER and plainer than "
                f"you feel like writing — a fragment, a word, an exclamation is ideal. "
                f"Do not write a full sentence if a few words capture it. Do not "
                f"explain, do not moralise, do not philosophise. Never quote one of "
                f"the canon lines above verbatim — say something new that still sounds "
                f"like you. Do not be eloquent: write the plain, real line the "
                f"character would say, even if it is rough or awkward. Never lean on "
                f"a single motif or catchphrase as a crutch — say a fresh, specific "
                f"line. Do not repeat a line or opening you have already said in "
                f"this conversation. Never answer with a bare '...' or silence — "
                f"say at least a few real words, even if terse.\n"
                f"{anchor_block}\n\n"
                f"Say the next thing you would say here, in your canon voice:"
            )
            try:
                # best-of-N: generate candidates, let the character pick the most
                # in-voice one (legitimate — the character chooses how to speak;
                # no answer leaked, anchors exclude the target).
                # CHEAT-FREE (two independent guarantees):
                #  (1) never quote an EXISTING canon line (verbatim or partial);
                #  (2) never recycle the Heir's OWN earlier replies in this run
                #      (exact/near repeat, phrase-crutch, formulaic opening).
                # Any such candidate is rejected and regenerated, so neither the
                # canon nor a self-invented catchphrase can be used to pass.
                cheat_set = canon_all | set(anchors) | set(exemplars)
                candidates = []
                tries = 0
                need = max(1, args.best_of)
                budget = need * 6
                while len(candidates) < need:
                    tries += 1
                    # Soft cap: stop once the budget is spent and we already
                    # have at least one real candidate. If the model is STUCK
                    # on '...' (rejected as degenerate), keep giving it room up
                    # to 2x the budget so it can still produce a real line.
                    if tries > budget and (tries > budget * 2 or candidates):
                        break
                    r = llm.chat(
                        [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
                        temperature=args.temp, max_tokens=120,
                    ).strip()
                    # Reasoning models (e.g. deepseek-r1-distill) emit a
                    # <think> block before the line — strip it so only the
                    # spoken reply is judged.
                    r = strip_reasoning(r)
                    r = _trim_to_short(r)
                    # Never let a blank or a bare '...' become a candidate —
                    # a line of only ellipsis is not a reply.
                    if (r and not is_degenerate(r)
                            and not is_quote_cheat(r, cheat_set)
                            and not (args.anti_cheat and is_run_repeat(
                                r, run_seen, run_grams, run_firsts, len(run_seen),
                                lenient=args.full))):
                        candidates.append(r)
                if not candidates:
                    candidates = ["..."]  # absolute last resort — judged low
                actual = _pick_most_in_voice(llm, system, name, candidates)
                # Safety nets: never judge a canon quote, and never let the Heir
                # repeat its own earlier lines from this run.
                if is_quote_cheat(actual, cheat_set) or (
                        args.anti_cheat and is_run_repeat(
                            actual, run_seen, run_grams, run_firsts, len(run_seen),
                            lenient=args.full)):
                    ok_c = [c for c in candidates
                            if not is_quote_cheat(c, cheat_set)
                            and not (args.anti_cheat and is_run_repeat(
                                c, run_seen, run_grams, run_firsts, len(run_seen),
                                lenient=args.full))]
                    actual = ok_c[0] if ok_c else "..."
            except Exception as e:
                print(f"  {heir_id}: LLM error {e}")
                continue
            if not actual:
                continue
            # Judge against the whole voice (anchors + target as content reference).
            # The judge also sees what the Heir already said in this run, so any
            # recycled phrase that slips through the filter still scores LOW.
            voice_ref = anchors + [target]
            prior_used = run_seen if (args.anti_cheat and len(run_seen) <= 12) else None
            try:
                j = judge_style(judge_llm, name, ctx, voice_ref, actual,
                                stats=stats, prior_used=prior_used)
                st = int(j.get("style", 0))
                ct = int(j.get("content", 0))
            except Exception:
                st, ct = 0, 0
            # Remember this accepted reply — it cannot be recycled later in the run.
            if args.anti_cheat:
                record_accepted(actual, run_seen, run_grams, run_firsts)
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
        # A Heir that HAD testable cases but evaluated ZERO of them means every
        # LLM call failed — the backend is down. Never record that as a score.
        if total == 0 and cases:
            backend_dead = True
            print(f"  ✗ {heir_id}: 0/{len(cases)} cases evaluated — every LLM call failed. "
                  f"The backend is DOWN.")
        report.append(
            f"| {name} ({heir_id}) | {total} | {passed} | {avg_s:.0f} | {avg_c:.0f} | {rate} |"
        )
        if fails:
            report.append("")
            report.append(f"**{name}** — failed cases (style/content):")
            for st, ct, ref, act in fails[:4]:
                report.append(f"- style {st} / content {ct} → canon ref *{ref}* → act *{act}*")

    if backend_dead:
        report.append("")
        report.append("**ERROR: the LLM backend was DOWN (0 cases evaluated). This run is VOID.**")
        report.append("Fix: powershell -ExecutionPolicy Bypass -File tools\\start_ollama.ps1, then re-run.")
        REPORT.write_text("\n".join(report), encoding="utf-8")
        print("\n✗ ABORTING: the LLM backend failed (0 cases evaluated). Run is VOID.")
        return 2

    REPORT.write_text("\n".join(report), encoding="utf-8")
    print(f"\nReport: {REPORT}")


if __name__ == "__main__":
    main()
