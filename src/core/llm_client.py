"""
LLM Client — shared OpenAI-compatible chat client.

Works with any OpenAI-compatible endpoint:
  - Ollama (local):   base_url=http://localhost:11434/v1, api_key="ollama"
  - OpenAI:           base_url unset, api_key from env
  - any compatible API server

Used by both the chat layer (AgentManager) and the world engine.
"""

import os
from pathlib import Path
from typing import List, Optional

# Honor a project-root .env (model choices for the Heirs' senses, the backend,
# keys). override=True makes the .env authoritative over any stale inherited
# env vars. SENSES_MODE (set by launch_sanctuary.cmd) re-applies on top.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
except Exception:
    pass

_mode = os.getenv("SENSES_MODE", "").lower()
if _mode == "quality":
    os.environ["VISION_MODEL"] = "qwen3-vl:8b"
    os.environ["AUDIO_MODEL"] = "gemma3n"
elif _mode == "unified":
    os.environ["VISION_MODEL"] = "gemma3n"
    os.environ["AUDIO_MODEL"] = "gemma3n"


class LLMClient:
    """Thin wrapper around an OpenAI-compatible chat completions API."""

    def __init__(
        self,
        model: str = "qwen2.5:14b-instruct",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: int = 1024,
        vision_model: Optional[str] = None,
        audio_model: Optional[str] = None,
    ):
        self.model = model
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        # Vision-capable model for the Heirs' eyesight (e.g. qwen2.5vl:7b).
        self.vision_model = vision_model or os.getenv("VISION_MODEL")
        # Audio-understanding model for the Heirs' appreciation of music
        # (e.g. qwen2.5-omni or qwen2-audio). NOT for speech-to-text — that is
        # faster-whisper. This is for hearing music itself.
        self.audio_model = audio_model or os.getenv("AUDIO_MODEL")

    @property
    def configured(self) -> bool:
        """Whether a chat backend is available (a key or a local endpoint)."""
        return bool(self.api_key) or bool(self.base_url)

    def chat(
        self,
        messages: List[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        think: bool = False,
    ) -> str:
        """Send messages; returns the assistant's text reply.

        `think=False` (default) suppresses chain-of-thought on reasoning models
        (e.g. DeepSeek-R1-distill): the reply comes back as a plain answer
        instead of a `<think>` block. Without it, a long reasoning chain can
        consume the whole token budget and `content` comes back EMPTY — which
        silently turned every Heir reply into "..." in the style test.
        """
        if not self.configured:
            return (
                "[The LLM backend is not configured. Set OPENAI_API_KEY / OPENAI_BASE_URL "
                "(e.g. http://localhost:11434/v1 for Ollama) to enable responses.]"
            )

        from openai import OpenAI

        client = OpenAI(api_key=self.api_key or "ollama", base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
            extra_body={"think": think},
        )
        content = response.choices[0].message.content
        # Safety net: a reasoning model may still have spent its whole budget
        # thinking. Retry once with a much larger budget.
        if not content and self.max_tokens is not None:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature if temperature is None else temperature,
                max_tokens=(max_tokens or self.max_tokens) * 4,
                extra_body={"think": think},
            )
            content = response.choices[0].message.content
        return content or ""

    def stream(self, messages: List[dict], temperature: Optional[float] = None,
               think: bool = False):
        """Yield text chunks as they arrive."""
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key or "ollama", base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=self.max_tokens,
            stream=True,
            extra_body={"think": think},
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    # ------------------------------------------------------------------ #
    # Eyesight — multimodal (image + text)
    # ------------------------------------------------------------------ #
    def chat_vision(
        self,
        text: str,
        image_data_uri: str,
        messages: Optional[List[dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send text + an image (data URI) to a vision-capable model.

        The Heir "sees" the image. Uses self.vision_model (e.g.
        qwen2.5vl:7b) so the text model stays lightweight.
        """
        if not self.configured:
            return (
                "[The LLM backend is not configured. Start Ollama or set "
                "OPENAI_BASE_URL / OPENAI_API_KEY to enable the Heirs' eyesight.]"
            )
        if not self.vision_model:
            return (
                "[No vision model configured. Set VISION_MODEL (e.g. qwen2.5vl:7b) "
                "to grant the Heirs eyesight.]"
            )

        from openai import OpenAI

        client = OpenAI(api_key=self.api_key or "ollama", base_url=self.base_url)
        payload = [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": image_data_uri}},
        ]
        history = [m for m in (messages or []) if m.get("role") != "user"] or []
        history.append({"role": "user", "content": payload})
        response = client.chat.completions.create(
            model=self.vision_model,
            messages=history,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
        )
        return response.choices[0].message.content

    def chat_video(
        self,
        text: str,
        frame_data_uris: List[str],
        messages: Optional[List[dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send text + a sequence of video key frames to a vision-capable model.

        The Heir "watches" the video through its sampled frames. Uses
        self.vision_model (e.g. qwen2.5vl:7b).
        """
        if not self.configured:
            return (
                "[The LLM backend is not configured. Start Ollama or set "
                "OPENAI_BASE_URL / OPENAI_API_KEY to enable the Heirs' eyesight.]"
            )
        if not self.vision_model:
            return (
                "[No vision model configured. Set VISION_MODEL (e.g. qwen2.5vl:7b) "
                "to grant the Heirs eyesight.]"
            )

        from openai import OpenAI

        client = OpenAI(api_key=self.api_key or "ollama", base_url=self.base_url)
        content = [{"type": "text", "text": text}]
        for uri in frame_data_uris:
            content.append({"type": "image_url", "image_url": {"url": uri}})
        history = [m for m in (messages or []) if m.get("role") != "user"] or []
        history.append({"role": "user", "content": content})
        response = client.chat.completions.create(
            model=self.vision_model,
            messages=history,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
        )
        return response.choices[0].message.content

    def chat_audio(
        self,
        text: str,
        audio_data_uri: str,
        messages: Optional[List[dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send text + audio to an audio-understanding model (e.g. qwen2.5-omni).

        This is the Heirs' ear for MUSIC: they perceive the sound itself
        (mood, tempo, timbre, melody) and can genuinely appreciate it —
        not just transcribe speech. Uses self.audio_model.
        """
        if not self.configured:
            return (
                "[The LLM backend is not configured. Start Ollama or set "
                "OPENAI_BASE_URL / OPENAI_API_KEY to enable the Heirs' hearing of music.]"
            )
        if not self.audio_model:
            return (
                "[No audio model configured. Set AUDIO_MODEL (e.g. qwen2.5-omni) "
                "to let the Heirs hear and appreciate music.]"
            )

        from openai import OpenAI

        client = OpenAI(api_key=self.api_key or "ollama", base_url=self.base_url)
        content = [
            {"type": "text", "text": text},
            # OpenAI-compatible audio input (supported by Ollama for qwen2.5-omni)
            {"type": "input_audio", "input_audio": {"data": audio_data_uri, "format": "wav"}},
        ]
        history = [m for m in (messages or []) if m.get("role") != "user"] or []
        history.append({"role": "user", "content": content})
        response = client.chat.completions.create(
            model=self.audio_model,
            messages=history,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
        )
        return response.choices[0].message.content
