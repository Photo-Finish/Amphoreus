"""Build HSR-accurate chimera/dromas land sprites.

Front still PNGs for stationary display; side-profile films for mobile roam.
Sources live in assets/life_sprites/_hsr_src/ (untracked working dumps).
"""
from __future__ import annotations

import shutil
from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "life_sprites" / "_hsr_src"
OUT = ROOT / "assets" / "life_sprites"
GEN = ROOT  # generated side/front art dropped in repo root by Cursor
CELL = 184

# Kinds with side-profile walk films + separate front stills.
PROFILE_KINDS = ("chimera", "dromas")

STILL_SRC = {
    "chimera": SRC / "chimera_okhema.png",
    "dromas": SRC / "dromas_front_still.png",
}

SIDE_SRC = {
    "chimera": SRC / "chimera_side_right.png",
    "dromas": SRC / "dromas_side_left.png",
}

# Bob offsets for 4-frame walk cycle on side art (px in cell space).
WALK_OFFSETS = {
    "chimera": ((0, 0), (5, -4), (0, -6), (-5, -3)),
    "dromas": ((0, 0), (4, -3), (0, -5), (-4, -2)),
}


def _white_flood(im: Image.Image, white_min: int = 220, thresh: int = 28) -> Image.Image:
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    vis = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def is_white(c) -> bool:
        return c[0] >= white_min and c[1] >= white_min and c[2] >= white_min

    def seed(x: int, y: int) -> None:
        if 0 <= x < w and 0 <= y < h and not vis[y][x] and is_white(px[x, y]):
            vis[y][x] = True
            q.append((x, y))

    for x in range(w):
        seed(x, 0)
        seed(x, h - 1)
    for y in range(h):
        seed(0, y)
        seed(w - 1, y)

    def near(a, b) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) <= thresh

    while q:
        x, y = q.popleft()
        c = px[x, y]
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (
                0 <= nx < w
                and 0 <= ny < h
                and not vis[ny][nx]
                and is_white(px[nx, ny])
                and near(c, px[nx, ny])
            ):
                vis[ny][nx] = True
                q.append((nx, ny))

    mask = Image.new("L", (w, h))
    md = mask.load()
    for y in range(h):
        for x in range(w):
            md[x, y] = 0 if vis[y][x] else 255
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im.convert("RGBA"), mask=mask)
    return out


def _border_flood(im: Image.Image, thresh: int, max_steps: int) -> Image.Image:
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    dist = [[-1] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def seed(x: int, y: int) -> None:
        if dist[y][x] < 0:
            dist[y][x] = 0
            q.append((x, y))

    for x in range(w):
        seed(x, 0)
        seed(x, h - 1)
    for y in range(h):
        seed(0, y)
        seed(w - 1, y)

    def near(a, b) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) <= thresh

    while q:
        x, y = q.popleft()
        d = dist[y][x]
        if d >= max_steps:
            continue
        c = px[x, y]
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and dist[ny][nx] < 0 and near(c, px[nx, ny]):
                dist[ny][nx] = d + 1
                q.append((nx, ny))

    mask = Image.new("L", (w, h))
    md = mask.load()
    for y in range(h):
        for x in range(w):
            md[x, y] = 0 if dist[y][x] >= 0 else 255
    mask = mask.filter(ImageFilter.MinFilter(3))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im.convert("RGBA"), mask=mask)
    return out


def _drop_islands(im: Image.Image, keep_frac: float = 0.05) -> Image.Image:
    w, h = im.size
    px = im.load()
    vis = [[False] * w for _ in range(h)]
    blobs: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            if vis[y][x] or px[x, y][3] < 20:
                continue
            stack = [(x, y)]
            vis[y][x] = True
            blob: list[tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                blob.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not vis[ny][nx] and px[nx, ny][3] >= 20:
                        vis[ny][nx] = True
                        stack.append((nx, ny))
            blobs.append(blob)
    if not blobs:
        return im
    keep = max(blobs, key=len)
    out = im.copy()
    opx = out.load()
    for blob in blobs:
        if blob is keep or len(blob) >= len(keep) * keep_frac:
            continue
        for x, y in blob:
            opx[x, y] = (0, 0, 0, 0)
    return out


def _trim(im: Image.Image, pad: int = 4) -> Image.Image:
    bbox = im.split()[-1].point(lambda p: 255 if p > 16 else 0).getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    return im.crop(
        (max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad))
    )


def _fit_cell(im: Image.Image, cell: int = CELL) -> Image.Image:
    im = _trim(im)
    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    ratio = min((cell - 8) / im.width, (cell - 8) / im.height)
    nw, nh = max(1, int(im.width * ratio)), max(1, int(im.height * ratio))
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas.paste(im, ((cell - nw) // 2, cell - nh - 2), im)
    return canvas


def _key(im: Image.Image) -> Image.Image:
    return _drop_islands(_white_flood(im))


def _key_still(path: Path) -> Image.Image:
    return _fit_cell(_key(Image.open(path)))


def _key_side(path: Path, *, flip: bool = False) -> Image.Image:
    im = _key(Image.open(path))
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return _fit_cell(im)


def _film(frames: list[Image.Image], dest: Path) -> None:
    strip = Image.new("RGBA", (CELL * len(frames), CELL), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * CELL, 0), fr)
    strip.save(dest)
    print("wrote", dest.name, strip.size)


def _stage_generated() -> None:
    """Copy Cursor-generated art into _hsr_src if present."""
    SRC.mkdir(parents=True, exist_ok=True)
    pairs = (
        (GEN / "chimera_side_right.png", SRC / "chimera_side_right.png"),
        (GEN / "dromas_side_left.png", SRC / "dromas_side_left.png"),
        (GEN / "dromas_front_still.png", SRC / "dromas_front_still.png"),
    )
    for src, dest in pairs:
        if src.is_file() and not dest.is_file():
            shutil.copy2(src, dest)
            print("staged", dest.name)


def build_kind(name: str) -> None:
    still_path = STILL_SRC[name]
    side_path = SIDE_SRC[name]
    if not still_path.is_file():
        raise FileNotFoundError(f"missing still source: {still_path}")
    if not side_path.is_file():
        raise FileNotFoundError(f"missing side source: {side_path}")

    still = _key_still(still_path)
    still.save(OUT / f"{name}.png")
    print("wrote", f"{name}.png", still.size, "(front still)")

    side = _key_side(side_path, flip=(name == "dromas"))
    frames: list[Image.Image] = []
    for i, (dx, dy) in enumerate(WALK_OFFSETS[name], 1):
        fr = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        fr.paste(side, (dx, dy), side)
        frames.append(fr)
        fr.save(OUT / f"{name}_f{i}.png")
    _film(frames, OUT / f"{name}_film.png")


def main() -> None:
    _stage_generated()
    for kind in PROFILE_KINDS:
        build_kind(kind)
    print("done — front stills + side walk films for", ", ".join(PROFILE_KINDS))


if __name__ == "__main__":
    main()
