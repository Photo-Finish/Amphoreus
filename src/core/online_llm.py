"""Remote OpenAI-compatible conversation backend.

The API key lives in a gitignored file (`secrets/online_llm.json`). Visit chat,
group talk, and Heir decide/react use this when the voice path is **online**,
so conversation does not load a local GPU model. The world machine (Keeper
fallback, hearths, streets) stays local.
"""

from __future__ import annotations

import json
from pathlib import Path  # noqa: F401 — kept for call-site type hints

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SECRETS_PATH = PROJECT_ROOT / "secrets" / "online_llm.json"

PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-4o-mini",
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "groq": {
        "label": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
    "custom": {
        "label": "Custom (OpenAI-compatible)",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
}


def _read() -> dict:
    try:
        if SECRETS_PATH.is_file():
            data = json.loads(SECRETS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def load() -> dict:
    """Return the saved remote-LLM settings (api_key may be empty)."""
    data = _read()
    provider = str(data.get("provider") or "openai").strip().lower()
    if provider not in PROVIDERS:
        provider = "openai"
    preset = PROVIDERS[provider]
    key = str(data.get("api_key") or "").strip()
    base = str(data.get("base_url") or "").strip() or preset["base_url"]
    model = str(data.get("model") or "").strip() or preset["model"]
    return {
        "provider": provider,
        "api_key": key,
        "base_url": base.rstrip("/"),
        "model": model,
    }


def save(
    api_key: str,
    *,
    provider: str = "openai",
    base_url: str = "",
    model: str = "",
) -> dict:
    """Write the secrets file. Empty key clears the stored key."""
    provider = str(provider or "openai").strip().lower()
    if provider not in PROVIDERS:
        provider = "custom"
    preset = PROVIDERS[provider]
    payload = {
        "provider": provider,
        "api_key": str(api_key or "").strip(),
        "base_url": (str(base_url or "").strip() or preset["base_url"]).rstrip("/"),
        "model": str(model or "").strip() or preset["model"],
    }
    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SECRETS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def clear_key() -> dict:
    cfg = load()
    return save("", provider=cfg["provider"], base_url=cfg["base_url"], model=cfg["model"])


def has_key() -> bool:
    return bool(load().get("api_key"))


def mask_key(key: str) -> str:
    k = str(key or "").strip()
    if not k:
        return "(none)"
    if len(k) <= 8:
        return "••••" + k[-2:]
    return k[:3] + "…" + k[-4:]


def status() -> dict:
    cfg = load()
    return {
        "configured": bool(cfg["api_key"]),
        "provider": cfg["provider"],
        "base_url": cfg["base_url"],
        "model": cfg["model"],
        "key_masked": mask_key(cfg["api_key"]),
        "path": str(SECRETS_PATH),
    }


_HOME_ATTR = "_amph_home_endpoint"


def _ensure_home(llm) -> None:
    """Snapshot the process-local Ollama endpoint once, before a remote apply."""
    if getattr(llm, _HOME_ATTR, None) is None:
        setattr(
            llm,
            _HOME_ATTR,
            {
                "api_key": llm.api_key,
                "base_url": llm.base_url,
                "model": llm.model,
            },
        )


def restore_local(llm) -> None:
    """Put an LLMClient back on its original local endpoint (Ollama / .env)."""
    home = getattr(llm, _HOME_ATTR, None)
    if not home:
        return
    llm.api_key = home.get("api_key")
    llm.base_url = home.get("base_url")
    if home.get("model"):
        llm.model = home["model"]


def apply_to_client(llm) -> bool:
    """Point an LLMClient at the remote conversation backend. False if no key."""
    cfg = load()
    if not cfg.get("api_key"):
        return False
    _ensure_home(llm)
    llm.api_key = cfg["api_key"]
    llm.base_url = cfg["base_url"]
    llm.model = cfg["model"]
    return True
