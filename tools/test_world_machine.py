# -*- coding: utf-8 -*-
"""World machine vs conversation: 1x period sync, month-gated Keeper, rest sprites."""
from __future__ import annotations

import os
import sys
from pathlib import Path

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

    print("== world machine ticks on CPU without CUDA ==")
    import tempfile
    from unittest.mock import patch

    prev_cpu = os.environ.get("AMP_WORLD_CPU")
    prev_keeper = os.environ.get("AMP_KEEPER_LLM")
    os.environ["AMP_WORLD_CPU"] = "1"
    os.environ.pop("AMP_KEEPER_LLM", None)
    tmp = Path(tempfile.mkdtemp(prefix="amp-wm-cpu-"))
    llm_calls = []

    def _gpu_boom(*_a, **_k):
        llm_calls.append(True)
        raise RuntimeError("CUDA unavailable")

    try:
        from src.core.llm_client import LLMClient
        from src.world.world_engine import WorldEngine
        import src.core.local_compute as lc
        lc._NVIDIA_CACHE = None
        with patch("src.core.local_compute.nvidia_present", return_value=False), \
             patch.object(LLMClient, "list_models", side_effect=_gpu_boom), \
             patch.object(LLMClient, "chat", side_effect=_gpu_boom):
            engine = WorldEngine(
                state_path=str(tmp / "world_state.json"),
                chronicle_path=str(tmp / "chronicle"),
                stop_path=str(tmp / "stop.flag"),
                memory_root=str(tmp),
            )
            engine.director.cache_path = str(tmp / "ambient_cache.json")
            engine.director._cache = {}
            engine.world.time_scale = 2.0
            lines = engine.run_day()
            check("CPU tick wrote chronicle lines", bool(lines), repr(lines)[:180])
            check("CPU tick did not call local GPU LLM",
                  not llm_calls, f"calls={len(llm_calls)}")
            weather = (engine.world.ambient or {}).get("weather") or {}
            check("CPU Keeper fallback set weather",
                  bool(weather), str(weather)[:160])
            check("torch was not imported for the tick",
                  "torch" not in sys.modules)
            check("patched nvidia_present is False",
                  lc.nvidia_present() is False)
    finally:
        if prev_cpu is None:
            os.environ.pop("AMP_WORLD_CPU", None)
        else:
            os.environ["AMP_WORLD_CPU"] = prev_cpu
        if prev_keeper is None:
            os.environ.pop("AMP_KEEPER_LLM", None)
        else:
            os.environ["AMP_KEEPER_LLM"] = prev_keeper

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILED:", ", ".join(FAILED))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
