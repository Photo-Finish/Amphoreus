"""
KB Builder — maps databank markdown sources to per-character knowledge bases.

Every Chrysos Heir gets a ChromaDB collection built from:
  1. GLOBAL sources  — world lore, Titans, the Amphoreus experiment, black tide,
                       the master registry (indexed into every character).
  2. PROFILE source  — the character's own databank profile (always indexed whole).
  3. MISSION sources — all chapter + adventure dialogue files, chunk-filtered to
                       passages that mention the character (or their aliases).
"""

from pathlib import Path
from typing import Dict, List

# Alias tokens used to select character-relevant passages from mission dialogue.
# Keys are character card IDs (file stems in src/characters/).
CHARACTER_ALIASES: Dict[str, List[str]] = {
    "aglaea": ["Aglaea"],
    "anaxa": ["Anaxa", "Anaxagoras", "Blasphemer"],
    "castorice": ["Castorice", "Thanatos"],
    "cerydra": ["Cerydra", "Empress", "Imperator of the Flame-Chase"],
    "cipher": ["Cipher", "Cifera", "Trickery"],
    "cyrene": ["Cyrene", "Demiurge", "Mem"],
    "dan-heng-permansor-terrae": ["Dan Heng", "Permansor", "Terravox", "Vidyadhara"],
    "evernight": ["Evernight", "March 7th", "March 7", "Oronyx", "Rain of Sensation"],
    "hyacine": ["Hyacine", "Hyacinthia", "Seliose", "Aquila"],
    "hysilens": ["Hysilens", "Helektra", "Phagousa"],
    "mydei": ["Mydei", "Mydeimos", "Kremnos", "Nikador"],
    "phainon": ["Phainon", "Khaslana", "Deliverer", "Kephale"],
    "tribbie": ["Tribbie", "Tribios", "Trianne", "Trinnon", "Janus"],
}

# Global files indexed into EVERY character's knowledge base.
GLOBAL_PATTERNS = [
    "world/**/*.md",
    "titans/**/*.md",
    "lore/**/*.md",
    "experiment/**/*.md",
    "characters/**/*.md",
    "chrysos-heirs/MASTER-REGISTRY.md",
    "INDEX.md",
]

# Mission files scanned for character-specific passages.
MISSION_PATTERNS = [
    "missions/chapter-*.md",
    "missions/INDEX.md",
    "missions/key-character-moments.md",
    "missions/adventure/*.md",
]


def collect_sources(
    character_id: str,
    databank_dir: str | Path,
) -> List[dict]:
    """Return the list of source descriptors for a character's knowledge base.

    Each descriptor: {"path": Path, "kind": "global"|"profile"|"mission", "filter": bool}
    - filter=True means only chunks mentioning an alias are kept.
    """
    root = Path(databank_dir)
    if not root.exists():
        raise FileNotFoundError(f"Databank directory not found: {root}")

    sources: List[dict] = []

    # 1. Global sources
    for pattern in GLOBAL_PATTERNS:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path.suffix.lower() == ".md":
                sources.append({"path": path, "kind": "global", "filter": False})

    # 2. Profile source (character card -> matching databank profile)
    profile = _find_profile(character_id, root)
    if profile is not None:
        sources.append({"path": profile, "kind": "profile", "filter": False})

    # 3. Mission sources (filtered by alias)
    for pattern in MISSION_PATTERNS:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path.suffix.lower() == ".md":
                sources.append({"path": path, "kind": "mission", "filter": True})

    return _dedupe(sources)


def character_aliases(character_id: str) -> List[str]:
    """Return the alias tokens for a character card ID."""
    return CHARACTER_ALIASES.get(character_id, [character_id])


def _find_profile(character_id: str, root: Path):
    """Map a character card ID to its databank profile markdown (best-effort)."""
    profile_dir = root / "chrysos-heirs"
    candidates = {
        "dan-heng-permansor-terrae": "dan-heng-permansor-terrae.md",
    }
    if character_id in candidates:
        path = profile_dir / candidates[character_id]
        if path.exists():
            return path
    # Fall back: a file whose stem contains the character id or vice versa
    for path in profile_dir.glob("*.md"):
        stem = path.stem.lower()
        if character_id.lower() == stem or character_id.lower() in stem or stem in character_id.lower():
            return path
    return None


def _dedupe(sources: List[dict]) -> List[dict]:
    seen = set()
    result = []
    for s in sources:
        key = str(s["path"])
        if key not in seen:
            seen.add(key)
            result.append(s)
    return result
