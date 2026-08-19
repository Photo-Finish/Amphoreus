"""Pack generated HSR sprites (white studio bg) into transparent land cells."""
from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter

CELL = 184
GEN = Path(r"D:\Workspace\Amphoreus\assets\life_sprites\_hsr_src")
OUT = Path(r"D:\Workspace\Amphoreus\assets\life_sprites")


def white_flood(im: Image.Image, white_min: int = 220, thresh: int = 28) -> Image.Image:
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


def drop_islands(im: Image.Image, keep_frac: float = 0.05) -> Image.Image:
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


def trim(im: Image.Image, pad: int = 4) -> Image.Image:
    bbox = im.split()[-1].point(lambda p: 255 if p > 16 else 0).getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    return im.crop(
        (max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad))
    )


def fit(im: Image.Image, cell: int = CELL) -> Image.Image:
    im = trim(im)
    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    ratio = min((cell - 8) / im.width, (cell - 8) / im.height)
    nw, nh = max(1, int(im.width * ratio)), max(1, int(im.height * ratio))
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas.paste(im, ((cell - nw) // 2, cell - nh - 2), im)
    return canvas


def film(frames: list[Image.Image], dest: Path) -> None:
    strip = Image.new("RGBA", (CELL * len(frames), CELL), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * CELL, 0), fr)
    strip.save(dest)
    print("wrote", dest.name, strip.size)


def pack(name: str, src: Path) -> None:
    still = fit(drop_islands(white_flood(Image.open(src))))
    still.save(OUT / f"{name}.png")
    print("wrote", f"{name}.png", still.size)
    frames = []
    for i, (dx, dy) in enumerate(((0, 0), (4, -3), (0, -5), (-4, -2))):
        fr = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        fr.paste(still, (dx, dy), still)
        frames.append(fr)
        fr.save(OUT / f"{name}_f{i + 1}.png")
    film(frames, OUT / f"{name}_film.png")


def main() -> None:
    pack("chimera", GEN / "chimera_okhema.png")
    pack("dromas", GEN / "dromas_okhema.png")


if __name__ == "__main__":
    main()
