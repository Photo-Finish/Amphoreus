# -*- coding: utf-8 -*-
"""World machine vs conversation: 1x period sync, month-gated Keeper, rest sprites."""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from src.core.visitor_mode import journey_sidebar_caption
from src.ui_scene_life import _sprite_motion_class
from src.world.ambient import AmbientDirector, NEWS_PALETTE, _text_fits_month
from src.world.sanctuary_clock import WorldClock, overlay_period_key

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def main():
    print("== month-gated Keeper fallback ==")
    check("Phagousa news is Joy-bound",
          not _text_fits_month(
              "The Festival of Phagousa rehearsals begin in Dawncloud.", 10
          ))
    check("Phagousa news fits Month of Joy",
          _text_fits_month(
              "The Festival of Phagousa rehearsals begin in Dawncloud.", 5
          ))
    check("Thief Star news is month-free",
          _text_fits_month(
              "The Thief Star burned crimson over Okhema last night.", 10
          ))
    strife = WorldClock(year=4933, month=10, week=1, day=7, period=2)
    director = AmbientDirector()
    heirs = {
        "aglaea": {"name": "Aglaea", "home": "Okhema", "title": "Goldweaver"},
        "hyacine": {"name": "Hyacine", "home": "Grove of Epiphany", "title": "Healer"},
    }
    amb = director._fallback(strife, heirs)
    news = amb.get("news") or ""
    check("Strife fallback news is not a Joy feast",
          "phagousa" not in news.lower(), news)
    err_blob = " ".join(
        f"{(v or {}).get('ask', '')} {(v or {}).get('cause', '')}"
        for v in (amb.get("errands") or {}).values()
    )
    check("Strife fallback errands are not Reaping",
          "month of reaping" not in err_blob.lower(), err_blob[:160])
    check("palette still has a Joy-only line for Joy days",
          any("Phagousa" in n for n in NEWS_PALETTE))

    print("== overlay period key ==")
    c = WorldClock(year=4933, month=10, week=1, day=7, period=0)
    k = overlay_period_key(c)
    check("key keeps Entry Hour", k.get("period") == 0)
    check("key keeps Strife month", k.get("month") == 10)

    print("== journey caption follows the bond ==")
    check("stranger + no visits is newly arrived",
          "newly arrived" in journey_sidebar_caption(
              {"friendship_level": "stranger", "visits": 0}
          ))
    check("best friend is already known",
          "already know you" in journey_sidebar_caption(
              {"friendship_level": "best friend", "visits": 70}
          ))

    print("== rest-hour sprites stay still ==")
    check("resting chimera is still",
          _sprite_motion_class("chimera", "resting") == " still")
    check("wandering chimera is mobile",
          _sprite_motion_class("chimera", "wandering") == " mobile")
    check("resting dromas is still",
          _sprite_motion_class("dromas", "resting") == " still")

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILED:", ", ".join(FAILED))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
