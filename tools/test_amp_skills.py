"""Unit checks for optional Amphoreus skills aid (no LLM required)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import src.core.amp_skills as amp_skills  # noqa: E402
from src.core.amp_skills import (  # noqa: E402
    baseline_skill_block,
    maybe_inject,
    refined_skill_block,
    set_skills_enabled,
    skills_enabled,
)
from src.core.context_builder import ContextBuilder  # noqa: E402


def test_prefer_voice_hits_orders_mission_first():
    hits = [
        {"kind": "global", "score": 0.9, "text": "g"},
        {"kind": "mission", "score": 0.5, "text": "m"},
        {"kind": "profile", "score": 0.8, "text": "p"},
    ]
    ordered = ContextBuilder.prefer_voice_hits(hits)
    assert [h["kind"] for h in ordered] == ["mission", "profile", "global"]


def test_format_context_voice_bias_note():
    cb = ContextBuilder()
    text = cb.format_context(
        [{"kind": "mission", "source": "missions/x.md", "text": "Hello."}],
        voice_bias=True,
    )
    assert "VOICE:" in text
    assert "kind: mission" in text


def test_toggle_and_inject():
    prev_path = amp_skills.RUNTIME_PATH
    prev_env = os.environ.get("AMP_SKILLS")
    try:
        with tempfile.TemporaryDirectory() as td:
            amp_skills.RUNTIME_PATH = Path(td) / "amp_skills.json"
            os.environ.pop("AMP_SKILLS", None)

            set_skills_enabled(False)
            assert skills_enabled() is False
            assert maybe_inject("BASE", "phainon") == "BASE"

            set_skills_enabled(True)
            assert skills_enabled() is True
            out = maybe_inject("BASE", "phainon")
            assert out.startswith("BASE")
            assert "Skills aid" in out or "measured card voice" in out

            os.environ["AMP_SKILLS"] = "0"
            assert skills_enabled() is False
            os.environ["AMP_SKILLS"] = "1"
            assert skills_enabled() is True

            assert "verbatim" in baseline_skill_block().lower()
            assert "encyclopedia" in refined_skill_block("tribbie").lower()
            assert amp_skills.RUNTIME_PATH.is_file()
            data = json.loads(amp_skills.RUNTIME_PATH.read_text(encoding="utf-8"))
            assert "enabled" in data
    finally:
        amp_skills.RUNTIME_PATH = prev_path
        if prev_env is None:
            os.environ.pop("AMP_SKILLS", None)
        else:
            os.environ["AMP_SKILLS"] = prev_env


if __name__ == "__main__":
    test_prefer_voice_hits_orders_mission_first()
    test_format_context_voice_bias_note()
    test_toggle_and_inject()
    print("ok")
