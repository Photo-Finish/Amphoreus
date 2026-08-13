"""
fetch_wiki_amphoreus.py — download the Honkai: Star Rail wiki's Amphoreus
world pages into the databank (`databank/wiki/<category>/`) as clean markdown,
for the Heirs' world-knowledge system. Pages are sorted into categories:
titans / locations / factions / characters / gameplay / experiment / lore.

Source: **honkai-star-rail.fandom.com** (English Fandom wiki, MediaWiki API).

NETWORK RECIPE (this machine, 2026-08-13):
  - DNS for fandom.com is locally poisoned (resolves to a wrong IP) and the
    direct route is firewalled.
  - It works via the iKuuu VPN proxy (http://127.0.0.1:12000) with the host's
    REAL Cloudflare IP pinned. The proxy is flaky -> every request retries
    with backoff. Override with env WIKI_PROXY / WIKI_RESOLVE_IP.

USAGE:
    python tools/fetch_wiki_amphoreus.py --discover
        Print the Amphoreus categories/pages that would be fetched, then exit.
    python tools/fetch_wiki_amphoreus.py --sort
        Move pages already downloaded to docs/wiki/ into databank/wiki sorted
        (then remove docs/wiki).
    python tools/fetch_wiki_amphoreus.py --pages 'Amphoreus,Okhema'
        Fetch only the named pages (comma-separated).
    python tools/fetch_wiki_amphoreus.py
        Fetch the whole curated Amphoreus world set into databank/wiki/.
    python tools/fetch_wiki_amphoreus.py --force
        Re-fetch pages that already exist.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "databank" / "wiki"      # sorted destination (databank/wiki/<cat>/)
LEGACY = ROOT / "docs" / "wiki"       # pre-sort location (migrated by --sort)

HOST = "honkai-star-rail.fandom.com"
API = f"https://{HOST}/api.php"
REAL_IP = os.environ.get("WIKI_RESOLVE_IP", "162.159.142.170")
PROXY = os.environ.get("WIKI_PROXY", "http://127.0.0.1:12000")
UA = "AmphoreusSanctuary/1.0 (local AI sanctuary project; fetches public wiki lore)"

import urllib3.util.connection as _uc  # noqa: E402
import requests  # noqa: E402

_orig_create = _uc.create_connection


def _pin_dns(address, *a, **kw):
    host, port = address
    if host == HOST:
        address = (REAL_IP, port)
    return _orig_create(address, *a, **kw)


_uc.create_connection = _pin_dns

SESSION = requests.Session()
SESSION.proxies = {"https": PROXY, "http": PROXY}
SESSION.headers["User-Agent"] = UA
SESSION.headers["Accept"] = "application/json, text/plain, */*"


def api(params, tries=6, timeout=45):
    """GET the MediaWiki API with retry + backoff (the proxy is flaky)."""
    last = None
    for i in range(tries):
        try:
            r = SESSION.get(API, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last = RuntimeError(f"HTTP {r.status_code}")
        except Exception as e:  # noqa: BLE001 - network layer, retry
            last = e
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"API failed after {tries} tries: {last}")


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #
def discover_categories():
    """Return Amphoreus-related category names (prefix search on 'Amphoreus')."""
    cats, cont = [], {}
    while True:
        p = {"action": "query", "list": "allcategories", "acprefix": "Amphoreus",
             "aclimit": 500, "format": "json", "formatversion": "2"}
        p.update(cont)
        d = api(p)
        cats += [c.get("category") or c.get("name") or c.get("*") for c in d["query"]["allcategories"]]
        cont = d.get("continue", {})
        if not cont:
            break
        time.sleep(0.4)
    return cats


def page_categories(title):
    d = api({"action": "query", "titles": title, "prop": "categories",
             "cllimit": 200, "format": "json", "formatversion": "2"})
    out = []
    for pg in d["query"]["pages"]:
        out += [c["title"] for c in pg.get("categories", [])]
    return out


def category_members(category, limit=500):
    """Return page titles in a category (recursively through subcats optional)."""
    titles, cont = [], {}
    while True:
        p = {"action": "query", "list": "categorymembers",
             "cmtitle": category, "cmlimit": limit,
             "cmtype": "page", "format": "json", "formatversion": "2"}
        p.update(cont)
        d = api(p)
        titles += [m["title"] for m in d["query"]["categorymembers"]]
        cont = d.get("continue", {})
        if not cont:
            break
        time.sleep(0.4)
    return titles


# --------------------------------------------------------------------------- #
# Wikitext -> Markdown
# --------------------------------------------------------------------------- #
def _strip_templates(text):
    """Remove {{...}} templates; keep {{Infobox|name=value}} as bullets."""
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("{{", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if text.startswith("{{", j):
                    depth += 1
                elif text.startswith("}}", j):
                    depth -= 1
                    j += 2
                    continue
                j += 1
            tpl = text[i:j].strip()
            infobox = re.match(r"\{\{\s*(?:Infobox|InfoBox)\s*[^|}]*", tpl)
            if infobox:
                # keep name=value pairs as bullets (useful world facts)
                pairs = re.findall(r"\|\s*([^=|]+)\s*=\s*([^|]*?)(?=\s*\||\s*\}\})", tpl)
                for k, v in pairs:
                    k = k.strip()
                    v = _strip_templates(v.strip())
                    if k.lower() not in ("image", "caption", "imagecaption"):
                        out.append(f"- {k}: {v}")
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _convert_links(text):
    # [[File:...|...]] -> drop; [[Page|text]] -> text; [[Page]] -> Page
    def _repl(m):
        inner = m.group(1)
        if inner.lower().startswith(("file:", "image:")):
            return ""
        if "|" in inner:
            return inner.split("|", 1)[1]
        return inner
    return re.sub(r"\[\[([^\]]+)\]\]", _repl, text)


def wikitext_to_markdown(wt):
    """Best-effort wikitext -> clean markdown for world-lore pages."""
    t = wt
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)          # comments
    t = re.sub(r"<ref[^>]*/>", "", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)  # references
    t = re.sub(r"<gallery[^>]*>.*?</gallery>", "", t, flags=re.S)  # image galleries
    t = re.sub(r"<nowiki>(.*?)</nowiki>", r"\1", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "", t)                          # other html tags
    t = re.sub(r"__TOC__|__NOTOC__|__FORCETOC__", "", t)
    t = re.sub(r"\{\{[^}]*\}\}", "", t)                    # simple templates
    t = _strip_templates(t)                                # nested-safe templates
    # headings: =X= (h1) .. ======X====== (h6)
    t = re.sub(r"^(={1,6})\s*(.+?)\s*\1\s*$",
               lambda m: "#" * len(m.group(1)) + " " + m.group(2).strip(), t, flags=re.M)
    t = _convert_links(t)
    t = re.sub(r"'''''(.+?)'''''", r"***\1***", t)         # bold+italic
    t = re.sub(r"'''''(.+?)'''''", r"***\1***", t)
    t = re.sub(r"''''(.+?)''''", r"**\1**", t)
    t = re.sub(r"'''(.+?)'''", r"**\1**", t)
    t = re.sub(r"''(.+?)''", r"*\1*", t)
    # horizontal rules
    t = re.sub(r"^-{4,}\s*$", "---", t, flags=re.M)
    # drop stray category/interwiki
    t = re.sub(r"\[\[Category:[^\]]*\]\]", "", t)
    t = re.sub(r"\[\[[a-z-]+:[^\]]*\]\]", "", t)
    # collapse 3+ blank lines
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def slugify(title):
    s = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-").lower()
    return s or "page"


# --------------------------------------------------------------------------- #
# Category sort (databank/wiki/<category>/)
# --------------------------------------------------------------------------- #
TITAN_NAMES = ["aquila", "cerces", "phagousa", "janus", "kephale", "thanatos",
               "oronyx", "georios", "nikador", "mnestia", "talanton", "zagreus"]

FACTION_TOKENS = ["chrysos-heirs", "pathstrider", "caprists", "cleaners",
                  "council-of-elders", "erythrokeramists", "helkolithists",
                  "kremnoan-detachment", "kremnoan-dynasty", "lotophagists",
                  "nodists", "nousporists", "venerationists",
                  "five-gourmet-overlords", "black-tide-council"]

CHARACTER_TOKENS = ["unnamed-chrysos-heir", "big-chungus-bartholos", "dolos",
                    "epos", "campa", "bulsa", "carmitis",
                    "researcher-eikura-shuu", "bartholos", "akmonides"]

LOCATION_TOKENS = ["okhema", "janusopolis", "grove-of-epiphany", "castrum-kremnos",
                   "styxia", "aedes-elysiae", "aidonia", "dawncloud",
                   "eye-of-twilight", "great-tomb", "ruins-of-time", "memortis",
                   "vortex-of-genesis", "titan-cliff", "ashen-throne",
                   "destiny-s-gate", "dome-of-", "abyss-of-fate", "archive-of"]

AREA_WORDS = ["altar", "plaza", "fountain", "courtyard", "market", "gate",
              "chapel", "mausoleum", "bastion", "pool", "perch", "smithy",
              "shop", "forum", "tower", "statue", "colossus", "veins",
              "cliff", "entrance", "sanctum", "battlefront", "scarwood",
              "murmuring", "strife", "warbling", "radiant", "lightless",
              "fortress", "universal", "nightmare", "destiny", "dragonbone",
              "cloister", "depths", "chisel", "platform", "sector", "matrix"]

GAMEPLAY_TOKENS = ["calyx-", "cavern-of-corrosion", "echo-of-war", "-crest",
                   "chasmic-geocore", "dromas-caravan", "resplendent-ambrosia",
                   "tidal-bounty"]


def categorize(slug):
    """Return the databank/wiki/<category> subfolder for a page slug."""
    t = slug
    if t == "titans":
        return "titans"
    if "amphoreus-experiment" in t or t == "the-amphoreus-experiment":
        return "experiment"
    for name in TITAN_NAMES:
        if t == name or t.startswith(name + "-"):
            return "titans"
    for f in FACTION_TOKENS:
        if f in t:
            return "factions"
    for g in GAMEPLAY_TOKENS:
        if g in t:
            return "gameplay"
    for c in CHARACTER_TOKENS:
        if c in t:
            return "characters"
    for loc in LOCATION_TOKENS:
        if loc in t:
            return "locations"
    if any(w in t for w in AREA_WORDS):
        return "locations"
    return "lore"


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #
def fetch_page(title):
    d = api({"action": "parse", "page": title, "prop": "wikitext",
             "format": "json", "formatversion": "2"}, tries=6)
    wt = d["parse"]["wikitext"]
    md = wikitext_to_markdown(wt)
    cats = page_categories(title)
    header = (
        f"# {title}\n\n"
        f"> Source: https://{HOST}/wiki/{title.replace(' ', '_')}\n"
        f"> Fetched: {time.strftime('%Y-%m-%d')} · Categories: {', '.join(cats)}\n\n"
        "---\n\n"
    )
    return header + md + "\n", cats


def sort_legacy():
    """Move docs/wiki/*.md into databank/wiki/<cat>/ sorted, then drop docs/wiki."""
    if not LEGACY.exists():
        print("no docs/wiki to sort")
        return
    files = sorted(LEGACY.glob("*.md"))
    moved = 0
    for f in files:
        cat = categorize(f.stem)
        dest_dir = OUT / cat
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f.name
        f.replace(dest)
        moved += 1
    LEGACY.rmdir()  # remove docs/wiki if now empty
    print(f"moved {moved} pages into databank/wiki/ (sorted)")


def main():
    ap = argparse.ArgumentParser(description="Fetch Amphoreus world lore from the HSR wiki.")
    ap.add_argument("--discover", action="store_true", help="print discovered pages and exit")
    ap.add_argument("--sort", action="store_true", help="move docs/wiki pages into databank/wiki sorted")
    ap.add_argument("--pages", default="", help="comma-separated page titles to fetch only")
    ap.add_argument("--force", action="store_true", help="re-fetch existing pages")
    args = ap.parse_args()

    if args.sort:
        sort_legacy()
        return

    print(f"wiki: {HOST} (pinned {REAL_IP}, proxy {PROXY}) -> {OUT}")

    if args.pages:
        titles = [t.strip() for t in args.pages.split(",") if t.strip()]
    else:
        # Curated Amphoreus world set: Amphoreus hub + locations + titans +
        # factions + key story pages. Discovered via allcategories + known hubs.
        seed = ["Amphoreus", "Amphoreus, The Eternal Land", "Amphoreus Annals",
                "Okhema", "Janusopolis", "Grove of Epiphany", "Castrum Kremnos",
                "Styxia", "Aedes Elysiae", "Great Abyss", "Vortex of Genesis",
                "Aidonia", "Titan", "The Twelve Titans", "Nikador", "Cerces",
                "Phagousa", "Janus", "Kephale", "Thanatos", "Oronyx", "Aquila",
                "Georios", "Hippeus", "Lanternus", "Mnestia", "Talanton",
                "Zagreus", "The Black Tide", "Amphoreus Experiment",
                "Pathstriders", "Chrysos Heirs", "Coreflame", "River of Souls",
                "Twilight Courtyard", "Dawn Device", "Century Gate",
                "Abyss of Fate", "Cloudedge Bastion Ruins", "Dragonbone City",
                "Lightless Chapel", "Murmuring Woods", "Nightmare's Echo",
                "Vortex of Genesis", "Memortis Shore"]
        titles = []
        for s in seed:
            d = api({"action": "query", "list": "search", "srsearch": s,
                     "srlimit": 3, "format": "json", "formatversion": "2"})
            for h in d["query"]["search"]:
                ti = h["title"]
                if ti not in titles and not ti.startswith(("File:", "User:", "Category:", "Template:", "Module:")):
                    titles.append(ti)
            time.sleep(0.4)
        # Also walk Amphoreus* categories for location/lore pages.
        for cat in discover_categories():
            if any(k in cat for k in ("Location", "Titan", "Story", "Faction", "World", "History")):
                for ti in category_members("Category:" + cat):
                    if ti not in titles and not ti.startswith(("File:", "User:", "Category:", "Template:", "Module:")):
                        titles.append(ti)
                time.sleep(0.4)

    print(f"{len(titles)} pages to fetch.")
    if args.discover:
        for t in titles:
            print("  -", t)
        return

    ok, fail = 0, []
    for title in titles:
        cat = categorize(slugify(title))
        dest_dir = OUT / cat
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / (slugify(title) + ".md")
        if dest.exists() and not args.force:
            print(f"  = {title} (exists in {cat}/)")
            continue
        try:
            md, cats = fetch_page(title)
            dest.write_text(md, encoding="utf-8")
            print(f"  ✓ {title} ({len(md)} chars -> {cat}/{dest.name})")
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {title}: {e}")
            fail.append(title)
        time.sleep(0.6)

    print(f"\nDone: {ok} fetched, {len(fail)} failed.")
    if fail:
        print("Failed:", ", ".join(fail))


if __name__ == "__main__":
    main()
