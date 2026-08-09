"""
audit_card_quotes.py — deterministic fallacy check.

Extracts every quoted claim ("…") from each Heir's card and verifies it
verbatim against the canon databank (personal-memories + databank/**/*.md).
Anything NOT found is a candidate fallacy — either a misquote or a claim with
no canon support — and is listed for manual review. No LLM involved, so this
is exact.

USAGE:
    python tools/audit_card_quotes.py            # all Heirs
    python tools/audit_card_quotes.py --heirs phainon
    python tools/audit_card_quotes.py --min-len 16
"""

import argparse
import json
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
from tools.refine_personal_traits import normalize_for_check  # noqa: E402

QUOTE_RE = re.compile(r'"([^"\n]{12,})"')


def walk_strings(obj, path: str):
    """Yield (path, string) for every string value in a JSON tree."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def collect_quotes(card: dict, min_len: int):
    """Return [(path, quote)] of verbatim-checkable claims: embedded quoted
    fragments plus the full speech.catchphrases / speech.verbal_tics items."""
    found = []
    seen = set()
    for path, text in walk_strings(card, ""):
        if any(s in path for s in (".meta.", "rag.", "identity.", "prompts.")):
            continue
        # whole catchphrase items are canon quotes (verbal_tics are descriptive,
        # not verbatim quotes — they are NOT flagged)
        if re.search(r"speech\.catchphrases\[\d+\]$", path):
            q = text.strip()
            if len(q) >= min_len and q not in seen:
                seen.add(q)
                found.append((path, q))
            continue
        for m in QUOTE_RE.finditer(text):
            q = m.group(1).strip()
            if len(q) >= min_len and q not in seen:
                seen.add(q)
                found.append((path, q))
    return found


def build_corpus(heir_id: str) -> str:
    """Normalised canon text: personal memories + whole databank."""
    parts = []
    folder = ROOT / HEIR_FOLDERS.get(heir_id, heir_id)
    mem = folder / "personal-memories.md"
    if mem.exists():
        parts.append(mem.read_text(encoding="utf-8"))
    for p in (ROOT / "databank").rglob("*.md"):
        try:
            parts.append(p.read_text(encoding="utf-8"))
        except Exception:
            continue
    return normalize_for_check("\n".join(parts))


def check_quote(q, norm_corpus):
    nq = normalize_for_check(q)
    if nq in norm_corpus:
        return True
    m = re.match(r"^[A-Za-z\u00c0-\u024f][^:]{0,30}?:\s*(.*)$", nq, re.S)
    if m and m.group(1) in norm_corpus:
        return True
    return False


def main():
    ap = argparse.ArgumentParser(description="Deterministic card-vs-canon quote audit.")
    ap.add_argument("--heirs", default="")
    ap.add_argument("--min-len", type=int, default=16, help="min quote length to check")
    args = ap.parse_args()

    heir_ids = [h.strip() for h in args.heirs.split(",") if h.strip()] or list(HEIR_FOLDERS)

    grand_total = grand_found = 0
    for heir_id in heir_ids:
        card_path = ROOT / "src" / "characters" / f"{heir_id}.json"
        if not card_path.exists():
            continue
        card = json.loads(card_path.read_text(encoding="utf-8"))
        quotes = collect_quotes(card, args.min_len)
        corpus = build_corpus(heir_id)
        missing = []
        for path, q in quotes:
            if check_quote(q, corpus):
                grand_found += 1
            else:
                missing.append((path, q))
            grand_total += 1
        print(f"  {heir_id:>26}: {len(quotes)} quoted claims, {len(missing)} not found in canon")
        for path, q in missing:
            print(f"      ! [{path}] \"{q[:110]}\"")
    print(f"\nTOTAL: {grand_found}/{grand_total} quoted claims found verbatim in canon")


if __name__ == "__main__":
    main()
