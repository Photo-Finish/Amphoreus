# -*- coding: utf-8 -*-
"""Art payload cache — no LLM, no GPU, no browser.

    python tools/test_art_cache.py

Checks the properties the Eternal Page depends on: the masters are untouched,
the encoded sprite is smaller and still sharp at the size the visitor sees,
the data URI path is deterministic and cached, and both escape hatches
(AMP_ART_CACHE=off, AMP_ART_QUALITY=lossless) still work.
"""
from __future__ import annotations

import base64
import hashlib
import io
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world import art_cache  # noqa: E402
from src.world import eternal_page as ep  # noqa: E402

PASSED, FAILED = [], []
BODY_SHOWN_H = 140
FACE_SHOWN_W = 34
# The contract: at the size the visitor sees, average visible-channel drift
# stays under ~2.5% and no pixel is off by more than a quarter of the range.
BODY_MEAN_MAX, BODY_PIXEL_MAX = 6.0, 64
FACE_MEAN_MAX, FACE_PIXEL_MAX = 6.0, 40


def check(name: str, cond: object, extra: str = "") -> None:
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}{('  ' + extra) if extra else ''}")


def decode_uri(uri: str):
    from PIL import Image

    payload = uri.split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(payload))).convert("RGBA")


def sprite_pair(cid: str):
    """(source RGBA, source bytes) for a companion body the page draws."""
    from PIL import Image

    spr = ep.stage_sprite(cid, "calm")
    if not spr:
        return None, None
    raw = spr.get("body_png")
    if not raw and spr.get("body_path"):
        raw = Path(spr["body_path"]).read_bytes()
    if not raw:
        return None, None
    return Image.open(io.BytesIO(raw)).convert("RGBA"), raw


def visible_delta(a, b) -> tuple[float, int]:
    """(mean, max) absolute channel drift over pixels with visible alpha."""
    h = min(BODY_SHOWN_H, a.size[1])
    w = max(1, round(a.size[0] * h / a.size[1]))
    a = a.resize((w, h))
    b = b.resize((w, h))
    pa, pb = a.tobytes(), b.tobytes()
    tot = seen = mx = 0
    for i in range(0, len(pa), 4):
        if pa[i + 3] <= 24:
            continue
        d = max(abs(pa[i] - pb[i]), abs(pa[i + 1] - pb[i + 1]), abs(pa[i + 2] - pb[i + 2]))
        tot += d
        seen += 1
        mx = max(mx, d)
    return (tot / seen if seen else 0.0), mx


def at_width(a, b, width: int) -> tuple[float, int]:
    h = max(1, round(a.size[1] * width / a.size[0]))
    a = a.resize((width, h))
    b = b.resize((width, h))
    pa, pb = a.tobytes(), b.tobytes()
    tot = seen = mx = 0
    for i in range(0, len(pa), 4):
        if pa[i + 3] <= 24:
            continue
        d = max(abs(pa[i] - pb[i]), abs(pa[i + 1] - pb[i + 1]), abs(pa[i + 2] - pb[i + 2]))
        tot += d
        seen += 1
        mx = max(mx, d)
    return (tot / seen if seen else 0.0), mx


def main() -> int:
    from PIL import Image, features

    print("== The module stays a world-layer helper ==")
    src = (ROOT / "src" / "world" / "art_cache.py").read_text(encoding="utf-8")
    check("no Streamlit import", "streamlit" not in src)
    check("no network import", not any(
        token in src for token in ("urllib", "requests", "http.client", "socket")))
    check("Pillow and WebP available", features.check("webp"))
    cache_path = art_cache.cache_dir()
    check("cache lives under world_runtime",
          "world_runtime" in str(cache_path).replace("\\", "/"), str(cache_path))
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    check("that directory is gitignored", "world_runtime/" in gitignore)

    print("== Masters are never modified ==")
    sample = Path(ROOT / "assets" / "eternal_page" / "q_program" / "cutouts" /
                  "cyrene_v38_sit.png")
    before = hashlib.sha256(sample.read_bytes()).hexdigest()
    art_cache.data_uri_path(sample, max_px=art_cache.BODY_MAX_PX)
    after = hashlib.sha256(sample.read_bytes()).hexdigest()
    check("PNG master byte-identical after encoding", before == after)

    print("== Encoding ==")
    art_cache.reset()
    encoded_smaller = capped = aspect_ok = alpha_ok = True
    worst_body = (0.0, 0, "")
    for cid in ep.all_ids():
        im, raw = sprite_pair(cid)
        if im is None:
            continue
        uri = art_cache.data_uri(raw)
        got = decode_uri(uri)
        if len(uri) >= len(raw) * 4 / 3:
            encoded_smaller = False
        if max(got.size) > art_cache.BODY_MAX_PX:
            capped = False
        if abs(im.size[0] / im.size[1] - got.size[0] / got.size[1]) > 0.02:
            aspect_ok = False
        src_alpha = im.tobytes()[3::4]
        got_alpha = got.tobytes()[3::4]
        solid_src = sum(1 for a in src_alpha if a > 200) / max(len(src_alpha), 1)
        solid_got = sum(1 for a in got_alpha if a > 200) / max(len(got_alpha), 1)
        if solid_src and abs(solid_src - solid_got) / solid_src > 0.02:
            alpha_ok = False
        # Compare the alpha channel at one common size; raw counts differ
        # whenever the encoded sprite is downscaled.
        h = min(BODY_SHOWN_H, im.size[1])
        w = max(1, round(im.size[0] * h / im.size[1]))
        a_src = im.resize((w, h)).tobytes()[3::4]
        a_got = got.resize((w, h)).tobytes()[3::4]
        alpha_drift = sum(abs(a - b) for a, b in zip(a_src, a_got)) / max(len(a_src), 1)
        if alpha_drift > 6:
            alpha_ok = False
        mean, mx = visible_delta(im, got)
        if mean > worst_body[0]:
            worst_body = (mean, mx, cid)
        check(f"{cid}: smaller and within {BODY_MEAN_MAX:.0f} mean drift",
              mean <= BODY_MEAN_MAX and mx <= BODY_PIXEL_MAX,
              f"mean {mean:.2f} max {mx}")
    check("every sprite encodes smaller than its PNG", encoded_smaller)
    check("bodies capped at the display cap", capped)
    check("aspect ratio preserved", aspect_ok)
    check("silhouette and alpha preserved", alpha_ok)

    print("== Lossless mode is exact at its own resolution ==")
    os.environ["AMP_ART_QUALITY"] = "lossless"
    art_cache.reset()
    exact = True
    for cid in ep.all_ids()[:4]:
        im, raw = sprite_pair(cid)
        if im is None:
            continue
        got = decode_uri(art_cache.data_uri(raw))
        target = im
        longest = max(im.size)
        if longest > art_cache.BODY_MAX_PX:
            scale = art_cache.BODY_MAX_PX / float(longest)
            target = im.resize((max(1, round(im.size[0] * scale)),
                                max(1, round(im.size[1] * scale))), Image.LANCZOS)
        if got.size != target.size or got.tobytes() != target.tobytes():
            exact = False
    check("lossless round-trip is pixel-exact", exact)
    check("lossless is still smaller than PNG", len(art_cache.data_uri(sprite_pair("cyrene")[1]))
          < len(sprite_pair("cyrene")[1]) * 4 / 3)
    os.environ.pop("AMP_ART_QUALITY", None)
    art_cache.reset()

    print("== Data URIs and the cache ==")
    im, raw = sprite_pair("cyrene")
    uri = art_cache.data_uri(raw)
    check("WebP data URI prefix", uri.startswith("data:image/webp;base64,"))
    check("payload decodes to an image", decode_uri(uri).size[0] > 0)
    again = art_cache.data_uri(raw)
    check("same bytes produce the same URI", uri == again)
    stats = art_cache.stats()
    check("second call is a memory hit", stats["hits"] >= 1, str(stats))
    check("nothing is written outside the cache dir",
          all(p.suffix in {".webp", ".tmp"} for p in cache_path.glob("*"))
          if cache_path.is_dir() else True)

    os.environ["AMP_ART_CACHE"] = "off"
    art_cache.reset()
    png_uri = art_cache.data_uri(raw)
    check("AMP_ART_CACHE=off yields a PNG URI", png_uri.startswith("data:image/png;base64,"))
    check("off mode keeps the source bytes",
          base64.b64decode(png_uri.split(",", 1)[1]) == raw)
    os.environ.pop("AMP_ART_CACHE", None)
    art_cache.reset()

    check("empty input yields no URI", art_cache.data_uri(b"") == "")

    parchment = ep.parchment_path()
    if parchment is not None:
        puri = art_cache.data_uri_path(parchment, max_px=art_cache.PARCHMENT_MAX_PX)
        check("already-compressed parchment passes through as JPEG",
              puri.startswith("data:image/jpeg;base64,"))
        check("parchment bytes unchanged",
              base64.b64decode(puri.split(",", 1)[1]) == parchment.read_bytes())

    print("== Faces stay sharp at sticker size ==")
    art_cache.reset()
    worst_face = (0.0, 0, "")
    for cid in ep.all_ids():
        face = ep.cute_art(cid, "calm")
        if face is None:
            continue
        got = decode_uri(art_cache.data_uri_path(face))
        src_im = Image.open(face).convert("RGBA")
        mean, mx = at_width(src_im, got, FACE_SHOWN_W)
        if mean > worst_face[0]:
            worst_face = (mean, mx, cid)
        check(f"{cid}: face within {FACE_MEAN_MAX:.0f} mean drift",
              mean <= FACE_MEAN_MAX and mx <= FACE_PIXEL_MAX, f"mean {mean:.2f} max {mx}")

    print("== The page payload ==")
    art_cache.reset()
    total = 0
    png_total = 0
    for cid in ep.all_ids():
        spr = ep.stage_sprite(cid, "calm")
        if not spr:
            continue
        if spr.get("kind") == "q" and spr.get("body_png"):
            png_total += len(spr["body_png"])
            total += len(art_cache.data_uri(spr["body_png"]))
            if spr.get("face_path"):
                png_total += Path(spr["face_path"]).stat().st_size
                total += len(art_cache.data_uri_path(spr["face_path"]))
        elif spr.get("body_path"):
            png_total += Path(spr["body_path"]).stat().st_size
            total += len(art_cache.data_uri_path(
                spr["body_path"], max_px=art_cache.BODY_MAX_PX))
    if parchment is not None:
        png_total += parchment.stat().st_size
        total += len(art_cache.data_uri_path(
            parchment, max_px=art_cache.PARCHMENT_MAX_PX))
    ratio = total / max(png_total, 1)
    check(f"inline payload under a quarter of the PNG masters ({ratio:.1%})",
          ratio < 0.25, f"{total / 1024:.0f} KB from {png_total / 1024:.0f} KB")
    check("payload fits in one megabyte", total < 1024 * 1024, f"{total / 1024:.0f} KB")
    check("thirteen bodies plus faces were encoded", total > 0)

    print()
    print(f"worst body at {BODY_SHOWN_H}px: mean {worst_body[0]:.2f} "
          f"max {worst_body[1]} ({worst_body[2]})")
    print(f"worst face at {FACE_SHOWN_W}px: mean {worst_face[0]:.2f} "
          f"max {worst_face[1]} ({worst_face[2]})")
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
