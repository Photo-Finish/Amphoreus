"""Frame official area art onto walkable ground.

The HSR wiki only ships cinematic ``Area_*`` establishing shots (sky, Kephale,
the Grove-tree's face). Street-level plaza files are not on the wiki. This
module crops those JPEGs onto pavement, terraces, paths, and stairs so outdoor
sprites can stand on something.

Establishing shots stay in ``assets/galgame/bg-*.jpg`` (Galgame / Map).
Land (Visit / Walk) uses ``assets/galgame/ground/bg-*.jpg``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

GALGAME_DIR = Path(__file__).resolve().parent.parent / "assets" / "galgame"
GROUND_DIR = GALGAME_DIR / "ground"

# Crop box as fractions of the source: (left, top, right, bottom).
# Tuned from the 1600×900 wiki Area arts so the frame holds a floor.
_CROP: dict[str, Tuple[float, float, float, float]] = {
    "okhema": (0.00, 0.36, 0.50, 0.78),          # terrace floor, not the drop-off
    "okhema-evernight": (0.00, 0.34, 0.52, 0.78),
    "aedes-elysiae": (0.00, 0.18, 1.00, 1.00),   # dirt path + boardwalk
    "kremnos": (0.10, 0.42, 0.90, 1.00),         # bridge pavement
    "kremnos-ruins": (0.08, 0.40, 0.92, 1.00),
    "grove": (0.08, 0.42, 0.78, 0.82),           # root-terrace buildings
    "murmuring-woods": (0.16, 0.24, 0.86, 0.74), # stone platforms, not mist
    "styxia": (0.00, 0.32, 0.64, 0.78),          # arched terrace, not the water
    "dragonbone-city": (0.00, 0.30, 0.68, 0.78),
    "janusopolis": (0.18, 0.48, 0.82, 1.00),     # stair ground
    "abyss-of-fate": (0.16, 0.46, 0.84, 1.00),
    "memortis-shore": (0.00, 0.38, 0.58, 1.00),  # left path
    "dawncloud": (0.06, 0.30, 0.94, 1.00),
    "lightless-chapel": (0.10, 0.38, 0.90, 1.00),
    "eye-of-twilight": (0.08, 0.36, 0.92, 1.00),
    "cloudedge-bastion": (0.08, 0.38, 0.92, 1.00),
    "great-tomb": (0.10, 0.40, 0.90, 1.00),
    "nightmare-echo": (0.10, 0.40, 0.90, 1.00),
    "beyond-time": (0.08, 0.34, 0.92, 1.00),
    "vortex-of-genesis": (0.12, 0.28, 0.88, 0.95),
}

_DEFAULT_CROP = (0.00, 0.34, 1.00, 1.00)


def _slug_of(path: Path) -> str:
    stem = path.stem.lower()
    return stem[3:] if stem.startswith("bg-") else stem


def _box_for(path: Path) -> Tuple[float, float, float, float]:
    return _CROP.get(_slug_of(path), _DEFAULT_CROP)


def write_ground_jpeg(src: Path, dest: Optional[Path] = None) -> Path:
    """Crop one establishing JPEG onto its ground plane."""
    from PIL import Image

    src = Path(src)
    dest = Path(dest) if dest else GROUND_DIR / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    w, h = im.size
    l, t, r, b = _box_for(src)
    box = (
        int(w * l),
        int(h * t),
        max(int(w * l) + 8, int(w * r)),
        max(int(h * t) + 8, int(h * b)),
    )
    crop = im.crop(box)
    crop.save(dest, "JPEG", quality=92)
    return dest


def ensure_grounded(path) -> Optional[Path]:
    """Land art: a ground-framed JPEG if this is area art, else the original."""
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return p
    if p.parent.resolve() == GROUND_DIR.resolve():
        return p
    if p.parent.resolve() != GALGAME_DIR.resolve() and p.name != "amphoreus_bg.jpg":
        return p
    dest = GROUND_DIR / (p.name if p.stem.startswith("bg-") else f"bg-{p.stem}.jpg")
    try:
        if dest.is_file() and dest.stat().st_mtime >= p.stat().st_mtime:
            return dest
        return write_ground_jpeg(p, dest)
    except Exception:
        return p


def reframe_all() -> list:
    """Write/refresh every ``ground/bg-*.jpg``. Returns [(slug, path), ...]."""
    out = []
    GROUND_DIR.mkdir(parents=True, exist_ok=True)
    for src in sorted(GALGAME_DIR.glob("bg-*.jpg")):
        dest = write_ground_jpeg(src)
        out.append((_slug_of(src), dest))
    return out


if __name__ == "__main__":
    for slug, dest in reframe_all():
        print(f"  {slug} -> {dest}")
