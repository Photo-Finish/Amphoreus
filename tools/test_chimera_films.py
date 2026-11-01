# -*- coding: utf-8 -*-
"""The chimera side-view walk and roar strips: present, animated, and wired.

    python tools/test_chimera_films.py

A strip that contains four copies of the same frame looks exactly like the bug the
operator reported ("still not animated"), so this measures the frames against each
other rather than trusting that the files exist.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui_scene_life import (  # noqa: E402
    _chimera_side_stem, _sprite_markup, sprite_film_uri,
)

SPRITES = ROOT / "assets" / "life_sprites"
FRAME = 184
VARIANTS = ("", "_pink", "_blue", "_orange", "_purple")
PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASSED if cond else FAILED).append(name if cond else f"{name}  [{detail}]")


def frames_of(path: Path) -> list[np.ndarray]:
    im = Image.open(path).convert("RGBA")
    check(f"{path.name}: is a 4-frame horizontal strip",
          im.width == FRAME * 4 and im.height == FRAME, f"{im.size}")
    return [np.array(im.crop((i * FRAME, 0, (i + 1) * FRAME, FRAME)), dtype=float)
            for i in range(4)]


def motion(frames: list[np.ndarray]) -> float:
    """Mean absolute difference between consecutive frames (alpha included)."""
    return float(np.mean([np.abs(frames[i] - frames[i - 1]).mean()
                          for i in range(1, len(frames))]))


def main() -> int:
    for suffix in VARIANTS:
        stem = "chimera_side" + suffix
        walk_path = SPRITES / f"{stem}_film.png"
        roar_path = SPRITES / f"{stem}_roar_film.png"
        check(f"{walk_path.name}: exists", walk_path.is_file())
        check(f"{roar_path.name}: exists", roar_path.is_file())
        if not (walk_path.is_file() and roar_path.is_file()):
            continue
        walk, roar = frames_of(walk_path), frames_of(roar_path)
        check(f"{stem}: the walk frames actually differ",
              motion(walk) > 1.0, f"mean|Δ|={motion(walk):.2f}")
        check(f"{stem}: the roar frames actually differ",
              motion(roar) > 1.0, f"mean|Δ|={motion(roar):.2f}")
        check(f"{stem}: the roar is not the walk",
              float(np.mean([np.abs(roar[i] - walk[i]).mean() for i in range(4)])) > 1.0)

    # the stem used by the renderer
    check("base chimera maps to the base side strip",
          _chimera_side_stem("chimera") == "chimera_side")
    check("a variant maps to its own strip",
          _chimera_side_stem("chimera_pink") == "chimera_side_pink")
    check("non-chimeras have no side strip",
          _chimera_side_stem("dromas") == "" and _chimera_side_stem("resident") == "")

    # the renderer prefers the side strip, not the old front-facing one
    for kind in ("chimera", "chimera_pink", "chimera_blue", "chimera_orange",
                 "chimera_purple"):
        markup = _sprite_markup(kind, asset=kind)
        side = sprite_film_uri(_chimera_side_stem(kind))
        front = sprite_film_uri(kind)
        check(f"{kind}: renders the side-view walk",
              bool(side) and side[:120] in markup)
        check(f"{kind}: does not render the old front strip",
              not (front and front[:120] in markup))

    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    for f in FAILED:
        print("  FAIL", f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
