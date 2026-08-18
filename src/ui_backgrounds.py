"""Shared location-background helpers for the UI (Classic / Map / Galgame).

The background art lives in `assets/galgame/bg-<slug>.jpg`, fetched from the
HSR wiki's Amphoreus area artwork by `tools/fetch_galgame_backgrounds.py`.
Every place the Heirs can be has a matching backdrop, and each Heir also has a
home-city backdrop. These helpers pick the most relevant one for a Heir
(current world location first, then home city, then the default banner).
"""

from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
GALGAME_DIR = ASSETS / "galgame"
DEFAULT_BG = ASSETS / "amphoreus_bg.jpg"

# Per-Heir home-city background.
PER_HEIR_BG = {
    "aglaea": "bg-okhema",
    "cerydra": "bg-okhema",
    "cipher": "bg-okhema",
    "anaxa": "bg-grove",
    "hyacine": "bg-grove",
    "castorice": "bg-styxia",
    "hysilens": "bg-styxia",
    "mydei": "bg-kremnos",
    "tribbie": "bg-janusopolis",
    "phainon": "bg-aedes-elysiae",
    "cyrene": "bg-aedes-elysiae",
    "dan-heng-permansor-terrae": "bg-beyond-time",
    "evernight": "bg-okhema-evernight",
}

# world-location name substring -> bg slug. Matching is case-insensitive
# substring and ORDERED: specific sub-areas come before their parent city so
# e.g. "Abyss of Fate" Janusopolis gets its own backdrop, not the city's.
LOCATION_MATCHES = (
    ("abyss of fate", "bg-abyss-of-fate"),
    ("okhema", "bg-okhema"),
    ("janusopolis", "bg-janusopolis"),
    ("murmuring", "bg-murmuring-woods"),
    ("grove", "bg-grove"),
    ("kremnos", "bg-kremnos"),
    ("dragonbone", "bg-dragonbone-city"),
    ("styxia", "bg-styxia"),
    ("elysiae", "bg-aedes-elysiae"),
    ("aidonia", "bg-memortis-shore"),
    ("lightless", "bg-lightless-chapel"),
    ("dawncloud", "bg-dawncloud"),
    ("cloudedge", "bg-cloudedge-bastion"),
    ("eye of twilight", "bg-eye-of-twilight"),
    ("twilight", "bg-eye-of-twilight"),
    ("nightmare", "bg-nightmare-echo"),
    ("great tomb", "bg-great-tomb"),
    ("memortis", "bg-memortis-shore"),
    ("ruins of time", "bg-memortis-shore"),
    ("vortex", "bg-vortex-of-genesis"),
    ("abyss", "bg-abyss-of-fate"),
    ("beyond time", "bg-beyond-time"),
)


def location_slug(loc):
    """Map a world-location name to a bg slug (or None)."""
    if not loc:
        return None
    l = loc.lower()
    for key, slug in LOCATION_MATCHES:
        if key in l:
            return slug
    return None


def current_location(character_id) -> str:
    """The Heir's current place name (or '' if unknown)."""
    try:
        from src.world.world_state import WorldState
        return WorldState().location_name(character_id) or ""
    except Exception:
        return ""


def bg_path(character_id):
    """Most relevant backdrop for a Heir: current place > home city > default."""
    loc = current_location(character_id)
    slug = location_slug(loc)
    if slug and (GALGAME_DIR / f"{slug}.jpg").exists():
        return GALGAME_DIR / f"{slug}.jpg"
    slug = PER_HEIR_BG.get(character_id)
    if slug and (GALGAME_DIR / f"{slug}.jpg").exists():
        return GALGAME_DIR / f"{slug}.jpg"
    return DEFAULT_BG if DEFAULT_BG.exists() else None


def bg_path_for_place(place: str):
    """Backdrop Path for a world place name (or None)."""
    slug = location_slug(place)
    if slug and (GALGAME_DIR / f"{slug}.jpg").exists():
        return GALGAME_DIR / f"{slug}.jpg"
    return DEFAULT_BG if DEFAULT_BG.exists() else None


def land_art_path(path):
    """Visit / Walk art: wiki Area JPEG cropped onto pavement / path / terrace."""
    if not path:
        return None
    try:
        from src.ui_ground import ensure_grounded
        return ensure_grounded(path)
    except Exception:
        return Path(path)


def place_for_slug(slug: str) -> str:
    """Best-effort world place name for a bg slug (for weather/eco derive)."""
    if not slug:
        return "Okhema"
    # Prefer longest matching LOCATION_MATCHES entry that maps to this slug.
    for key, s in LOCATION_MATCHES:
        if s == f"bg-{slug}" or s == slug or s.endswith(slug):
            # Title-ish from key
            return key.title() if key != "elysiae" else "Aedes Elysiae"
    return slug.replace("-", " ").title()


def available_backgrounds():
    """[(slug, Path)] for every downloaded area backdrop (sorted)."""
    out = []
    if GALGAME_DIR.exists():
        for p in sorted(GALGAME_DIR.glob("bg-*.jpg")):
            out.append((p.stem[3:], p))
    return out
