# -*- coding: utf-8 -*-
"""Build a consistent side-view walk cycle for every resident.

    python tools/build_resident_walk_films.py

The shipped `resident_*_film.png` strips are NOT a walk cycle: the four frames are four
different orientations (left profile, three-quarter, front, front-standing), so the
figure spins as it plays — the "awkward orientation" the operator reported. Frame 1 of
every variant is a clean left-facing profile, so the cycle is DERIVED from that frame by
warping it (legs swing with the motion at the feet, arms counter-swing, body bobs).
Orientation therefore never changes, and mirroring for rightward travel lands correctly.

Writes `resident[_variant]_walk_film.png`, 4 frames of 256 px laid out horizontally. The
original strips are left untouched.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SPRITES = ROOT / "assets" / "life_sprites"
PREVIEW = ROOT / "world_runtime" / "art_review"
FRAME = 256
FRAMES = 4


def to_frame(im: Image.Image) -> Image.Image:
    """Crop to content, bottom-centre in a square, resize to FRAME."""
    a = np.array(im.convert("RGBA"))
    ys, xs = np.where(a[:, :, 3] > 16)
    crop = im.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    side = max(crop.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(crop, ((side - crop.width) // 2, side - crop.height))
    return sq.resize((FRAME, FRAME), Image.LANCZOS)


def warp(img: Image.Image, dx_fn, dy_fn) -> Image.Image:
    a = np.array(img)
    h, w = a.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    sx = np.clip(xs - dx_fn(xs, ys), 0, w - 1).astype(np.int32)
    sy = np.clip(ys - dy_fn(xs, ys), 0, h - 1).astype(np.int32)
    return Image.fromarray(a[sy, sx])


def walk_frames(base: Image.Image) -> list[Image.Image]:
    h = FRAME
    hip = h * 0.52           # hip line: legs swing below it
    shoulder = h * 0.28
    span = h - hip
    stride = 150.0
    frames = []
    for k in range(FRAMES):
        phase = k / FRAMES
        bob = -2.0 * abs(math.sin(2 * math.pi * phase))

        def dx(xs, ys, _p=phase):
            leg = np.clip((ys - hip) / span, 0, 1) ** 2.2
            arm = np.clip((ys - shoulder) / (h * 0.30), 0, 1) * np.clip(
                (hip - ys) / (h * 0.22), 0, 1)
            leg_wave = np.sin(2 * math.pi * (_p + xs / stride))
            arm_wave = np.sin(2 * math.pi * (_p + xs / stride) + math.pi)   # opposite
            return 9.0 * leg * leg_wave + 2.6 * arm * arm_wave

        def dy(xs, ys, _b=bob, _p=phase):
            leg = np.clip((ys - hip) / span, 0, 1) ** 3.0
            wave = np.sin(2 * math.pi * (_p + xs / stride))
            return np.full_like(xs, _b) - 3.0 * leg * np.clip(wave, 0, 1)

        frames.append(warp(base, dx, dy))
    return frames


def strip(frames: list[Image.Image]) -> Image.Image:
    out = Image.new("RGBA", (FRAME * len(frames), FRAME), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.alpha_composite(f, (i * FRAME, 0))
    return out


def main() -> int:
    variants = sorted(
        p.stem.replace("_f1", "")
        for p in SPRITES.glob("resident*_f1.png")
        if "_walk_" not in p.stem          # never consume our own output
    )
    if not variants:
        print("no resident art found")
        return 1
    written = []
    preview_rows = []
    for stem in variants:
        src = SPRITES / f"{stem}_f1.png"
        base = to_frame(Image.open(src).convert("RGBA"))
        frames = walk_frames(base)
        name = f"{stem}_walk"
        path = SPRITES / f"{name}_film.png"
        strip(frames).save(path, optimize=True)
        for i, fr in enumerate(frames, 1):
            fr.save(SPRITES / f"{name}_f{i}.png", optimize=True)
        written.append(f"{path.name} ({path.stat().st_size // 1024} KB)")
        preview_rows.append((stem, frames))
    print("wrote:")
    for w in written:
        print("  ", w)

    PREVIEW.mkdir(parents=True, exist_ok=True)
    rows = min(len(preview_rows), 6)
    sheet = Image.new("RGBA", (FRAME * FRAMES // 2 * 2, FRAME * rows // 2),
                      (28, 24, 40, 255))
    # compact preview: first variant's 4 frames plus each variant's frame 1
    small = Image.new("RGBA", (FRAME // 2 * FRAMES, FRAME // 2 * rows), (28, 24, 40, 255))
    for r in range(rows):
        _, frames = preview_rows[r]
        for i, f in enumerate(frames):
            small.alpha_composite(f.resize((FRAME // 2, FRAME // 2), Image.LANCZOS),
                                  (i * FRAME // 2, r * FRAME // 2))
    small.save(PREVIEW / "resident_walk_sheet.png")
    print("preview:", PREVIEW / "resident_walk_sheet.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
