"""
build_heir_knowledge.py — decide each Heir's SPECIFIC knowledge range of the
Amphoreus world (grounded in the wiki docs in databank/wiki/) and embed it into
their character settings (`world_knowledge` section of each card in
src/characters/*.json).

The Heirs only know Amphoreus (see src/core/world_knowledge.py). This tool
decides WHAT each Heir knows *within* Amphoreus, based on:
  - their home city (from the card)          -> wiki city page essence
  - their Titan / Coreflame (from the card)  -> wiki Titan page essence
  - their circles (Chrysos Heirs, factions)  -> wiki faction pages
  - the era's events (black tide, Coreflame trials, their own biography)
  - the six great cities (every Heir knows the world's names)

It writes a `world_knowledge` section into each card, including a compact
`prompt_block` that CharacterLoader.build_system_prompt() injects into the
system prompt, so the knowledge is actually used in conversation.

USAGE:
    python tools/build_heir_knowledge.py            # all 13 Heirs
    python tools/build_heir_knowledge.py --heirs anaxa,tribbie
    python tools/build_heir_knowledge.py --dry-run  # show, don't write
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
CARDS = ROOT / "src" / "characters"
WIKI = ROOT / "databank" / "wiki"  # sorted: databank/wiki/<category>/<slug>.md

# The six great cities (every Heir of Amphoreus knows these names).
GREAT_CITIES = [
    ("Okhema", "the \"Eternal Holy City\""),
    ("Janusopolis", "the \"City of Thousand Gates\""),
    ("Grove of Epiphany", "the \"Home of Sages\""),
    ("Castrum Kremnos", "the \"Capital of Might\""),
    ("Styxia", "the \"Pearly Shores\""),
    ("Aidonia", "the \"Snow City\""),
]

# Per-Heir: which wiki docs anchor their home / Titan / circles.
# Values are substrings matched against the wiki file SLUG (filename) so we
# survive title quirks (e.g. "\"Eternal Holy City\" Okhema" -> slug okhema).
ANCHORS = {
    "aglaea": {"city": "okhema", "titan": "mnestia", "factions": ["chrysos-heirs"]},
    "anaxa": {"city": "grove-of-epiphany", "titan": "cerces",
              "factions": ["chrysos-heirs", "nousporists", "six-schools"]},
    "castorice": {"city": "styxia", "titan": "thanatos",
                  "factions": ["chrysos-heirs", "black-tide"]},
    "cerydra": {"city": "okhema", "titan": "talanton",
                "factions": ["chrysos-heirs", "council-of-elders"]},
    "cipher": {"city": "okhema", "titan": "zagreus",
               "factions": ["chrysos-heirs"]},
    "cyrene": {"city": "aedes-elysiae", "titan": "",
               "factions": ["chrysos-heirs", "amphoreus-experiment"]},
    "dan-heng-permansor-terrae": {"city": "", "titan": "georios",
                                  "factions": ["chrysos-heirs", "pathstrider"]},
    "evernight": {"city": "", "titan": "oronyx",
                  "factions": ["chrysos-heirs", "garden-of-recollection"]},
    "hyacine": {"city": "grove-of-epiphany", "titan": "aquila",
                "factions": ["chrysos-heirs", "twilight-courtyard"]},
    "hysilens": {"city": "styxia", "titan": "phagousa",
                 "factions": ["chrysos-heirs", "five-gourmet-overlords"]},
    "mydei": {"city": "castrum-kremnos", "titan": "nikador",
              "factions": ["chrysos-heirs", "kremnoan-dynasty"]},
    "phainon": {"city": "aedes-elysiae", "titan": "kephale",
                "factions": ["chrysos-heirs"]},
    "tribbie": {"city": "janusopolis", "titan": "janus",
                "factions": ["chrysos-heirs", "council-of-elders"]},
}

# Name/alias signals used to detect which docs mention a Heir personally.
def _aliases(card):
    m = card.get("meta", {})
    names = [m.get("name", "")]
    names += [c for c in card.get("knowledge", {}).get("known_characters", {})]
    return [n for n in names if n]


def _slug_to_title(slug):
    return slug.replace("-", " ").title()


def load_wiki_docs():
    """Return {slug: {"title": str, "text": str}} for every fetched doc
    (recursively across databank/wiki/<category>/)."""
    docs = {}
    if not WIKI.exists():
        return docs
    for f in sorted(WIKI.glob("**/*.md")):
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        m = re.match(r"^#\s+(.+)$", txt, re.M)
        title = m.group(1).strip() if m else _slug_to_title(f.stem)
        docs[f.stem] = {"title": title, "text": txt}
    return docs


def _is_infobox_dump(para):
    """True if a paragraph is mostly template/infobox field remnants
    (key = value or - key: value), even flattened onto one line."""
    if not para.strip():
        return False
    eq = len(re.findall(r"[\w' ]+\s*=\s*", para))
    cols = len(re.findall(r"-\s*[\w' ]+:", para))
    known = sum(para.count(k) for k in
                ("vaEN", "vaCN", "vaJP", "vaKR", "pathlore", "factionNote",
                 "faction2", "relatives", "coreflame =", "image =", "caption"))
    return (eq + cols) >= 3 or known >= 2


def _essence(doc, max_chars=420):
    """First substantive prose paragraph of a wiki doc (1-3 sentences)."""
    text = doc["text"]
    for para in text.split("\n\n"):
        para = para.strip()
        if not para or para.startswith((">", "#", "---")):
            continue
        if _is_infobox_dump(para):
            continue
        para = re.sub(r"[\*\#\[\]\|]", "", para)
        para = re.sub(r"\{\{|\}\}", "", para)
        para = re.sub(r"\s+", " ", para).strip()
        if len(para) >= 40:
            return para[:max_chars].strip()
    return ""


def _find_doc(docs, slug_part):
    """Find the wiki doc for a slug part: exact slug first, then whole-token
    substring (so 'janus' matches 'janus' but NOT 'janusopolis')."""
    if not slug_part:
        return None
    norm = slug_part.strip().lower()
    if norm in docs:
        return docs[norm]
    pat = re.compile(rf"(^|-){re.escape(norm)}(-|$)")
    cands = [s for s in docs if pat.search(s)]
    if not cands:
        return None
    cands.sort(key=len)
    return docs[cands[0]]


def _mention_docs(docs, names):
    """Docs that mention any of these names (personal relevance)."""
    hits = []
    for slug, doc in docs.items():
        text = doc["text"].lower()
        if any(n and n.lower() in text for n in names):
            hits.append((slug, doc))
    return hits


def build_prompt_block(card, info):
    """Compact per-Heir WORLD KNOWLEDGE block injected into the system prompt."""
    home = info["home"]
    titan = info["titan"]
    cities = ", ".join(f"{n} ({d})" for n, d in GREAT_CITIES)
    lines = ["WORLD KNOWLEDGE — what you, of Amphoreus, know:"]
    if home:
        lines.append(f"- Your home: {home}")
    if titan:
        lines.append(f"- Your Titan: {titan}")
    lines.append(
        f"- The world: Amphoreus has six great cities — {cities} — each "
        "under a Titan's dominion. The black tide devours whatever it "
        "touches; the Chrysos Heirs bear the Coreflames to hold it back."
    )
    if info["circles"]:
        lines.append(f"- Your circles: {info['circles']}")
    if info["events"]:
        lines.append(f"- Your age: {info['events']}")
    return "\n".join(lines)


def build_knowledge(card, docs):
    cid = card["meta"]["id"]  # e.g. chrysos-heir-09
    name = card["meta"]["name"]
    ident = card.get("identity", {})
    city = ident.get("city_state", "")
    titan = ident.get("titan", "")
    bio = card.get("biography", {})
    doms = card.get("knowledge", {}).get("domains", [])

    a = ANCHORS.get(_key_of(card), {})

    home_doc = _find_doc(docs, a.get("city", "")) if a.get("city") else None
    titan_doc = _find_doc(docs, a.get("titan", "")) if a.get("titan") else None

    home = f"{city}" if city else ""
    if home_doc:
        ess = _essence(home_doc)
        home = f"{home_doc['title']} — {ess}" if ess else home_doc["title"]
    elif city:
        home = city

    titan_txt = f"{titan}" if titan else ""
    if titan_doc:
        ess = _essence(titan_doc)
        titan_txt = f"{titan_doc['title']} — {ess}" if ess else titan_doc["title"]
    elif titan:
        titan_txt = titan
    # If the wiki page had no prose, fall back to the card's canon note.
    if titan and titan_txt == titan:
        kc = card.get("knowledge", {}).get("known_characters", {})
        note = kc.get(titan)
        if note:
            titan_txt = f"{titan} — {note}"

    # Circles: faction docs + the Heir's own domains.
    circles = []
    for fpart in a.get("factions", []):
        d = _find_doc(docs, fpart)
        if d:
            t = d["title"]
            if t not in circles:
                circles.append(t)
    if doms and len(circles) < 4:
        for dom in doms[:3]:
            if dom and dom not in circles:
                circles.append(dom)
    circles_txt = "; ".join(circles) if circles else "the Chrysos Heirs"

    # Events: biography key events (what they lived through).
    events = bio.get("key_events", []) or []
    ev = "; ".join(events[:4]) if events else "the Coreflame trials"
    if "black tide" not in ev.lower():
        ev = "the black tide; " + ev

    info = {
        "home": home, "titan": titan_txt, "circles": circles_txt, "events": ev,
    }
    return info, build_prompt_block(card, info)


def _key_of(card):
    """Return the heir key used in ANCHORS (from meta.id or meta.name)."""
    mid = card.get("meta", {}).get("id", "")
    name = card.get("meta", {}).get("name", "")
    # id is like 'chrysos-heir-09' -> not the anchor key; use lowercase name slug
    if name:
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return mid


def main():
    ap = argparse.ArgumentParser(description="Embed per-Heir Amphoreus world knowledge into cards.")
    ap.add_argument("--heirs", default="", help="comma-separated keys (default: all 13)")
    ap.add_argument("--dry-run", action="store_true", help="show blocks, don't write")
    args = ap.parse_args()

    docs = load_wiki_docs()
    print(f"wiki docs available: {len(docs)}")

    wanted = {k.strip() for k in args.heirs.split(",") if k.strip()} if args.heirs else None
    changed = 0
    for f in sorted(CARDS.glob("*.json")):
        card = json.loads(f.read_text(encoding="utf-8"))
        key = _key_of(card)
        if wanted and key not in wanted:
            continue
        info, block = build_knowledge(card, docs)
        wk = {
            "home": info["home"],
            "titan": info["titan"],
            "circles": info["circles"],
            "events": info["events"],
            "prompt_block": block,
            "source": "wiki (honkai-star-rail.fandom.com) + canon card",
            "built": "2026-08-13",
        }
        if args.dry_run:
            print(f"\n=== {key} ===")
            print(block)
            continue
        if card.get("world_knowledge") != wk:
            card["world_knowledge"] = wk
            f.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✓ {key}: world_knowledge embedded")
            changed += 1
        else:
            print(f"  = {key}: unchanged")
    print(f"\n{changed} cards updated.")


if __name__ == "__main__":
    main()
