# -*- coding: utf-8 -*-
"""Build a side-view walk cycle and a roar for the chimera from its side art.

    python tools/build_chimera_side_films.py

The project has one side-view chimera pose (`_hsr_src/chimera_side_right.png`) and no
image generator, so both strips are DERIVED from that pose by warping it, never by
drawing a new creature: a puppet gait (a travelling wave through the legs, body bob,
tail sway) and a roar (head tips back, jaw opens, body crouches). The source art is
never modified.

Writes, 184 px per frame, 4 frames laid out horizontally:
    assets/life_sprites/chimera_side_film.png       walk / run
    assets/life_sprites/chimera_side_roar_film.png  roar (on click)
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "life_sprites" / "_hsr_src" / "chimera_side_right.png"
OUT = ROOT / "assets" / "life_sprites"
PREVIEW = ROOT / "world_runtime" / "art_review"
FRAME = 184
FRAMES = 4


def matte(path: Path, tol: int = 26) -> Image.Image:
    """Flat background -> transparent, flood-filled from the border."""
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    h, w = a.shape[:2]
    corners = np.array([a[0, 0, :3], a[0, w - 1, :3], a[h - 1, 0, :3], a[h - 1, w - 1, :3]])
    bg = np.median(corners, axis=0)
    near_bg = np.abs(a[:, :, :3].astype(int) - bg).sum(axis=2) < tol

    from collections import deque
    seen = np.zeros((h, w), bool)
    q: deque = deque()
    for x in range(w):
        for y in (0, h - 1):
            if near_bg[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and near_bg[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    a[:, :, 3] = np.where(seen, 0, 255)
    return Image.fromarray(a)


def to_frame(im: Image.Image) -> Image.Image:
    al = np.array(im)[:, :, 3]
    ys, xs = np.where(al > 16)
    crop = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    side = max(crop.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(crop, ((side - crop.width) // 2, side - crop.height))
    return sq.resize((FRAME, FRAME), Image.LANCZOS)


def warp(img: Image.Image, dx_fn, dy_fn) -> Image.Image:
    """Sample the source through a displacement field: out(x,y) = src(x-dx, y-dy)."""
    a = np.array(img)
    h, w = a.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    sx = np.clip(xs - dx_fn(xs, ys), 0, w - 1).astype(np.int32)
    sy = np.clip(ys - dy_fn(xs, ys), 0, h - 1).astype(np.int32)
    return Image.fromarray(a[sy, sx])


def walk_frames(base: Image.Image) -> list[Image.Image]:
    h = w = FRAME
    hip = h * 0.60
    span = h - hip
    stride = 118.0         # one full leg cycle across the body
    frames = []
    for k in range(FRAMES):
        phase = k / FRAMES
        bob = -2.8 * abs(math.sin(2 * math.pi * phase))

        def dx(xs, ys, _p=phase):
            # concentrate the swing at the paws: hips barely move, hooves do
            ramp = np.clip((ys - hip) / span, 0, 1) ** 2.4
            wave = np.sin(2 * math.pi * (_p + xs / stride))
            return 11.0 * ramp * wave

        def dy(xs, ys, _b=bob, _p=phase):
            # the forward-swinging paw lifts off the ground
            ramp = np.clip((ys - hip) / span, 0, 1) ** 3.0
            wave = np.sin(2 * math.pi * (_p + xs / stride))
            return np.full_like(xs, _b) - 3.2 * ramp * np.clip(wave, 0, 1)

        f = warp(base, dx, dy)
        # tail sway: shift the top-left tail band sideways
        def tdx(xs, ys, _p=phase):
            tail = (ys < hip + 8) & (xs < w * 0.30)
            return np.where(tail, 2.2 * math.cos(2 * math.pi * _p), 0.0)

        f = warp(f, tdx, lambda xs, ys: np.zeros_like(xs))
        frames.append(f)
    return frames


def roar_frames(base: Image.Image) -> list[Image.Image]:
    h = w = FRAME
    neck_y = h * 0.58
    angles = [-7, -14, -19, -11]
    opens = [3, 11, 16, 7]
    frames = []
    for ang, open_px in zip(angles, opens):
        # mouth first, so it warps with the head
        mouth = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(mouth)
        mx, my = int(w * 0.85), int(h * 0.50)
        d.polygon([(mx - int(w * 0.04), my - 1), (mx + int(w * 0.09), my + 2),
                   (mx + int(w * 0.01), my + open_px)],
                  fill=(112, 26, 30, 255))
        if open_px >= 11:
            d.polygon([(mx - int(w * 0.01), my + 3), (mx + int(w * 0.06), my + 5),
                       (mx + int(w * 0.01), my + open_px - 2)],
                      fill=(196, 104, 106, 255))
        composed = base.copy()
        composed.alpha_composite(mouth)

        shear = math.tan(math.radians(abs(ang)))

        def dx(xs, ys, _s=shear, _sign=1 if ang < 0 else -1):
            t = np.clip((neck_y - ys) / neck_y, 0, 1)
            return _sign * _s * t * (neck_y - ys) * 0.55

        def dy(xs, ys, _a=abs(ang)):
            t = np.clip((neck_y - ys) / neck_y, 0, 1)
            return -(_a / 19.0) * 3.0 * t

        frames.append(warp(composed, dx, dy))
    return frames


def strip(frames: list[Image.Image]) -> Image.Image:
    out = Image.new("RGBA", (FRAME * len(frames), FRAME), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.alpha_composite(f, (i * FRAME, 0))
    return out




# Variant body hues sampled from their own front frames, so a pink chimera walks as a
# pink chimera rather than turning purple.
# Torso RGB sampled from each variant's own art (median of the belly patch), so a
# pink chimera walks as a pink chimera rather than turning brown or purple.
_VARIANT_RGB = {
    "": None,
    "_pink": (232, 150, 170),
    "_blue": (86, 132, 168),
    "_orange": (226, 146, 74),
    "_purple": (128, 78, 158),
}
_BASE_RGB = (96, 56, 128)     # the side art's own torso colour
_BODY_BAND = 64               # euclidean colour distance that counts as body


def recolour(frames: list[Image.Image], target: tuple[int, int, int] | None) -> list[Image.Image]:
    """Map the side art's torso colour onto a variant's, leaving horns and eyes alone."""
    if target is None:
        return frames
    ratio = np.array(target, dtype=float) / np.maximum(np.array(_BASE_RGB, dtype=float), 1)
    base = np.array(_BASE_RGB, dtype=float)
    out = []
    for f in frames:
        a = np.array(f).astype(float)
        rgb, alpha = a[:, :, :3], a[:, :, 3]
        d = np.sqrt(((rgb - base) ** 2).sum(axis=2))
        near = (d < _BODY_BAND) & (alpha > 8)
        shifted = np.clip(rgb * ratio.reshape(1, 1, 3), 0, 255)
        rgb = np.where(near[:, :, None], shifted, rgb)
        out.append(Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8)))
    return out


def main() -> int:
    if not SRC.is_file():
        print("missing source:", SRC)
        return 1
    base = to_frame(matte(SRC))
    walk = walk_frames(base)
    roar = roar_frames(base)

    written = []
    for suffix, target in _VARIANT_RGB.items():
        stem = "chimera_side" + suffix
        for name, frames in ((stem, recolour(walk, target)),
                             (stem + "_roar", recolour(roar, target))):
            path = OUT / f"{name}_film.png"
            strip(frames).save(path, optimize=True)
            for i, fr in enumerate(frames, 1):
                fr.save(OUT / f"{name}_f{i}.png", optimize=True)
            written.append(f"{path.name} ({path.stat().st_size // 1024} KB)")

    print("wrote:")
    for w in written:
        print("  ", w)

    PREVIEW.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGBA", (FRAME * FRAMES, FRAME * 2 + 12), (28, 24, 40, 255))
    for i, f in enumerate(walk):
        sheet.alpha_composite(f, (i * FRAME, 0))
    for i, f in enumerate(roar):
        sheet.alpha_composite(f, (i * FRAME, FRAME + 12))
    sheet.save(PREVIEW / "chimera_side_sheet.png")
    print("preview:", PREVIEW / "chimera_side_sheet.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
