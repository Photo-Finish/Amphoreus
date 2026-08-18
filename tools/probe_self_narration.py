# -*- coding: utf-8 -*-
"""Live probe: which Heirs still wrap speech in self-narration.

Does not write Heir history or world_state. Prints raw vs sanitized.

    D:\\Workspace\\.venv\\Scripts\\python.exe tools\\probe_self_narration.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:11434/v1"
os.environ["OPENAI_API_KEY"] = "ollama"

from src.core.agent_manager import AgentManager
from src.core.heir_folders import HEIR_FOLDERS
from src.core.speech_sanitize import has_self_narration, spoken_words
from src.core.voice_path import get_voice_path, set_voice_path

PROMPT = (
    "Tell me about your journey here — any insights or challenges "
    "you've encountered."
)
OUT = ROOT / "world_runtime" / "_probe_narration.json"


def _mute_persist(mgr: AgentManager) -> None:
    mgr.memory.record_visit = lambda *a, **k: None
    mgr.memory.add_history = lambda *a, **k: None
    mgr.memory.add_memory = lambda *a, **k: None
    mgr._echo_visit = lambda *a, **k: None
    mgr._social_reactions = lambda *a, **k: None
    mgr._note_overhear = lambda *a, **k: None
    mgr._witness_realization = lambda *a, **k: None
    mgr._note_mind = lambda *a, **k: None


def main() -> None:
    prev_path = get_voice_path()
    if prev_path != "rag":
        set_voice_path("rag")
        print(f"voice_path {prev_path} -> rag (needed for 14B GPU)")

    mgr = AgentManager(
        llm_model="qwen2.5:14b-instruct",
        use_rag=False,
        llm_base_url="http://127.0.0.1:11434/v1",
        llm_api_key="ollama",
    )
    mgr.llm.max_tokens = 280
    mgr._restore_session = lambda *a, **k: None
    _mute_persist(mgr)
    raw_box: dict = {}
    orig_call = mgr._call_llm

    def _capture(messages, stream=False):
        text = orig_call(messages, stream=stream)
        raw_box["raw"] = text
        return text

    mgr._call_llm = _capture

    results = []
    print(f"model={mgr.llm.model} voice_path={get_voice_path()}")
    print(f"prompt: {PROMPT}\n")

    for cid in HEIR_FOLDERS:
        raw_box.clear()
        t0 = time.time()
        print(f"-- {cid} --", flush=True)
        try:
            cleaned = mgr.chat(cid, PROMPT)
        except Exception as e:
            rec = {
                "id": cid,
                "ok": False,
                "error": str(e),
                "seconds": round(time.time() - t0, 1),
            }
            results.append(rec)
            print(f"  ERROR {e}", flush=True)
            continue
        raw = raw_box.get("raw") if isinstance(raw_box.get("raw"), str) else cleaned
        flagged = has_self_narration(raw)
        still = has_self_narration(cleaned)
        rec = {
            "id": cid,
            "ok": True,
            "seconds": round(time.time() - t0, 1),
            "raw_narration": flagged,
            "cleaned_narration": still,
            "raw_preview": (raw or "")[:400],
            "cleaned_preview": (cleaned or "")[:400],
        }
        results.append(rec)
        mark = "NARRATE" if flagged else "clean"
        print(f"  {mark}  {rec['seconds']}s  still={still}", flush=True)
        print(f"  raw: {(raw or '')[:220].replace(chr(10), ' / ')}", flush=True)
        if flagged:
            print(
                f"  out: {(cleaned or '')[:220].replace(chr(10), ' / ')}",
                flush=True,
            )

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    narrators = [r["id"] for r in results if r.get("raw_narration")]
    leftover = [r["id"] for r in results if r.get("cleaned_narration")]
    errors = [r["id"] for r in results if not r.get("ok")]
    print("\nraw narrators:", ", ".join(narrators) or "(none)")
    print("sanitizer leftover:", ", ".join(leftover) or "(none)")
    print("errors:", ", ".join(errors) or "(none)")
    print("wrote", OUT)

    if prev_path != get_voice_path() and prev_path:
        # Leave RAG on so 14B can stay loaded; caller may switch back.
        pass


if __name__ == "__main__":
    main()
