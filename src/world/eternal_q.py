# -*- coding: utf-8 -*-
"""Eternal Page — official Special Program Q sit bodies.

Idle figures on the sill are painted Q cutouts (full-body sit), not geometry.
Guests from the same stills never join the thirteen-Heir circle. Tiny 360p
Bilibili stage grabs are research-only. PPG busts remain the emotion face.
"""
from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
CUTOUTS = ROOT / "assets" / "eternal_page" / "q_program" / "cutouts"

# Files that must never be a circle body (other speakers / research extras).
GUEST_STEMS: tuple[str, ...] = (
    "himeko",
    "sunday",
    "witch_guest",
    "mini_companion",
)

# Bilibili 360p stage grabs — too small / muddy for a sill sprite.
BILI_JUNK_MARK = "_bili_"

# Circle Heir → (cutout filename, crop box as fractions L,T,R,B).
# Boxes drop date banners and neighbor/guest bodies. Leftover sofa / branch /
# ice that shares the sit is kept so feet still read as planted.
# anaxa / phainon / evernight have no acceptable sit cutout (bust-only or none).
Q_SIT: dict[str, tuple[str, tuple[float, float, float, float]]] = {
    "tribbie": ("tribbie_v31_swing.png", (0.00, 0.00, 0.70, 0.90)),
    "aglaea": ("aglaea_v31_sit.png", (0.02, 0.20, 0.78, 1.00)),
    "hyacine": ("hyacine_v33_sit.png", (0.18, 0.22, 0.76, 0.90)),
    "castorice": ("castorice_v33_sit.png", (0.10, 0.08, 0.70, 1.00)),
    "cipher": ("cipher_v33_sit.png", (0.10, 0.18, 0.80, 0.86)),
    # 3.8 sofa Cyrene — not cyrene_forms / not Mem. Neighbor hair cropped off.
    "cyrene": ("cyrene_v38_sit.png", (0.18, 0.10, 0.78, 0.94)),
    "mydei": ("mydei_v31_sit.png", (0.18, 0.18, 0.66, 1.00)),
    "cerydra": ("cerydra_v35_sit.png", (0.14, 0.18, 0.68, 1.00)),
    "hysilens": ("hysilens_v35_sit.png", (0.18, 0.18, 0.70, 1.00)),
    # Chimera in his lap is kept (companion prop). Sunday / Himeko cropped out.
    "dan-heng-permansor-terrae": ("dan_heng_pt_v36_sit.png", (0.32, 0.26, 0.66, 0.92)),
}

MIN_SHORT_PX = 120
MIN_LONG_PX = 200
MIN_BYTES = 8000


def guest_cutout_names() -> list[str]:
    names = []
    if not CUTOUTS.is_dir():
        return names
    for path in CUTOUTS.glob("*.png"):
        stem = path.stem.lower()
        if any(g in stem for g in GUEST_STEMS):
            names.append(path.name)
    return names


def source_path(character_id: str) -> Optional[Path]:
    spec = Q_SIT.get(character_id)
    if not spec:
        return None
    name, _box = spec
    if BILI_JUNK_MARK in name or any(g in name.lower() for g in GUEST_STEMS):
        return None
    path = CUTOUTS / name
    if path.is_file() and path.stat().st_size >= MIN_BYTES:
        return path
    return None


def _crop_body(path: Path, box: tuple[float, float, float, float]):
    from PIL import Image

    im = Image.open(path).convert("RGBA")
    w, h = im.size
    l, t, r, b = box
    crop = im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    alpha = crop.split()[-1]
    ab = alpha.getbbox()
    if not ab:
        return None
    crop = crop.crop(ab)
    short, long = min(crop.size), max(crop.size)
    if short < MIN_SHORT_PX or long < MIN_LONG_PX:
        return None
    probe = crop.copy()
    probe.thumbnail((48, 48))
    opaque = sum(1 for px in probe.getdata() if px[3] > 20)
    if opaque < 12:
        return None
    return crop


@lru_cache(maxsize=16)
def body_png(character_id: str) -> Optional[bytes]:
    """Cropped RGBA PNG bytes for the sill body, or None to fall back to PPG."""
    spec = Q_SIT.get(character_id)
    path = source_path(character_id)
    if not spec or path is None:
        return None
    try:
        crop = _crop_body(path, spec[1])
    except Exception:
        return None
    if crop is None:
        return None
    buf = io.BytesIO()
    crop.save(buf, format="PNG")
    data = buf.getvalue()
    if len(data) < MIN_BYTES:
        return None
    return data


def has_q_body(character_id: str) -> bool:
    return body_png(character_id) is not None


# Alias used by the stage renderer.
q_body_png = body_png


def q_body_ids(circle: list[str]) -> list[str]:
    return [cid for cid in circle if has_q_body(cid)]


def ppg_fallback_ids(circle: list[str]) -> list[str]:
    return [cid for cid in circle if not has_q_body(cid)]


# Names used by tests / callers that prefer the older labels.
SITTERS = Q_SIT
GUESTS = frozenset(GUEST_STEMS) | frozenset({"mem", "witch", "himeko", "sunday"})


def sitter_ids() -> tuple[str, ...]:
    return tuple(Q_SIT.keys())
