# -*- coding: utf-8 -*-
"""Walkers must face the way they walk.

    python tools/test_walk_orientation.py

The stage mirrors a walker with `scaleX(-1)` when its travel direction opposes the
direction its ART faces. Two things have to stay true for that to look right:

  * every art family reports the way its art actually faces (people face LEFT,
    chimeras and dromas face RIGHT) — including the named variants such as
    `resident_weaver`, which used to fall through to the default and walked
    backwards in both directions;
  * the mirror decision follows travel, not a timer. The old `amp-sprite-face-r/l`
    animation flipped the figure at the midpoint of every crossing, so a one-way
    walk turned round halfway.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui_scene_life import (  # noqa: E402
    _native_facing, _sprite_facing_class,
)

SPRITES = ROOT / "assets" / "life_sprites"
PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASSED if cond else FAILED).append(name if cond else f"{name}  [{detail}]")


def mirrors(native: str, travels_right: bool) -> bool:
    """The rule the roam JS applies: mirror when travel opposes the art."""
    return travels_right != (native == "right")


def main() -> int:
    # 1. every resident variant is left-facing art
    residents = sorted({p.stem.split("_f")[0].split("_pet")[0]
                        for p in SPRITES.glob("resident*.png")})
    check("found the resident art", len(residents) >= 10, str(len(residents)))
    for stem in residents:
        if stem.endswith("_film"):
            continue
        check(f"{stem}: art faces left", _native_facing(stem) == "left",
              _native_facing(stem))

    # 2. creatures face right
    for stem in ("chimera", "chimera_pink", "chimera_blue", "chimera_orange",
                 "chimera_purple", "dromas", "dromas_calf"):
        check(f"{stem}: art faces right", _native_facing(stem) == "right",
              _native_facing(stem))

    # 3. the class the still renderer emits agrees with the facing
    check("resident_weaver still class is face-l",
          _sprite_facing_class("resident_weaver") == " face-l")
    check("chimera_pink still class is face-r",
          _sprite_facing_class("chimera_pink") == " face-r")

    # 4. the mirror rule itself, in the four combinations
    check("person walking right is mirrored", mirrors("left", True) is True)
    check("person walking left is not mirrored", mirrors("left", False) is False)
    check("creature walking right is not mirrored", mirrors("right", True) is False)
    check("creature walking left is mirrored", mirrors("right", False) is True)

    # 5. the flip must not be timer-driven inside a single crossing: the roamer
    #    rules pin the transform and switch the face animation off.
    css = (ROOT / "src" / "ui_scene_life.py").read_text(encoding="utf-8")
    roamer_block = css[css.index(".amp-sprite.amp-roamer {"):]
    roamer_block = roamer_block[:roamer_block.index("/* face-r = keep native art")]
    check("roamers disable the timed face animation",
          "animation: none !important" in roamer_block,
          "animation still runs")
    check("roamer facing is a static transform",
          "transform: scaleX(1)" in css and "transform: scaleX(-1)" in css)
    check("no timed flip keyframes are applied to roamers",
          not re.search(r"\.amp-sprite\.amp-roamer[^{]*\{[^}]*amp-sprite-face", css),
          "a roamer still uses amp-sprite-face-*")

    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    for f in FAILED:
        print("  FAIL", f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
