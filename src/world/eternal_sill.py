# -*- coding: utf-8 -*-
"""Eternal Page sill bodies — prefer the second-pass matte when it exists.

`tools/cut_q_program.py` cut each Q sit from its announcement still but kept the
sit furniture, so feet would read as planted. At the sill's 140 px that leftover
bench and floor read as a rectangular slab of the source photograph.
`tools/matte_sill.py` writes a cleaner body to `cutouts_matte/`; this module is
the lookup the page asks first.

Nothing is deleted or rewritten: the first-pass `cutouts/` remain the record, the
catalog, and the fallback. Remove `cutouts_matte/` (or call `has_body` false) and
the page is exactly as it was.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from src.world.eternal_q import Q_SIT

ROOT = Path(__file__).resolve().parents[2]
MATTE_DIR = ROOT / "assets" / "eternal_page" / "q_program" / "cutouts_matte"
MANIFEST = MATTE_DIR / "manifest.json"
# Below this a file is a placeholder, not art (same rule the first pass uses).
MIN_BYTES = 4000


# Where a second-pass body is not named after the first-pass file it shadows.
# anaxa: the first-pass `anaxa_v34_sit.png` is the Trailblazer, not Anaxa, so the
# corrected body is the 3.4 announcement bust under its own honest name.
ALIAS = {
    "anaxa": "anaxa_v34_announcement_bust.png",
    "phainon": "phainon_v34_announcement_bust.png",
}


def matte_path(character_id: str) -> Optional[Path]:
    """The second-pass file for this Heir, or None when there is no usable one."""
    spec = Q_SIT.get(character_id)
    if not spec:
        return None
    path = MATTE_DIR / ALIAS.get(character_id, spec[0])
    if path.is_file() and path.stat().st_size > MIN_BYTES:
        return path
    return None


def has_body(character_id: str) -> bool:
    return matte_path(character_id) is not None


def ids() -> list[str]:
    return [cid for cid in Q_SIT if has_body(cid)]


@lru_cache(maxsize=32)
def body_png(character_id: str) -> Optional[bytes]:
    """RGBA PNG bytes for the cleaned sill body, or None to fall back to the cut."""
    path = matte_path(character_id)
    if path is None:
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


@lru_cache(maxsize=1)
def manifest() -> dict:
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return {}


def covered(character_id: str) -> Optional[float]:
    """Fraction of the first-pass silhouette the matte keeps (from the manifest)."""
    row = manifest().get(character_id)
    if isinstance(row, dict) and "covered" in row:
        try:
            return float(row["covered"])
        except (TypeError, ValueError):
            return None
    return None
