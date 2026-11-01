# -*- coding: utf-8 -*-
"""Nothing may float in Walk the Land.

    python tools/test_walk_airborne.py

The operator's rule (2026-11-01): the walk scene keeps its ground — sitters,
walkers, grazing beasts — and nothing hangs in the air. This builds a scene that
*contains* every kind that used to float and asserts none of them reaches the
rendered markup, then checks the ground kinds still do.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui_scene_life import pictorial_stage_documents  # noqa: E402

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASSED if cond else FAILED).append(name if cond else f"{name}  [{detail}]")


def scene_with(kinds: list[str]) -> list[dict]:
    return [
        {
            "id": f"{kind}-1",
            "kind": kind,
            "name": kind.title(),
            "clickable": True,
            "doing": "drifting",
            "hotspot": {"left": "40%", "bottom": "55%"},
        }
        for kind in kinds
    ]


def main() -> int:
    airborne = ["kite", "courier", "thief_star", "wind", "grove_leaf",
                "laundry", "banner", "cicada"]
    ground = ["chimera", "dromas", "stall", "hearth"]

    docs = pictorial_stage_documents(
        None, "Okhema", "none", "", scene_with(airborne + ground),
        page_layer=False, entities=True, dense=True,
    )
    html = "\n".join(d if isinstance(d, str) else str(d) for d in docs)
    check("the scene rendered something", len(html) > 500, str(len(html)))

    # Match the scene ids ("kite-1"), not the bare word: kinds such as courier,
    # wind and laundry also name CSS animations, which would give false hits.
    for kind in airborne:
        check(f"{kind} is not drawn", f"{kind}-1" not in html)
    # Positive control: the filter must not be a blanket over the whole scene.
    for kind in ('chimera', 'dromas'):
        check(f"ground {kind} is still drawn", f"{kind}-1" in html)
    check("no sky-classed sprite remains", 'amp-sprite sky' not in html)

    print("== fragment art is not drawn ==")
    # Every pillar file is a right-hand slice of a column cut flat down its left edge,
    # so the stage used to show half a column. The scene now omits the family.
    scenes = scene_with(["pillar", "pillar_okhema", "pillar_grove", "pillar_aidonia"])
    frag = pictorial_stage_documents(
        None, "Okhema", "none", "", scenes + scene_with(["chimera"]),
        page_layer=False, entities=True, dense=True,
    )
    frag_html = "\n".join(frag)
    for kind in ("pillar", "pillar_okhema", "pillar_grove", "pillar_aidonia"):
        check(f"{kind} is not drawn", f"{kind}-1" not in frag_html)
    check("the chimera is still drawn beside them", "chimera-1" in frag_html)
    check("no airborne marker in the payload", '"elevated": true' not in html.lower())

    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    for f in FAILED:
        print("  FAIL", f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
