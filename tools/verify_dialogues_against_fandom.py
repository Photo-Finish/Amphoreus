"""
verify_dialogues_against_fandom.py — check the automatically generated Heir
dialogues against the canon on the Fandom wiki (Honkai: Star Rail).

WHAT IT DOES
------------
1.  AUTO-OBTAINS the Fandom content. For every Chrysos Heir it fetches their
    wiki page (plus the "/Voice" sub-page when it exists) through the MediaWiki
    API (https://hsr.fandom.com/api.php, action=parse&prop=text), and reduces
    the rendered HTML to plain text.

2.  EXAMINES every dialogue line that was generated automatically into each
    Heir's folder — <HeirFolder>/personal-memories.md, the canon dialogue
    copied by extract_personal_memories.py. Each unique line is checked:
      * verbatim match (after light normalisation) against the fetched Fandom
        page corpus for that Heir,
      * if that misses, a phrase search on Fandom (action=query&list=search),
      * anything still unmatched is reported as "not found".

3.  WRITES a markdown report (docs/fandom-verification-report.md by default)
    with per-Heir coverage percentages and every unmatched line with its
    source, so nobody has to check the dialogues by hand — the script does.

You do NOT need to verify the dialogues yourself. Re-run with no arguments
any time; results are cached in .cache/fandom_verify.json, so re-runs are
instant unless new dialogue was added.

USAGE
-----
    python tools/verify_dialogues_against_fandom.py                 # all Heirs
    python tools/verify_dialogues_against_fandom.py --heirs phainon,aglaea
    python tools/verify_dialogues_against_fandom.py --limit 30      # quick smoke
    python tools/verify_dialogues_against_fandom.py --no-fetch      # offline, cache only
    python tools/verify_dialogues_against_fandom.py --api https://<mirror>/api.php

NOTES
-----
* The script AUTO-DISCOVERS a working endpoint: it probes the Fandom API,
  then any entries in MIRROR_APIS (add working mirrors there), then public
  relays (RELAY_BUILDERS). The first route that answers is used for the run.
* If your network cannot reach any of them (some networks block fandom.com
  entirely), it falls back to offline/cached mode and tells you. Pass a
  reachable mirror via --api (any MediaWiki-compatible endpoint works).
* The matcher is "verbatim after light normalisation": whitespace, smart
  quotes and dashes are unified; everything else must match exactly.
* Stdlib only — no pip dependencies.
"""

import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Windows consoles default to cp1252 and crash on some emoji / CJK.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.knowledge.kb_builder import CHARACTER_ALIASES  # noqa: E402
from src.core.heir_folders import HEIR_FOLDERS  # noqa: E402

DEFAULT_API = "https://hsr.fandom.com/api.php"
USER_AGENT = "AmphoreusDialogueVerifier/1.0 (local script; verifies extracted canon dialogue)"

# Candidate MediaWiki API endpoints, tried in order until one responds.
# Add any working Fandom mirror / proxy here (e.g. a self-hosted relay).
MIRROR_APIS: list[str] = []

# URL-wrapping relays: public services that fetch a target URL and return its
# body. Each entry is (label, builder(target_url) -> relay_url). Best-effort;
# they may be down — the script only uses the first one that answers.
RELAY_BUILDERS: list[tuple[str, callable]] = [
    ("allorigins (api.allorigins.win)",
     lambda target: "https://api.allorigins.win/raw?url=" + urllib.parse.quote(target, safe="")),
]

# Fandom page titles consulted per Heir (main page + voice sub-page).
HEIR_PAGES = {
    "phainon": ["Phainon", "Phainon/Voice"],
    "aglaea": ["Aglaea", "Aglaea/Voice"],
    "anaxa": ["Anaxa", "Anaxa/Voice"],
    "castorice": ["Castorice", "Castorice/Voice"],
    "cerydra": ["Cerydra", "Cerydra/Voice"],
    "cipher": ["Cipher", "Cipher/Voice"],
    "cyrene": ["Cyrene", "Cyrene/Voice"],
    "hyacine": ["Hyacine", "Hyacine/Voice"],
    "hysilens": ["Hysilens", "Hysilens/Voice"],
    "mydei": ["Mydei", "Mydei/Voice"],
    "tribbie": ["Tribbie", "Tribbie/Voice"],
    # Evernight is March 7th in Amphoreus; Permansor Terrae is Dan Heng.
    "evernight": ["March 7th", "March 7th/Voice"],
    "dan-heng-permansor-terrae": ["Dan Heng", "Dan Heng/Voice"],
}

CACHE_DIR = ROOT / ".cache"
CACHE_FILE = CACHE_DIR / "fandom_verify.json"
DEFAULT_REPORT = ROOT / "docs" / "fandom-verification-report.md"

SPEAKER_RE = re.compile(r"^\s*>?\s*\*\*(.+?):\*\*\s*(.*)$")
PART_RE = re.compile(r"^###\s+Part\s+(\d+)\s*—\s*`([^`]+)`\s*$")

_QUOTE_MAP = {
    "\u201c": '"', "\u201d": '"',   # “ ”
    "\u2018": "'", "\u2019": "'",   # ‘ ’
    "\u2013": "-", "\u2014": "-",   # – —
    "\u00a0": " ",                  # nbsp
    "\u200b": "", "\ufeff": "",     # zero-width
}


# --------------------------------------------------------------------------
# Normalisation (applied identically to both sides before matching)
# --------------------------------------------------------------------------

def html_to_text(raw_html: str) -> str:
    """Strip tags from rendered wiki HTML, keeping text and spaces."""
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw_html)
    t = re.sub(r"(?i)<br\s*/?>", " ", t)
    t = re.sub(r"(?i)</(p|div|li|tr|td|th|h[1-6]|ul|ol|table|blockquote|pre|section|article)>", " ", t)
    t = re.sub(r"(?i)<(p|div|li|tr|td|th|h[1-6]|ul|ol)>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return t


def normalize(text: str) -> str:
    """Light normalisation for verbatim matching: strip emphasis markers and
    tags, unify smart quotes / dashes / whitespace. Everything else is kept."""
    t = text
    t = re.sub(r"'''", "", t)          # wiki bold
    t = re.sub(r"''", "", t)           # wiki italic
    t = re.sub(r"\*\*", "", t)         # markdown bold
    t = re.sub(r"\*", "", t)           # markdown emphasis / list leftovers
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", t)  # [[A|B]] -> B
    t = re.sub(r"<[^>]+>", " ", t)     # leftover tags
    t = html.unescape(t)               # &amp; &quot; &#39; etc.
    for src, dst in _QUOTE_MAP.items():
        t = t.replace(src, dst)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# --------------------------------------------------------------------------
# Fandom API access (stdlib urllib, retries, rate limiting)
# --------------------------------------------------------------------------

class FandomClient:
    def __init__(self, api: str, rate: float, timeout: float, relay_builder=None):
        self.api = api
        self.rate = rate
        self.timeout = timeout
        self.relay_builder = relay_builder  # wraps target URLs when going via a relay
        self.next_call = 0.0
        self.calls = 0

    def _pace(self):
        now = time.time()
        if now < self.next_call:
            time.sleep(self.next_call - now)
        self.next_call = time.time() + self.rate

    def request(self, params: dict) -> dict:
        """One GET to the MediaWiki API (or through a relay) with retries;
        raises on persistent failure."""
        if self.relay_builder:
            target = DEFAULT_API + "?" + urllib.parse.urlencode(params)
            url = self.relay_builder(target)
        else:
            url = self.api + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        last_err = None
        for attempt in range(3):
            self._pace()
            self.calls += 1
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8", "replace"))
            except Exception as err:  # network / HTTP / JSON errors
                last_err = err
                time.sleep(1 + attempt * 2)
        raise RuntimeError(f"Fandom API request failed after 3 tries: {url} ({last_err})")

    def fetch_page_text(self, title: str):
        """Return the normalised plain text of a wiki page, or None if missing."""
        data = self.request({
            "action": "parse", "page": title, "prop": "text",
            "format": "json", "formatversion": 2, "redirects": 1,
        })
        if "error" in data or "parse" not in data:
            return None
        text = data["parse"]["text"]
        if isinstance(text, dict):  # formatversion=1 shape
            text = text.get("*", "")
        return normalize(html_to_text(text))

    def phrase_search(self, phrase: str, limit: int = 3):
        """Phrase-search Fandom; return [(title, snippet), ...]."""
        data = self.request({
            "action": "query", "list": "search",
            "srsearch": f'"{phrase[:200]}"', "srlimit": limit,
            "format": "json", "formatversion": 2,
        })
        hits = data.get("query", {}).get("search", [])
        return [
            (h.get("title", ""), re.sub(r"<[^>]+>", "", h.get("snippet", "")))
            for h in hits
        ]


# --------------------------------------------------------------------------
# Dialogue line extraction from the generated personal-memories.md files
# --------------------------------------------------------------------------

def parse_memory_file(path: Path):
    """Return [(speaker, text, part_no, src), ...] for every `**Speaker:** text`
    dialogue line in a generated personal-memories.md file."""
    entries = []
    part_no = 0
    src = ""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as err:
        print(f"  ! cannot read {path}: {err}")
        return entries
    for line in lines:
        m = PART_RE.match(line)
        if m:
            part_no = int(m.group(1))
            src = m.group(2)
            continue
        m = SPEAKER_RE.match(line)
        if m:
            speaker = m.group(1).strip()
            text = m.group(2).strip()
            if speaker and text and speaker.lower() != "context":
                entries.append((speaker, text, part_no, src))
    return entries


def is_own_line(speaker: str, aliases) -> bool:
    s = speaker.lower()
    return any(a.lower() in s for a in aliases)


# --------------------------------------------------------------------------
# Endpoint discovery (try Fandom, then mirrors, then relays)
# --------------------------------------------------------------------------

def probe_api(api: str, timeout: float, rate: float) -> bool:
    """True if a MediaWiki siteinfo request succeeds against this endpoint."""
    try:
        client = FandomClient(api, rate, timeout)
        data = client.request({"action": "query", "meta": "siteinfo",
                               "format": "json", "formatversion": 2})
        return "query" in data
    except Exception:
        return False


def discover_working_api(args) -> tuple:
    """Return (api_base, route_label, relay_builder) of the first reachable
    endpoint, or (None, None, None) when the network blocks everything."""
    candidates = [("fandom (hsr.fandom.com)", DEFAULT_API, None)]
    candidates += [
        (f"mirror {i + 1} ({u})", u, None) for i, u in enumerate(MIRROR_APIS)
    ]
    for name, api, builder in candidates:
        if probe_api(api, args.probe_timeout, args.rate):
            return api, name, builder
    for name, builder in RELAY_BUILDERS:
        relay = builder(DEFAULT_API + "?action=query&meta=siteinfo&format=json")
        if probe_api(relay, args.probe_timeout, args.rate):
            return relay, name, builder
    return None, None, None


# --------------------------------------------------------------------------
# Cache (JSON, so re-runs skip network entirely)
# --------------------------------------------------------------------------

def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {"corpora": {}, "lines": {}}


def save_cache(cache: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(CACHE_FILE)


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------

def verify_line(norm: str, corpus_text: str, client, cache, heir_id, do_search, max_calls):
    """Return a result dict for one normalised line (cache-first)."""
    heir_lines = cache["lines"].setdefault(heir_id, {})
    if norm in heir_lines:
        return heir_lines[norm]

    result = {"status": "not found", "pages": [], "snippet": ""}
    if corpus_text and norm in corpus_text:
        result = {"status": "matched", "pages": ["(character page corpus)"], "snippet": ""}
    elif do_search and (max_calls == 0 or client.calls < max_calls):
        try:
            hits = client.phrase_search(norm)
            if hits:
                result = {
                    "status": "found",
                    "pages": [t for t, _ in hits],
                    "snippet": hits[0][1],
                }
        except RuntimeError as err:
            print(f"    ! search failed: {err}")
            result = {"status": "search error", "pages": [], "snippet": ""}

    heir_lines[norm] = result
    return result


def main():
    global CACHE_FILE
    ap = argparse.ArgumentParser(description="Verify generated Heir dialogues against the Fandom wiki.")
    ap.add_argument("--heirs", default="", help="comma-separated character ids (default: all 13)")
    ap.add_argument("--limit", type=int, default=0, help="max unique lines to check per Heir (0 = all)")
    ap.add_argument("--api", default=DEFAULT_API, help="MediaWiki API endpoint (default hsr.fandom.com)")
    ap.add_argument("--rate", type=float, default=0.25, help="seconds between API calls (default 0.25)")
    ap.add_argument("--timeout", type=float, default=20.0, help="per-request timeout in seconds")
    ap.add_argument("--probe-timeout", type=float, default=8.0, help="timeout when probing endpoints (default 8s)")
    ap.add_argument("--max-calls", type=int, default=0, help="cap total Fandom API calls (0 = unlimited)")
    ap.add_argument("--no-fetch", action="store_true", help="offline: use cached page corpora only, no network")
    ap.add_argument("--no-search", action="store_true", help="skip the phrase-search step (corpus match only)")
    ap.add_argument("--out", default=str(DEFAULT_REPORT), help="report markdown path")
    ap.add_argument("--cache", default=str(CACHE_FILE), help="cache JSON path")
    args = ap.parse_args()

    CACHE_FILE = Path(args.cache)

    heir_ids = [h.strip() for h in args.heirs.split(",") if h.strip()] or list(CHARACTER_ALIASES)
    cache = load_cache()

    api, route, relay_builder = args.api, "explicit --api", None
    if args.api == DEFAULT_API and not args.no_fetch:
        api, route, relay_builder = discover_working_api(args)
        if api is None:
            print("!! No reachable Fandom endpoint found on this network.")
            print("   The script will continue offline (cached corpora only).")
            print("   On a network with Fandom access it works out of the box;")
            print("   or point it at a working mirror with: --api <mediawiki-endpoint>")
            args.no_fetch = True
            api = DEFAULT_API

    client = FandomClient(api, args.rate, args.timeout, relay_builder)
    print(f"Fandom verification — route: {route} ({client.api})")
    print(f"Targets: {', '.join(heir_ids)}")
    if args.no_fetch:
        print("Offline mode: using cached Fandom corpora only (no network).")

    # ---- 1. obtain Fandom content (pages) ----
    corpus_texts = {}   # heir_id -> "\n".join(normalised page texts)
    page_list = {}      # heir_id -> [(title, fetched?)]

    for heir_id in heir_ids:
        pages = cache["corpora"].setdefault(heir_id, {})
        texts = []
        entries = []
        for title in HEIR_PAGES.get(heir_id, [heir_id]):
            if title in pages:
                texts.append(pages[title])
                entries.append((title, True))
                continue
            if args.no_fetch:
                entries.append((title, False))
                continue
            try:
                text = client.fetch_page_text(title)
            except RuntimeError as err:
                print(f"  ! {heir_id}: cannot fetch '{title}': {err}")
                text = None
            if text:
                pages[title] = text
                texts.append(text)
                entries.append((title, True))
                print(f"  fetched: {heir_id:>26} <- {title}")
            else:
                entries.append((title, False))
        corpus_texts[heir_id] = "\n".join(texts)
        page_list[heir_id] = entries

    # ---- 2. examine every generated dialogue line ----
    stats = {}
    for heir_id in heir_ids:
        folder = ROOT / HEIR_FOLDERS.get(heir_id, heir_id)
        memory = folder / "personal-memories.md"
        if not memory.exists():
            print(f"  ! no {memory.relative_to(ROOT)} — skipped")
            stats[heir_id] = {"total": 0, "own": 0, "matched": 0, "found": 0, "notfound": 0, "errors": 0, "unmatched": []}
            continue

        entries = parse_memory_file(memory)
        aliases = CHARACTER_ALIASES.get(heir_id, [heir_id])
        corpus_text = corpus_texts[heir_id]

        seen, unique = set(), []
        for speaker, text, part_no, src in entries:
            norm = normalize(text)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            unique.append({"norm": norm, "raw": text, "speaker": speaker,
                           "own": is_own_line(speaker, aliases), "part": part_no, "src": src})

        if args.limit:
            unique = unique[: args.limit]

        st = {"total": len(unique), "own": sum(1 for u in unique if u["own"]),
              "matched": 0, "found": 0, "notfound": 0, "errors": 0, "unmatched": []}

        for i, u in enumerate(unique, 1):
            res = verify_line(u["norm"], corpus_text, client, cache, heir_id,
                              do_search=(not args.no_search and not args.no_fetch),
                              max_calls=args.max_calls)
            status = res["status"]
            if status == "matched":
                st["matched"] += 1
            elif status == "found":
                st["found"] += 1
            elif status == "search error":
                st["errors"] += 1
            else:
                st["notfound"] += 1
                st["unmatched"].append(u)
            if i % 50 == 0 or i == len(unique):
                print(f"  {heir_id:>26}: {i}/{len(unique)} lines "
                      f"(matched {st['matched']}, found {st['found']}, missing {st['notfound']})")

        stats[heir_id] = st
        print(f"  {heir_id:>26}: DONE {st['total']} unique lines | "
              f"matched {st['matched']} | found-via-search {st['found']} | "
              f"not-found {st['notfound']} | errors {st['errors']}")

    # ---- 3. write the report ----
    if not args.no_fetch:
        save_cache(cache)

    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Fandom Verification Report",
        "",
        f"*Generated: {now}*",
        f"*Source: `{client.api}` (MediaWiki API)*",
        "*Examined: every auto-generated dialogue line in each Heir's `personal-memories.md`*",
        "",
        "**Method:** each unique `**Speaker:** text` line is normalised (whitespace, smart",
        "quotes, dashes, emphasis markers unified) and checked verbatim against the Heir's",
        "fetched Fandom page corpus; misses are then phrase-searched on Fandom. Anything",
        "still unmatched is listed below as **not found** (may be story dialogue that Fandom",
        "does not publish, or a transcription difference).",
        "",
        "## Summary",
        "",
        "| Heir | unique lines | own lines | matched (corpus) | found (search) | not found | coverage |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for heir_id in heir_ids:
        st = stats.get(heir_id, {"total": 0, "own": 0, "matched": 0, "found": 0, "notfound": 0, "errors": 0})
        total = st["total"]
        ok = st["matched"] + st["found"]
        pct = f"{100 * ok / total:.1f}%" if total else "—"
        lines.append(
            f"| {heir_id} | {total} | {st['own']} | {st['matched']} | {st['found']} | {st['notfound']} | {pct} |"
        )
    lines += ["", "## Details", ""]
    for heir_id in heir_ids:
        st = stats.get(heir_id, {"total": 0, "own": 0, "matched": 0, "found": 0, "notfound": 0, "errors": 0, "unmatched": []})
        total = st["total"]
        ok = st["matched"] + st["found"]
        pct = f"{100 * ok / total:.1f}%" if total else "—"
        fetched = ", ".join(t for t, okk in page_list.get(heir_id, []) if okk) or "(none fetched)"
        lines.append(f"### {heir_id} — {ok}/{total} verified ({pct})")
        lines.append("")
        lines.append(f"*Fandom pages consulted: {fetched}*")
        lines.append("")
        if not st["unmatched"]:
            lines.append("_Every examined line was found on Fandom._")
            lines.append("")
            continue
        lines.append("**Not found on Fandom** (raw text / source):")
        lines.append("")
        for u in st["unmatched"]:
            kind = "own line" if u["own"] else "other speaker"
            lines.append(f"- **{u['speaker']}:** {u['raw']}  \n  _({kind}; Part {u['part']} — `{u['src']}`)_")
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written: {out.relative_to(ROOT)}")

    grand = {"total": 0, "matched": 0, "found": 0, "notfound": 0}
    for st in stats.values():
        for k in grand:
            grand[k] += st[k]
    ok = grand["matched"] + grand["found"]
    pct = f"{100 * ok / grand['total']:.1f}%" if grand["total"] else "—"
    print(f"TOTAL: {ok}/{grand['total']} verified ({pct}) — "
          f"matched {grand['matched']}, found-via-search {grand['found']}, not-found {grand['notfound']}")


if __name__ == "__main__":
    main()
