# -*- coding: utf-8 -*-
"""Draw the phone app's launcher icon from the project's own colours.

    python android/make_icon.py

Writes `android/app/res/mipmap-xxxhdpi/ic_launcher.png` (192 px). The motif is the
Eternal Page's: the Vortex star-field behind a chrysos-gold four-point star. No
external art is used, so the icon cannot drift from the project's palette.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "android" / "app" / "res" / "mipmap-xxxhdpi" / "ic_launcher.png"
SIZE = 192
# The parchment's own darks and the gold the sill's name plates use.
NIGHT = (11, 18, 36)
DEEP = (26, 38, 74)
GOLD = (247, 237, 210)
GOLD_DIM = (228, 196, 128)


def star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, inner: float,
         fill) -> None:
    """A four-point star: the page's own motif, not a generic icon."""
    pts = []
    for i in range(8):
        angle = math.pi / 2 * (i / 2.0) - math.pi / 2
        radius = r if i % 2 == 0 else inner
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    draw.polygon(pts, fill=fill)


def main() -> int:
    # Radial night sky.
    sky = Image.new("RGB", (SIZE, SIZE), NIGHT)
    px = sky.load()
    cx, cy = SIZE * 0.5, SIZE * 0.46
    for y in range(SIZE):
        for x in range(SIZE):
            d = math.hypot(x - cx, y - cy) / (SIZE * 0.72)
            t = min(1.0, max(0.0, d))
            px[x, y] = tuple(
                int(DEEP[i] * (1 - t) + NIGHT[i] * t) for i in range(3)
            )
    img = sky.convert("RGBA")

    # A soft halo behind the star.
    halo = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([cx - 52, cy - 52, cx + 52, cy + 52], fill=(228, 196, 128, 70))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(16)))

    # The star, with a smaller echo above-left like the page's sparkles.
    d = ImageDraw.Draw(img)
    star(d, cx, cy, 62, 15, GOLD)
    star(d, cx - 44, cy - 40, 13, 3.5, GOLD_DIM)
    star(d, cx + 46, cy + 34, 9, 2.5, GOLD_DIM)

    # Inner ring, so the icon reads at small sizes too.
    ring = ImageDraw.Draw(img)
    ring.ellipse([cx - 74, cy - 74, cx + 74, cy + 74], outline=(228, 196, 128, 120),
                 width=2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGBA").save(OUT, "PNG")
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size} bytes, {SIZE}px)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
