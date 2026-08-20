"""Optional Amphoreus Cursor-skills aid for RAG-mode Heir speech.

Skills under `.cursor/skills/` guide agents on retrieval/charter. When this
switch is ON, a compact runtime block is appended after Chroma RAG so the
LLM uses those skills as *retrieval + voice discipline* — never as a
generic lore-bot persona.

Default: OFF (optional). Override with env `AMP_SKILLS=1` / `AMP_SKILLS=0`,
or Control Panel / `world_runtime/amp_skills.json`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PATH = PROJECT_ROOT / "world_runtime" / "amp_skills.json"
SKILLS_DIR = PROJECT_ROOT / ".cursor" / "skills"

# Thin inject used for A/B baseline ("skills as originally written").
BASELINE_SKILL_BLOCK = """
# Amphoreus skills (databank RAG + charter) — baseline
- Do not invent lore; ground answers in retrieved Knowledge excerpts and the Heir card.
- Prefer verbatim mission dialogue lines for voice; paraphrase only when summarizing.
- Stay behind the knowledge wall: Amphoreus only (no Earth / modern science / machines).
- If excerpts are low-confidence, prefer the Heir profile over weak hits.
- Operator experiment docs are not Heir dialogue fuel.
""".strip()


def _read() -> dict:
    try:
        if RUNTIME_PATH.is_file():
            data = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _write(data: dict) -> None:
    RUNTIME_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _env_override() -> Optional[bool]:
    raw = (os.environ.get("AMP_SKILLS") or "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return None


def skills_enabled() -> bool:
    """Whether to inject the skills aid into RAG-mode chat. Default OFF."""
    env = _env_override()
    if env is not None:
        return env
    return bool(_read().get("enabled", False))


def set_skills_enabled(enabled: bool) -> bool:
    data = _read()
    data["enabled"] = bool(enabled)
    _write(data)
    return bool(enabled)


def skills_available() -> bool:
    return (SKILLS_DIR / "amphoreus-databank-rag" / "SKILL.md").is_file()


def label(enabled: Optional[bool] = None) -> str:
    on = skills_enabled() if enabled is None else bool(enabled)
    return "Skills aid ON (optional RAG voice/retrieval)" if on else "Skills aid OFF (default)"


def baseline_skill_block() -> str:
    """Original thin skill rules — for A/B comparison only."""
    return BASELINE_SKILL_BLOCK


def refined_skill_block(character_id: Optional[str] = None) -> str:
    """Voice-first skills inject for runtime RAG when the switch is ON.

    Keep this short — long policy text flattens delivery into generic assistant.
    Skills sharpen retrieval + anti-lore-bot discipline; the card owns the voice.
    """
    cid = (character_id or "").strip() or "this Heir"
    return f"""
# Skills aid (optional) - for {cid}
- Speak ONLY in your measured card voice (length, rhythm, tics). Style beats lore dump.
- Prefer mission-dialogue excerpts for how you talk; use other excerpts for facts only.
- Never become an encyclopedia or tour guide. No narration / stage directions / name prefix.
- Do not invent lore; ignore low-confidence excerpts. Knowledge wall: Amphoreus only.
- If a fact needs a lecture that would not sound like you, stay brief in your voice or say you do not know.
""".strip()


def skill_prompt_block(character_id: Optional[str] = None, *, variant: str = "refined") -> str:
    """Build the inject block. `variant`: 'refined' (default) or 'baseline'."""
    if variant == "baseline":
        return baseline_skill_block()
    return refined_skill_block(character_id)


def maybe_inject(
    system_prompt: str,
    character_id: Optional[str] = None,
    *,
    force: Optional[bool] = None,
    variant: str = "refined",
) -> str:
    """Append skills block when enabled (or when force=True for eval)."""
    use = skills_enabled() if force is None else bool(force)
    if not use:
        return system_prompt
    block = skill_prompt_block(character_id, variant=variant)
    if not block:
        return system_prompt
    return f"{system_prompt}\n\n{block}"
