"""
refine_personal_traits.py — let the LLM read each Heir's canon dialogue
(personal-memories.md) and refine their personal traits to a deeper level.

WHAT IT DOES
------------
For every Chrysos Heir:
  1. Reads their personal memories — the canon dialogue copied from the
     databank into <HeirFolder>/personal-memories.md (sampled within the
     context window, the Heir's own lines always kept).
  2. Sends that dialogue + their current personality/speech profile to the
     local LLM (Ollama, default qwen2.5:14b-instruct) with a strict rule:
     derive EVERYTHING only from the dialogue — never invent — and quote
     exact lines as evidence.
  3. Applies the refined profile back:
       * src/characters/<id>.json      -> personality + speech sections,
                                          plus a "refinement" block with the
                                          evidence quotes (this IS tracked in git).
       * <HeirFolder>/preferences.json -> refined likes/dislikes/tastes/
                                          places/values merged in, plus the raw
                                          block under "refined_from_dialogue"
                                          (runtime file, gitignored).
  4. Backs up every card it changes to .cache/refine-backups/ first.

USAGE
-----
    python tools/refine_personal_traits.py                  # all 13 Heirs
    python tools/refine_personal_traits.py --heirs phainon,aglaea
    python tools/refine_personal_traits.py --dry-run        # analyse, change nothing
    python tools/refine_personal_traits.py --model qwen2.5:14b-instruct

The Ollama server must be running (tools/start_ollama.ps1).
"""

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.heir_folders import HEIR_FOLDERS  # noqa: E402
from src.knowledge.kb_builder import CHARACTER_ALIASES  # noqa: E402

CARDS_DIR = ROOT / "src" / "characters"
BACKUP_DIR = ROOT / ".cache" / "refine-backups"
PREFERENCES_FILE = "preferences.json"

SPEAKER_RE = re.compile(r"^\s*>?\s*\*\*(.+?):\*\*\s*(.*)$")
PART_SPLIT_RE = re.compile(r"(?=^### Part \d+)", re.M)

_QUOTE_MAP = {
    "\u201c": '"', "\u201d": '"',
    "\u2018": "'", "\u2019": "'",
    "\u2013": "-", "\u2014": "-",
    "\u00a0": " ", "\u200b": "", "\ufeff": "",
}


def normalize_for_check(text: str) -> str:
    """Light normalisation for verbatim checks: emphasis markers, a wrapping
    quote pair, blockquote '> ' prefixes, curly/straight quote styles, dashes,
    whitespace."""
    t = re.sub(r"\*\*", "", text)
    t = re.sub(r"\*", "", t)
    for src, dst in _QUOTE_MAP.items():
        t = t.replace(src, dst)
    t = t.replace('"', "'")                      # unify quote style (canon uses "…")
    t = re.sub(r"^'(.*)'$", r"\1", t.strip())    # unwrap a whole-quote wrapping pair FIRST
    t = re.sub(r"(?m)^\s*>\s*", "", t)           # then strip markdown blockquote markers
    return re.sub(r"\s+", " ", t).strip()

PERSONALITY_KEYS = ("temperament", "emotional_range", "moral_alignment", "hamartia")
SPEECH_TEXT_KEYS = ("formality", "vocabulary_level", "tone", "sentence_structure")
SPEECH_LIST_KEYS = ("verbal_tics", "catchphrases")
PREFERENCE_KEYS = ("likes", "dislikes", "tastes", "places", "values")


# --------------------------------------------------------------------------
# Sampling the canon dialogue
# --------------------------------------------------------------------------

def is_own_line(line: str, aliases) -> bool:
    m = SPEAKER_RE.match(line)
    if not m:
        return False
    s = m.group(1).lower()
    return any(a.lower() in s for a in aliases)


def build_digest(path: Path, aliases, max_chars: int) -> str:
    """Sample personal-memories.md for the LLM: the Heir's own lines first,
    then surrounding context, spread evenly across the whole story, within
    max_chars. Returns the raw dialogue lines (speaker labels intact)."""
    raw = path.read_text(encoding="utf-8")
    segments = [s.strip() for s in PART_SPLIT_RE.split(raw) if s.strip()]

    own_per = []
    for seg in segments:
        own_per.append(sum(1 for ln in seg.splitlines() if is_own_line(ln, aliases)))

    total_own = sum(own_per)
    # How many parts we can afford so the Heir's own lines fit the budget.
    avg_own = total_own / max(1, len(segments))
    target_parts = max(1, int((max_chars * 0.7) / max(1, avg_own)))
    target_parts = min(target_parts, len(segments))
    step = max(1, len(segments) // target_parts)

    selected_idx = list(range(0, len(segments), step))
    if len(selected_idx) < target_parts and len(segments) - 1 not in selected_idx:
        selected_idx.append(len(segments) - 1)  # keep the story's later beats

    blocks = []
    used = 0
    for i in selected_idx:
        if used >= max_chars:
            break
        lines = seg_lines = segments[i].splitlines()
        own = [ln for ln in seg_lines if is_own_line(ln, aliases)]
        other = [ln for ln in seg_lines if ln not in own]
        pick = list(own)
        for ln in other:
            if sum(len(x) + 1 for x in pick) + len(ln) + 1 > max_chars - used:
                break
            pick.append(ln)
        block = "\n".join(pick)
        if used + len(block) > max_chars:
            block = block[: max_chars - used]
        blocks.append(block)
        used += len(block) + 1
    return "\n\n".join(b for b in blocks if b)


# --------------------------------------------------------------------------
# Ollama native API (honours options.num_ctx; the /v1 OpenAI-compat endpoint
# ignores it and stays at the server's small default context)
# --------------------------------------------------------------------------

OLLAMA_BASE = "http://127.0.0.1:11434"


def ollama_models(base_url: str = OLLAMA_BASE) -> set:
    """Names of models currently visible to the Ollama server."""
    with urllib.request.urlopen(base_url.rstrip("/") + "/api/tags", timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    return {m.get("name", "") for m in data.get("models", [])}


def ollama_chat(model: str, messages: list, num_ctx: int, temperature: float,
                max_tokens: int, base_url: str = OLLAMA_BASE) -> str:
    """Call Ollama's native /api/chat with options.num_ctx."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"num_ctx": num_ctx, "temperature": temperature},
    }
    if max_tokens:
        payload["options"]["num_predict"] = max_tokens
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=1800) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data["message"]["content"]


# --------------------------------------------------------------------------
# LLM call + JSON parsing
# --------------------------------------------------------------------------

def extract_json(text: str) -> dict:
    """Robustly pull a JSON object out of a model reply (handles ``` fences
    and stray prose around the object)."""
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1)
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in model reply")
    return json.loads(t[start:end + 1])


def build_prompt(heir_id: str, card: dict, digest: str) -> list:
    identity = card.get("identity", {})
    name = identity.get("name", heir_id)
    true_name = identity.get("true_name", "")
    titles = ", ".join(identity.get("titles", [])) or heir_id

    current = {
        "personality": card.get("personality", {}),
        "speech": card.get("speech", {}),
    }
    system = (
        "You are a meticulous literary analyst working for an AI character sanctuary. "
        "Your task is to refine a character's personality profile so it faithfully matches "
        "their canon dialogue. Rules:\n"
        "1. Derive EVERYTHING strictly from the dialogue provided. Never invent facts, "
        "events, or traits that the dialogue does not support.\n"
        "2. Preserve the character's identity (name, titles, background) — you only refine "
        "how their personality and speech are described.\n"
        "3. Quote exact dialogue lines as evidence.\n"
        "4. Respond with a single valid JSON object and nothing else."
    )
    user = f"""Character: {name} (true name: {true_name}). Titles: {titles}.

CURRENT PROFILE (from the character card — refine, do not contradict facts):
{json.dumps(current, ensure_ascii=False, indent=2)}

CANON DIALOGUE (sampled from their personal memories):
{digest}

Output ONLY a JSON object with this exact schema:
{{
  "personality": {{
    "traits": ["trait1", "trait2", ...],
    "temperament": "...",
    "emotional_range": "...",
    "moral_alignment": "...",
    "hamartia": "..."
  }},
  "speech": {{
    "formality": "...",
    "vocabulary_level": "...",
    "verbal_tics": ["...", ...],
    "tone": "...",
    "sentence_structure": "...",
    "catchphrases": ["...", ...]
  }},
  "preferences": {{
    "likes": ["...", ...],
    "dislikes": ["...", ...],
    "tastes": ["...", ...],
    "places": ["...", ...],
    "values": ["...", ...]
  }},
  "evidence": ["exact quote 1", "exact quote 2", ...]
}}
"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def refine_with_llm(model: str, num_ctx: int, heir_id: str, card: dict, digest: str) -> dict:
    messages = build_prompt(heir_id, card, digest)
    reply = ollama_chat(model, messages, num_ctx, 0.4, 2400)
    try:
        return extract_json(reply)
    except (ValueError, json.JSONDecodeError):
        # one stricter retry
        messages = messages + [
            {"role": "assistant", "content": reply[:4000]},
            {"role": "user", "content": "That was not valid JSON. Output ONLY the JSON object, no prose, no markdown fences."},
        ]
        reply2 = ollama_chat(model, messages, num_ctx, 0.2, 2400)
        return extract_json(reply2)


# --------------------------------------------------------------------------
# Applying the refinement
# --------------------------------------------------------------------------

def _clean_str_list(items) -> list:
    out = []
    for it in items:
        s = str(it).strip().strip('"')
        if s and s not in out:
            out.append(s)
    return out


def apply_to_card(card: dict, refined: dict, model: str) -> dict:
    """Mutate and return the card with the refined personality/speech + evidence."""
    p = refined.get("personality") or {}
    if isinstance(p, dict):
        pers = card.setdefault("personality", {})
        traits = p.get("traits")
        if isinstance(traits, list) and traits:
            pers["traits"] = _clean_str_list(traits)
        for k in PERSONALITY_KEYS:
            v = p.get(k)
            if isinstance(v, str) and v.strip():
                pers[k] = v.strip()

    s = refined.get("speech") or {}
    if isinstance(s, dict):
        sp = card.setdefault("speech", {})
        for k in SPEECH_TEXT_KEYS:
            v = s.get(k)
            if isinstance(v, str) and v.strip():
                sp[k] = v.strip()
        for k in SPEECH_LIST_KEYS:
            v = s.get(k)
            if isinstance(v, list) and v:
                sp[k] = _clean_str_list(v)

    ref = card.setdefault("refinement", {})
    ev = refined.get("evidence")
    if isinstance(ev, list) and ev:
        ref["evidence"] = _clean_str_list(ev)
    ref["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ref["model"] = model
    ref["method"] = "LLM refined from personal-memories.md (canon dialogue); evidence quotes verbatim"
    return card


def apply_to_preferences(prefs_path: Path, refined: dict):
    """Merge dialogue-derived preferences into the Heir's preferences.json."""
    prefs = {}
    if prefs_path.exists():
        try:
            prefs = json.loads(prefs_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            prefs = {}
    rp = refined.get("preferences") or {}
    if isinstance(rp, dict):
        for k in PREFERENCE_KEYS:
            v = rp.get(k)
            if isinstance(v, list) and v:
                merged = _clean_str_list(v)
                for old in prefs.get(k, []):
                    if old not in merged:
                        merged.append(old)
                prefs[k] = merged
        prefs.setdefault("refined_from_dialogue", {})[datetime.now(timezone.utc).strftime("%Y-%m-%d")] = {
            k: _clean_str_list(rp[k]) for k in PREFERENCE_KEYS
            if isinstance(rp.get(k), list) and rp[k]
        }
    prefs_path.parent.mkdir(parents=True, exist_ok=True)
    prefs_path.write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8")


def _strip_speaker_label(q: str):
    """Strip a leading 'Speaker:' label from a normalised quote, if present."""
    m = re.match(r"^[A-Za-z\u00c0-\u024f][^:]{0,30}?:\s*(.*)$", q, re.S)
    return m.group(1) if m else None


def verify_evidence(heir_id: str, card: dict, memory_path: Path):
    """Check every refinement.evidence quote appears verbatim in the canon.
    A quote counts as verbatim if its text (with or without the leading
    'Speaker:' label) is a substring of the canon. Returns [(quote, ok)]."""
    ev = (card.get("refinement") or {}).get("evidence") or []
    raw = memory_path.read_text(encoding="utf-8")
    norm_mem = normalize_for_check(raw)
    results = []
    for q in ev:
        nq = normalize_for_check(q)
        ok = nq in norm_mem
        if not ok:
            rest = _strip_speaker_label(nq)
            if rest and rest in norm_mem:
                ok = True
        results.append((q, ok))
    return results


def run_verification(heir_ids, dry_run: bool) -> int:
    """--verify mode: report evidence fidelity without touching anything."""
    total = ok = 0
    failed_heirs = []
    for heir_id in heir_ids:
        folder = ROOT / HEIR_FOLDERS.get(heir_id, heir_id)
        card_path = CARDS_DIR / f"{heir_id}.json"
        memory = folder / "personal-memories.md"
        if not card_path.exists() or not memory.exists():
            print(f"  ! {heir_id}: missing card/memory")
            continue
        card = json.loads(card_path.read_text(encoding="utf-8"))
        results = verify_evidence(heir_id, card, memory)
        n, k = len(results), sum(1 for _, okk in results if okk)
        total += n
        ok += k
        flag = "OK" if k == n and n else "MISMATCH"
        print(f"  {heir_id:>26}: {k}/{n} evidence quotes verbatim  [{flag}]")
        for q, okk in results:
            if not okk:
                print(f"      ! NOT FOUND: {q[:120]}")
        if k != n:
            failed_heirs.append(heir_id)
    print(f"\nEvidence fidelity: {ok}/{total} verbatim")
    return 1 if failed_heirs else 0


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="LLM-refine Heir traits from their canon dialogue.")
    ap.add_argument("--heirs", default="", help="comma-separated character ids (default: all)")
    ap.add_argument("--model", default="qwen2.5:14b-instruct", help="Ollama model (default qwen2.5:14b-instruct)")
    ap.add_argument("--num-ctx", type=int, default=32768, help="request context window (default 32768)")
    ap.add_argument("--max-chars", type=int, default=30000, help="dialogue budget fed to the LLM (default 30000)")
    ap.add_argument("--dry-run", action="store_true", help="analyse and report only, write nothing")
    ap.add_argument("--verify", action="store_true", help="check evidence quotes verbatim against canon, write nothing")
    ap.add_argument("--max-tokens", type=int, default=2400, help="LLM reply budget")
    args = ap.parse_args()

    heir_ids = [h.strip() for h in args.heirs.split(",") if h.strip()] or list(HEIR_FOLDERS)

    if args.verify:
        print(f"Verifying evidence quotes verbatim against canon ({len(heir_ids)} Heirs)\n")
        return run_verification(heir_ids, args.dry_run)

    try:
        models = ollama_models()
    except Exception as err:
        print(f"Ollama is not reachable at {OLLAMA_BASE}: {err}")
        print("Start the server with: powershell -File tools/start_ollama.ps1")
        return 1
    if args.model not in models:
        print(f"Model '{args.model}' not found. Available: {sorted(models)}")
        return 1

    print(f"Refining {len(heir_ids)} Heirs with {args.model}"
          f"{' (DRY RUN — nothing will be written)' if args.dry_run else ''}\n")

    for heir_id in heir_ids:
        folder = ROOT / HEIR_FOLDERS.get(heir_id, heir_id)
        memory = folder / "personal-memories.md"
        card_path = CARDS_DIR / f"{heir_id}.json"
        if not memory.exists() or not card_path.exists():
            print(f"  ! {heir_id}: missing memory/card — skipped")
            continue

        aliases = CHARACTER_ALIASES.get(heir_id, [heir_id])
        digest = build_digest(memory, aliases, args.max_chars)
        card = json.loads(card_path.read_text(encoding="utf-8"))

        print(f"  {heir_id:>26}: analysing {len(digest):,} chars of canon dialogue ...")
        try:
            refined = refine_with_llm(args.model, args.num_ctx, heir_id, card, digest)
        except Exception as err:
            print(f"  {heir_id:>26}: FAILED — {err}")
            continue

        traits = (refined.get("personality") or {}).get("traits") or []
        ev = refined.get("evidence") or []
        print(f"  {heir_id:>26}: traits {len(traits)} | evidence {len(ev)}")

        if args.dry_run:
            continue

        # backup the original card, then write the refined one
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup = BACKUP_DIR / f"{heir_id}-{stamp}.json"
        backup.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")

        apply_to_card(card, refined, args.model)
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        apply_to_preferences(folder / PREFERENCES_FILE, refined)
        print(f"  {heir_id:>26}: updated {card_path.relative_to(ROOT)} + {PREFERENCES_FILE}")

    print("\nDone.")


if __name__ == "__main__":
    raise SystemExit(main())
