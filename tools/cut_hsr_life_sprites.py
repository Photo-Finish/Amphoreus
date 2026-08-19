"""Cut official HSR wiki screenshots into transparent land sprites.

Sources: assets/life_sprites/_hsr_src/
Outputs overwrite chimera.png / dromas.png and rebuild 4-frame films.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "life_sprites" / "_hsr_src"
OUT = ROOT / "assets" / "life_sprites"
CELL = 184


def _border_flood(im: Image.Image, thresh: int, max_steps: int) -> Image.Image:
    """Flood similar colours a limited distance from the crop *border only*."""
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


def _drop_islands(im: Image.Image, keep_frac: float = 0.08) -> Image.Image:
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


def _trim(im: Image.Image, pad: int = 2) -> Image.Image:
    bbox = im.split()[-1].point(lambda p: 255 if p > 20 else 0).getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    return im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))


def _fit_cell(im: Image.Image, cell: int = CELL) -> Image.Image:
    im = _trim(im)
    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    max_w, max_h = cell - 6, cell - 6
    ratio = min(max_w / im.width, max_h / im.height)
    nw, nh = max(1, int(im.width * ratio)), max(1, int(im.height * ratio))
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas.paste(im, ((cell - nw) // 2, cell - nh - 2), im)
    return canvas


def cut(src: Path, box: tuple[int, int, int, int], thresh: int, steps: int) -> Image.Image:
    im = Image.open(src).crop(box)
    return _fit_cell(_drop_islands(_border_flood(im, thresh, steps)))


def _film(frames: list[Image.Image], dest: Path) -> None:
    film = Image.new("RGBA", (CELL * len(frames), CELL), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        film.paste(fr, (i * CELL, 0), fr)
    film.save(dest)
    print("wrote", dest.name, film.size)


def main() -> None:
    # Tight boxes; limited-distance flood so dark fur is not eaten.
    c1 = cut(SRC / "chimera_purple.png", (275, 310, 525, 730), 22, 28)
    c2 = cut(SRC / "chimera_pink.png", (470, 500, 750, 950), 24, 32)
    c3 = cut(SRC / "chimera_orange.png", (305, 410, 555, 780), 20, 26)
    c4 = cut(SRC / "chimera_blue.png", (305, 280, 505, 590), 22, 24)

    c1.save(OUT / "chimera.png")
    print("wrote chimera.png", c1.size)
    for i, fr in enumerate((c1, c2, c3, c4), 1):
        fr.save(OUT / f"chimera_f{i}.png")
    _film([c1, c2, c3, c4], OUT / "chimera_film.png")

    d1 = cut(SRC / "dromas_wiki.png", (570, 260, 870, 860), 16, 40)
    d1.save(OUT / "dromas.png")
    print("wrote dromas.png", d1.size)
    d_frames = []
    for i, (dx, dy) in enumerate(((0, 0), (3, -2), (0, -4), (-3, -1))):
        fr = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        fr.paste(d1, (dx, dy), d1)
        d_frames.append(fr)
        fr.save(OUT / f"dromas_f{i + 1}.png")
    _film(d_frames, OUT / "dromas_film.png")


if __name__ == "__main__":
    main()
