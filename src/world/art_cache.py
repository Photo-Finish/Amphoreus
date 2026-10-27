# -*- coding: utf-8 -*-
"""Eternal Page art payloads — encode each sprite once, then reuse it.

The stage inlines every companion as a data URI, so the same 4.4 MB of PNG was
re-read, re-base64-encoded, and re-parsed by the browser on every Streamlit
rerun — a click, a drag, a pet, a whisper. This module derives a WebP once per
sprite, keeps the encoded bytes in memory, and reuses them from
``world_runtime/_art_cache/`` after a restart.

The PNG masters under ``assets/`` are never modified: the cache is derived,
local, and gitignored. Nothing leaves the machine.

Encoding aims at what the visitor can actually see. ``.buddy .sprite`` is a
fixed 140 px box and the PPG face sticker is ~34 px wide, and no CSS rule ever
scales a body up, so a body is capped at twice its box and a face at 96 px —
a HiDPI screen stays sharp, and no bytes are spent on pixels that never reach
the page. ``AMP_ART_CACHE=off`` restores the plain PNG data URI path, and
``AMP_ART_QUALITY=lossless`` gives a mathematically identical pass.
"""
from __future__ import annotations

import base64
import hashlib
import os
import threading
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "world_runtime" / "_art_cache"

# Displayed at 140 px tall (2× keeps a HiDPI screen sharp).
BODY_MAX_PX = 280
# The face sticker is 36% of a 7.8% buddy — ~34 px on a 1200 px stage, but the
# stage widens with the window, so keep a generous 4-5× and encode cheaply.
FACE_MAX_PX = 160
# Full-bleed parchment background; only trimmed, never shrunk below 2× stage.
PARCHMENT_MAX_PX = 2400
QUALITY = 92
# Pillow's WebP "method" is effort, not quality. Method 6 spends ~40× the CPU
# for under 1% fewer bytes; 5 keeps a cold first build under a second.
METHOD = 5

WEBP_MIME = "image/webp"
PNG_MIME = "image/png"
JPEG_MIME = "image/jpeg"
GIF_MIME = "image/gif"

MIME_BY_SUFFIX = {
    ".png": PNG_MIME,
    ".jpg": JPEG_MIME,
    ".jpeg": JPEG_MIME,
    ".webp": WEBP_MIME,
    ".gif": GIF_MIME,
}

_off_values = {"0", "off", "false", "no", "disable", "disabled"}
_lock = threading.Lock()
_memory: dict[str, str] = {}
_stats = {"hits": 0, "misses": 0, "png_bytes": 0, "webp_bytes": 0}


def _env(name: str, default: str = "") -> str:
    return str(os.environ.get(name, default) or "").strip()


def enabled() -> bool:
    """Cache + WebP are on unless ``AMP_ART_CACHE`` says otherwise."""
    return _env("AMP_ART_CACHE").lower() not in _off_values


def quality() -> object:
    """``92`` by default; ``"lossless"`` (or ``AMP_ART_QUALITY=lossless``)."""
    raw = _env("AMP_ART_QUALITY").lower()
    if raw in {"lossless", "ll", "exact"}:
        return "lossless"
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return QUALITY
    return max(1, min(100, value))


def cache_dir() -> Path:
    """Where encoded sprites live; ``AMP_ART_CACHE_DIR`` overrides it."""
    override = _env("AMP_ART_CACHE_DIR")
    return Path(override) if override else CACHE_DIR


def _digest(raw: bytes) -> str:
    return hashlib.sha1(raw).hexdigest()[:20]


def _key(raw: bytes, max_px: int, qual: object) -> str:
    return f"{_digest(raw)}-{max_px}-{qual}"


def _encode(raw: bytes, max_px: int, qual: object) -> Optional[bytes]:
    """PNG bytes → trimmed WebP bytes, or None when Pillow/WebP is unavailable."""
    try:
        import io

        from PIL import Image
    except Exception:
        return None
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
        if im.mode != "RGBA":
            # Palette / grey+alpha / RGB all become one shape for WebP alpha.
            im = im.convert("RGBA")
        longest = max(im.size)
        if max_px and longest > max_px:
            scale = max_px / float(longest)
            size = (max(1, round(im.size[0] * scale)), max(1, round(im.size[1] * scale)))
            im = im.resize(size, Image.LANCZOS)
        buf = io.BytesIO()
        if qual == "lossless":
            # exact=True keeps the RGB of fully transparent pixels too, so a
            # lossless pass is bit-identical to the (capped) master.
            im.save(buf, "WEBP", lossless=True, exact=True, method=METHOD)
        else:
            im.save(buf, "WEBP", lossless=False, quality=int(qual), method=METHOD)
        data = buf.getvalue()
    except Exception:
        return None
    if not data:
        return None
    return data


def _disk_read(path: Path) -> Optional[bytes]:
    try:
        if path.is_file():
            return path.read_bytes()
    except Exception:
        return None
    return None


def _disk_write(path: Path, data: bytes) -> None:
    """Best effort — a read-only or sandboxed runtime keeps the memory cache."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)
    except Exception:
        pass


def _uri(mime: str, data: bytes) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def data_uri(raw: bytes, *, max_px: int = BODY_MAX_PX) -> str:
    """Data URI for PNG ``raw``, encoded once and reused by key."""
    if not raw:
        return ""
    qual = quality()
    if not enabled():
        return _uri(PNG_MIME, raw)
    key = _key(raw, max_px, qual)
    with _lock:
        hit = _memory.get(key)
    if hit is not None:
        _stats["hits"] += 1
        return hit
    _stats["misses"] += 1
    _stats["png_bytes"] += len(raw)
    cached = _disk_read(cache_dir() / f"{key}.webp")
    encoded = cached if cached is not None else _encode(raw, max_px, qual)
    if encoded is None:
        return _uri(PNG_MIME, raw)
    if cached is None:
        _disk_write(cache_dir() / f"{key}.webp", encoded)
    uri = _uri(WEBP_MIME, encoded)
    _stats["webp_bytes"] += len(encoded)
    with _lock:
        _memory[key] = uri
    return uri


def data_uri_path(
    path: Optional[Path],
    *,
    max_px: int = FACE_MAX_PX,
    mime: Optional[str] = None,
) -> str:
    """Data URI for an image file.

    ``mime`` is honoured for already-compressed formats (the parchment JPEG is
    not re-encoded to PNG); PNG artwork goes through the WebP cache.
    """
    if path is None:
        return ""
    path = Path(path)
    try:
        if not path.is_file():
            return ""
        raw = path.read_bytes()
    except Exception:
        return ""
    suffix = path.suffix.lower()
    if suffix == ".png":
        return data_uri(raw, max_px=max_px)
    # Anything already compressed keeps its own bytes and its own mime type.
    return _uri(mime or MIME_BY_SUFFIX.get(suffix, PNG_MIME), raw)


def stats() -> dict:
    """What the cache has saved this process — used by the payload audit."""
    with _lock:
        hits, misses = _stats["hits"], _stats["misses"]
        png, webp = _stats["png_bytes"], _stats["webp_bytes"]
    return {
        "enabled": enabled(),
        "quality": quality(),
        "hits": hits,
        "misses": misses,
        "memory_entries": len(_memory),
        "png_bytes": png,
        "webp_bytes": webp,
        "ratio": (webp / png) if png else 0.0,
    }


def reset() -> None:
    """Forget the memory cache (tests, or a forced re-encode)."""
    with _lock:
        _memory.clear()
        for name in ("hits", "misses", "png_bytes", "webp_bytes"):
            _stats[name] = 0
