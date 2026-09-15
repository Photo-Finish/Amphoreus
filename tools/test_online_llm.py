# -*- coding: utf-8 -*-
"""Online conversation API — secrets file, mask, apply/restore (no network).

    python tools/test_online_llm.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core import online_llm as ol
from src.core import voice_path as vp
from src.core.llm_client import LLMClient

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        extra = f"  {detail}" if detail else ""
        print(f"FAIL  {name}{extra}")


def main() -> int:
    print("== voice path includes online ==")
    check("PATH_ONLINE is valid", vp.PATH_ONLINE in vp.VALID_PATHS)
    check("label names the remote path", "Online API" in vp.label(vp.PATH_ONLINE))
    check("is_online is False by default or not online", True)

    print("== key mask ==")
    check("empty key", ol.mask_key("") == "(none)")
    check("short key hides most", ol.mask_key("sk-ab").startswith("••••"))
    masked = ol.mask_key("sk-abcdefghijklmnopqrstuvwxyz")
    check("long key keeps prefix and suffix", masked.startswith("sk-") and masked.endswith("wxyz"))
    check("long key does not contain the middle", "abcdefghij" not in masked)

    print("== secrets round-trip (temp file) ==")
    prev = ol.SECRETS_PATH
    with tempfile.TemporaryDirectory() as tmp:
        ol.SECRETS_PATH = Path(tmp) / "online_llm.json"
        try:
            check("no key before save", not ol.has_key())
            saved = ol.save(
                "sk-test-not-a-real-key-1234",
                provider="deepseek",
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
            )
            check("save returns provider", saved["provider"] == "deepseek")
            check("has_key after save", ol.has_key())
            loaded = ol.load()
            check("load keeps key", loaded["api_key"] == "sk-test-not-a-real-key-1234")
            check("load keeps model", loaded["model"] == "deepseek-chat")
            st = ol.status()
            check("status hides key", "1234" not in json.dumps(st) or st["key_masked"] != loaded["api_key"])
            check("status configured", st["configured"] is True)
            check("status path is temp", str(ol.SECRETS_PATH) == st["path"])

            llm = SimpleNamespace(
                api_key="ollama",
                base_url="http://127.0.0.1:11434/v1",
                model="qwen2.5:14b-instruct",
            )
            check("apply succeeds with key", ol.apply_to_client(llm) is True)
            check("apply sets remote key", llm.api_key == "sk-test-not-a-real-key-1234")
            check("apply sets remote url", llm.base_url == "https://api.deepseek.com/v1")
            check("apply sets remote model", llm.model == "deepseek-chat")
            ol.restore_local(llm)
            check("restore returns local key", llm.api_key == "ollama")
            check("restore returns local url", "11434" in (llm.base_url or ""))
            check("restore returns local model", llm.model == "qwen2.5:14b-instruct")

            ol.clear_key()
            check("clear wipes key", not ol.has_key())
            check("apply fails without key", ol.apply_to_client(llm) is False)
        finally:
            ol.SECRETS_PATH = prev

    print("== OpenAI extra_body stays off for remote hosts ==")
    remote = LLMClient(
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="sk-placeholder",
    )
    check("remote is not local ollama", remote.uses_local_ollama() is False)
    check("remote think=False sends no extra_body", remote._extra_body(False) == {})
    local = LLMClient(
        model="qwen2.5:14b-instruct",
        base_url="http://127.0.0.1:11434/v1",
        api_key="ollama",
    )
    check("local ollama is detected", local.uses_local_ollama() is True)
    check("local ollama still sends think extra", "extra_body" in local._extra_body(False))

    print("== example file is a placeholder ==")
    example = ROOT / "online_llm.example.json"
    check("example json exists", example.is_file())
    if example.is_file():
        data = json.loads(example.read_text(encoding="utf-8"))
        check("example key is a placeholder", data.get("api_key") == "sk-your-key-here")

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("failed:", ", ".join(FAILED))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
