# -*- coding: utf-8 -*-
"""Residents must walk in ONE orientation, and face the way they travel.

    python tools/test_resident_walk.py

The shipped `resident_*_film.png` strips contain four DIFFERENT orientations (left
profile, three-quarter, front, front-standing), so playing them spins the figure while
it slides along the ground. `resident_*_walk_film.png` is built from frame 1 and keeps a
single orientation, swinging its legs instead.

The test measures the figure's silhouette per frame: a spinning strip changes width and
centre dramatically, a walking strip does not. It uses the OLD strips as the negative
control, so the metric is proven to catch the bug rather than merely pass.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui_scene_life import (  # noqa: E402
    _native_facing, _resident_walk_stem, _sprite_markup, sprite_film_uri,
)

SPRITES = ROOT / "assets" / "life_sprites"
PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASSED if cond else FAILED).append(name if cond else f"{name}  [{detail}]")


def frames(path: Path) -> list[np.ndarray]:
    im = Image.open(path).convert("RGBA")
    fw = im.width // 4
    return [np.array(im.crop((i * fw, 0, (i + 1) * fw, im.height)))[:, :, 3] > 16
            for i in range(4)]


def profile(masks: list[np.ndarray]) -> tuple[float, float]:
    """Upper-body silhouette spread across frames.

    Orientation lives in the torso and head, not the legs: a walking cycle swings its
    legs (so the whole silhouette's centre moves) while the shoulders stay put. A strip
    that SPINS changes the head's width and centre drastically. So measure the top 30%.
    """
    centres, widths = [], []
    for m in masks:
        top = m[: max(1, int(m.shape[0] * 0.30))]
        cols = np.where(top.any(axis=0))[0]
        if not len(cols):
            return 999.0, 999.0
        centres.append((cols.min() + cols.max()) / 2)
        widths.append(cols.max() - cols.min())
    return float(max(centres) - min(centres)), float(max(widths) - min(widths))


def motion(masks: list[np.ndarray]) -> float:
    return float(np.mean([np.logical_xor(masks[i], masks[i - 1]).sum() for i in range(1, 4)]))


def main() -> int:
    variants = sorted(p.stem.replace("_walk_film", "")
                      for p in SPRITES.glob("resident*_walk_film.png"))
    check("a walk strip exists for every resident", len(variants) >= 11, str(len(variants)))

    for stem in variants:
        new = SPRITES / f"{stem}_walk_film.png"
        old = SPRITES / f"{stem}_film.png"
        check(f"{stem}: walk strip exists", new.is_file())
        if not new.is_file():
            continue
        masks = frames(new)
        centre_spread, width_spread = profile(masks)
        check(f"{stem}: orientation holds through the cycle",
              centre_spread <= 2.0 and width_spread <= 3.0,
              f"centre spread {centre_spread:.1f}px, width spread {width_spread:.1f}px")
        check(f"{stem}: the legs actually move", motion(masks) > 150, f"{motion(masks):.0f}px")

        if old.is_file():
            o_centre, o_width = profile(frames(old))
            check(f"{stem}: the old strip really did spin (negative control)",
                  o_centre > 2.0 or o_width > 3.0,
                  f"old centre {o_centre:.1f}px, width {o_width:.1f}px")

    # every resident faces left natively, so rightward travel must mirror it
    for kind in ("resident", "resident_guard", "resident_weaver", "resident_smith"):
        check(f"{kind}: art faces left", _native_facing(kind) == "left")
        check(f"{kind}: renders the walk strip",
              sprite_film_uri(_resident_walk_stem(kind))[:120]
              in _sprite_markup(kind, asset=kind))

    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    for f in FAILED:
        print("  FAIL", f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
