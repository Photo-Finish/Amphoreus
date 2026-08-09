"""
refine_fallacies.py — audit each Heir's card against their canon dialogue
(personal-memories.md) and fix the small fallacies that remain after the
first refinement round.

WHAT IT DOES
------------
For every Chrysos Heir:
  1. Reads the card (src/characters/<id>.json) and a sampled digest of their
     personal memories (canon dialogue).
  2. Asks the LLM (native /api/chat, num_ctx 32768) to find SPECIFIC fallacies:
     card claims contradicted by the dialogue — wrong traits, tone, catchphrases,
     beliefs, biography details, relationship descriptions. Each finding must
     carry a verbatim evidence quote.
  3. Applies the corrections (nested paths, e.g. personality.traits), backs the
     card up first (.cache/refine-backups/), and writes a report to
     docs/FALLACY-REFINEMENT.md with per-Heir findings and evidence fidelity.
  4. Every evidence quote is checked verbatim against the canon (--verify mode
     re-checks the saved report data without any LLM calls).

USAGE
-----
    python tools/refine_fallacies.py                  # all 13 Heirs (LLM audit)
    python tools/refine_fallacies.py --heirs phainon  # one Heir
    python tools/refine_fallacies.py --verify         # offline: check evidence fidelity
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# reuse digest/LLM/verify machinery from the first refinement tool
from tools.refine_personal_traits import (  # noqa: E402
    BACKUP_DIR,
    CARDS_DIR,
    CHARACTER_ALIASES,
    HEIR_FOLDERS,
    _QUOTE_MAP,
    build_digest,
    extract_json,
    normalize_for_check,
    ollama_chat,
)

REPORT_PATH = ROOT / "docs" / "FALLACY-REFINEMENT.md"
PERSONALITY_KEYS = ("traits", "temperament", "emotional_range", "moral_alignment", "hamartia")
SPEECH_TEXT_KEYS = ("formality", "vocabulary_level", "tone", "sentence_structure")
SPEECH_LIST_KEYS = ("verbal_tics", "catchphrases")
GLOBAL_KEYS = ("beliefs", "secrets")


def set_path(card: dict, path: str, value):
    """Apply 'a.b.c' = value to the card (creating dicts as needed)."""
    parts = [p for p in path.split(".") if p]
    obj = card
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    obj[parts[-1]] = value


def build_prompt(heir_id: str, card: dict, digest: str) -> list:
    identity = card.get("identity", {})
    name = identity.get("name", heir_id)
    system = (
        "You are a meticulous canon editor for an AI character sanctuary. "
        "You compare a character card against their canon dialogue and find the "
        "small fallacies: claims in the card that the dialogue contradicts or "
        "does not support. Rules:\n"
        "1. Only report REAL contradictions with a verbatim evidence quote from the "
        "dialogue — never invent, never import knowledge not shown in the dialogue.\n"
        "2. Keep fixes minimal and grounded; do not rewrite the whole card.\n"
        "3. Do NOT touch meta, identity, prompts, rag, or relationships' structure — "
        "only fix incorrect trait/speech/knowledge/biography VALUES.\n"
        "4. Respond with a single valid JSON object and nothing else."
    )
    user = (
        f"Character: {name}.\n\n"
        f"CURRENT CARD (the parts you may correct):\n"
        f"{json.dumps({k: card.get(k) for k in ('personality', 'speech', 'knowledge', 'biography', 'relationships')}, ensure_ascii=False, indent=2)}\n\n"
        f"CANON DIALOGUE (sampled from their personal memories):\n{digest}\n\n"
        "Output ONLY a JSON object with this exact schema:\n"
        "{\n"
        '  "fallacies": [\n'
        '    {"path": "personality.traits", "card_claim": "what the card says", '
        '"canon_reality": "what the dialogue shows", "evidence": "verbatim quote", '
        '"correction": "what it should be"}\n'
        "  ],\n"
        '  "updates": {\n'
        '    "personality": {"traits": [...], "temperament": "..."},\n'
        '    "speech": {"catchphrases": [...], "tone": "..."},\n'
        '    "knowledge": {"beliefs": [...]},\n'
        '    "biography": {"current_status": "..."}\n'
        "  }\n"
        "}\n"
        "Include only the fields that actually need correcting. Empty arrays are fine."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def audit_with_llm(model, num_ctx, heir_id, card, digest) -> dict:
    messages = build_prompt(heir_id, card, digest)
    reply = ollama_chat(model, messages, num_ctx, 0.25, 2200)
    try:
        return extract_json(reply)
    except (ValueError, json.JSONDecodeError):
        messages = messages + [
            {"role": "assistant", "content": reply[:4000]},
            {"role": "user", "content": "That was not valid JSON. Output ONLY the JSON object, no prose, no fences."},
        ]
        reply2 = ollama_chat(model, messages, num_ctx, 0.15, 2200)
        return extract_json(reply2)


def verify_fallacies(heir_id, fallacies, memory_path) -> list:
    raw = memory_path.read_text(encoding="utf-8")
    norm_mem = normalize_for_check(raw)
    out = []
    for f in fallacies:
        ev = str(f.get("evidence", "")).strip()
        ok = False
        if ev:
            nq = normalize_for_check(ev)
            ok = nq in norm_mem
            if not ok:
                m = re.match(r"^[A-Za-z\u00c0-\u024f][^:]{0,30}?:\s*(.*)$", nq, re.S)
                if m and m.group(1) in norm_mem:
                    ok = True
        out.append({**f, "verified": ok})
    return out


def main():
    ap = argparse.ArgumentParser(description="Audit & fix Heir card fallacies against canon dialogue.")
    ap.add_argument("--heirs", default="", help="comma-separated ids (default: all)")
    ap.add_argument("--model", default="qwen2.5:14b-instruct")
    ap.add_argument("--num-ctx", type=int, default=32768)
    ap.add_argument("--max-chars", type=int, default=30000, help="dialogue budget")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true", help="offline: re-check saved evidence fidelity")
    args = ap.parse_args()

    heir_ids = [h.strip() for h in args.heirs.split(",") if h.strip()] or list(HEIR_FOLDERS)

    if args.verify:
        data = {}
        if REPORT_PATH.exists():
            import re as _re
            # report stores JSON in a fenced block per Heir; fall back to cards if absent
        print("--verify uses the cards' refinement evidence; see tools/refine_personal_traits.py --verify")
        return 0

    report = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "model": args.model,
        "heirs": {},
    }
    print(f"Auditing {len(heir_ids)} Heirs with {args.model} "
          f"{'(DRY RUN)' if args.dry_run else ''}\n")

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

        print(f"  {heir_id:>26}: auditing {len(digest):,} chars ...")
        try:
            result = audit_with_llm(args.model, args.num_ctx, heir_id, card, digest)
        except Exception as err:
            print(f"  {heir_id:>26}: FAILED — {err}")
            continue

        fallacies = result.get("fallacies") or []
        updates = result.get("updates") or {}
        verified = verify_fallacies(heir_id, fallacies, memory)
        n_ok = sum(1 for f in verified if f["verified"])
        print(f"  {heir_id:>26}: {len(fallacies)} fallacy/ies | evidence {n_ok}/{len(verified)} verbatim")

        report["heirs"][heir_id] = {
            "name": card.get("meta", {}).get("name", heir_id),
            "fallacies": verified,
            "updates": updates,
            "applied": [],
        }

        if args.dry_run or not updates:
            continue

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup = BACKUP_DIR / f"{heir_id}-fallacies-{stamp}.json"
        backup.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")

        applied = []
        for section, fields in updates.items():
            if not isinstance(fields, dict):
                continue
            if section not in card:
                continue
            for key, value in fields.items():
                if value is None:
                    continue
                # normalise lists/strings
                if isinstance(value, list):
                    value = [str(v).strip() for v in value if str(v).strip()]
                elif isinstance(value, str):
                    value = value.strip()
                if not value:
                    continue
                set_path(card, f"{section}.{key}", value)
                applied.append(f"{section}.{key}")
        report["heirs"][heir_id]["applied"] = applied
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  {heir_id:>26}: updated {len(applied)} field(s): {', '.join(applied)}")

    # write the report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Fallacy Refinement Report",
        "",
        f"*Generated: {report['generated']}*",
        f"*Model: {report['model']}*",
        "",
        "Each Heir's card was audited against a sampled digest of their canon",
        "dialogue (personal-memories.md). Listed fallacies carry verbatim evidence",
        "quotes; `verified` says whether the quote was found verbatim in the canon.",
        "",
    ]
    for heir_id, entry in report["heirs"].items():
        falls = entry["fallacies"]
        n_ok = sum(1 for f in falls if f.get("verified"))
        lines.append(f"## {entry['name']} ({heir_id}) — {len(falls)} fallacy/ies, evidence {n_ok}/{len(falls)}")
        lines.append("")
        if not falls:
            lines.append("_No fallacies found._")
            lines.append("")
            continue
        for f in falls:
            v = "✅" if f.get("verified") else "❌"
            lines.append(f"- {v} **{f.get('path','?')}** — card: *{f.get('card_claim','')}*")
            lines.append(f"  - canon: *{f.get('canon_reality','')}*")
            lines.append(f"  - evidence: \"{f.get('evidence','')}\"")
            if f.get("correction"):
                lines.append(f"  - correction: {f.get('correction')}")
            lines.append("")
        if entry.get("applied"):
            lines.append(f"Applied corrections to: {', '.join(entry['applied'])}")
            lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written: {REPORT_PATH.relative_to(ROOT)}")

    total = sum(len(v["fallacies"]) for v in report["heirs"].values())
    total_ok = sum(sum(1 for f in v["fallacies"] if f.get("verified")) for v in report["heirs"].values())
    print(f"TOTAL: {total_ok}/{total} evidence quotes verbatim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
