"""
Senses — hearing and eyesight for the Chrysos Heirs.

The Heirs genuinely PROCESS multimodal input:

  HEARING (ears)   : the visitor speaks -> audio bytes -> faster-whisper STT
                     -> the Heir "hears" the words and responds.
  EYESIGHT (eyes)  : pictures  -> base64 -> a vision model (qwen2.5vl) "sees" it.
                     videos    -> PyAV frame extraction -> the key frames are
                     sent to the vision model, so the Heir "watches" the video.

Everything runs locally. If a backend is missing, the sense reports "offline"
and the sanctuary still works through text.

Environment:
  STT_MODEL   (default "small")   faster-whisper model name
  VISION_MODEL                    vision-capable model for eyesight (e.g. qwen2.5vl:7b)
  HF_ENDPOINT (default https://hf-mirror.com)  for downloading the STT model
  HF_HOME     (default <project>/models/hf-cache)  everything stays in the project
"""

import base64
import io
import os
from pathlib import Path
from typing import List, Optional

# The Amphoreus project root (this file is src/core/senses.py).
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Keep HuggingFace downloads inside the project (self-contained; nothing on C:)
# and routed through a reachable mirror.
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HOME", str(_PROJECT_ROOT / "models" / "hf-cache"))
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")  # classic LFS, not the xet CDN

# Preferred local STT model directory (inside the project, so the whole
# Amphoreus folder is self-contained).
DEFAULT_STT_LOCAL = str(_PROJECT_ROOT / "models" / "faster-whisper-base")


class Senses:
    """Perception: audio -> text (hearing), images/videos -> frames (eyesight)."""

    def __init__(
        self,
        stt_model: Optional[str] = None,
        vision_model: Optional[str] = None,
        audio_model: Optional[str] = None,
        whisper_device: Optional[str] = None,
    ):
        # Prefer the explicitly configured model, then a local dir, else "small"
        default_stt = (
            DEFAULT_STT_LOCAL if os.path.isdir(DEFAULT_STT_LOCAL) else "small"
        )
        self.stt_model = stt_model or os.getenv("STT_MODEL") or default_stt
        self.vision_model = vision_model or os.getenv("VISION_MODEL")
        self.audio_model = audio_model or os.getenv("AUDIO_MODEL")
        self.whisper_device = whisper_device or os.getenv("STT_DEVICE", "auto")
        self._whisper = None

    # ------------------------------------------------------------------ #
    # Eyesight — pictures
    # ------------------------------------------------------------------ #
    @staticmethod
    def encode_image(image_bytes: bytes, mime: str = "image/png") -> str:
        """Encode raw image bytes as a base64 data URI for a vision model."""
        return f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"

    @property
    def vision_available(self) -> bool:
        """Whether a vision-capable model is configured (eyesight enabled)."""
        return bool(self.vision_model)

    # ------------------------------------------------------------------ #
    # Hearing — music appreciation (audio-understanding model)
    # ------------------------------------------------------------------ #
    @staticmethod
    def encode_audio(audio_bytes: bytes, fmt: str = "wav") -> str:
        """Encode raw audio bytes as base64 (no data-URI prefix) for an audio model."""
        return base64.b64encode(audio_bytes).decode("ascii")

    @property
    def music_available(self) -> bool:
        """Whether an audio-understanding model is configured (music appreciation)."""
        return bool(self.audio_model)

    # ------------------------------------------------------------------ #
    # Eyesight — videos (the Heir watches)
    # ------------------------------------------------------------------ #
    def extract_video_frames(
        self,
        video_bytes: bytes,
        max_frames: int = 6,
        max_width: int = 640,
    ) -> List[str]:
        """
        Extract evenly-spaced key frames from a video as base64 JPEG data URIs,
        using PyAV (bundled with faster-whisper — no OpenCV needed).
        """
        try:
            import av
            from PIL import Image
        except ImportError:
            return []

        collected = []
        try:
            container = av.open(io.BytesIO(video_bytes))
            stream = container.streams.video[0]
            for frame in container.decode(stream):
                img = frame.to_image()
                if img.width > max_width:
                    h = int(img.height * max_width / img.width)
                    img = img.resize((max_width, h))
                collected.append(img)
                if len(collected) >= 400:  # safety cap for very long videos
                    break
            container.close()
        except Exception:
            return []

        if not collected:
            return []

        # Pick evenly-spaced frames so the Heir sees the whole arc, not one moment
        step = max(1, len(collected) // max_frames)
        chosen = collected[::step][:max_frames]

        uris: List[str] = []
        for img in chosen:
            buf = io.BytesIO()
            try:
                img.convert("RGB").save(buf, format="JPEG", quality=80)
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                uris.append(f"data:image/jpeg;base64,{b64}")
            except Exception:
                continue
        return uris

    # ------------------------------------------------------------------ #
    # Hearing — speech to text (the Heir listens)
    # ------------------------------------------------------------------ #
    @property
    def hearing_available(self) -> bool:
        return bool(self.stt_model)

    def _get_whisper(self):
        """Load the faster-whisper model once (cached)."""
        if self._whisper is None:
            from faster_whisper import WhisperModel

            device = self._resolve_device()
            self._whisper = WhisperModel(
                self.stt_model, device=device, compute_type="int8"
            )
        return self._whisper

    def _resolve_device(self) -> str:
        if self.whisper_device == "auto":
            try:
                import ctranslate2

                if ctranslate2.get_cuda_device_count() > 0:
                    return "cuda"
            except Exception:
                pass
            return "cpu"
        return self.whisper_device

    def transcribe_audio(self, audio_bytes: bytes) -> Optional[str]:
        """
        Convert spoken audio to text (the Heir 'hears' it).

        Returns the transcript, or None if no STT backend is configured.
        """
        if not self.stt_model:
            return None
        try:
            model = self._get_whisper()
            segments, _info = model.transcribe(io.BytesIO(audio_bytes))
            return "".join(s.text for s in segments).strip()
        except Exception:
            return None

    def hear(self, audio_bytes: bytes) -> Optional[str]:
        """Alias for transcribe_audio."""
        return self.transcribe_audio(audio_bytes)
