"""Build HSR-accurate chimera/dromas land sprites.

Front still PNGs for stationary display; side-profile *walk films* for roam.
Walk frames are distinct poses under assets/life_sprites/_hsr_src/walk/
(not bobbed copies of one still).
"""
from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "life_sprites" / "_hsr_src"
WALK = SRC / "walk"
OUT = ROOT / "assets" / "life_sprites"
CELL = 184

PROFILE_KINDS = ("chimera", "dromas")

STILL_SRC = {
    "chimera": SRC / "chimera_okhema.png",
    "dromas": SRC / "dromas_front_still.png",
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


def _dark_flood(im: Image.Image, dark_max: int = 48, thresh: int = 36) -> Image.Image:
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    vis = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def is_dark(c) -> bool:
        return c[0] <= dark_max and c[1] <= dark_max and c[2] <= dark_max

    def seed(x: int, y: int) -> None:
        if 0 <= x < w and 0 <= y < h and not vis[y][x] and is_dark(px[x, y]):
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
                and is_dark(px[nx, ny])
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


def _key_walk_frame(path: Path) -> Image.Image:
    """Key a generated walk pose; frames already face right for roam facing."""
    return _fit_cell(_key(Image.open(path)))


def _film(frames: list[Image.Image], dest: Path) -> None:
    strip = Image.new("RGBA", (CELL * len(frames), CELL), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * CELL, 0), fr)
    strip.save(dest)
    print("wrote", dest.name, strip.size)


def _frame_diversity(frames: list[Image.Image]) -> list[float]:
    """Mean absolute RGB delta vs frame 0 (opaque pixels only)."""
    base = frames[0].convert("RGBA")
    bp = base.load()
    scores: list[float] = []
    for fr in frames[1:]:
        fp = fr.convert("RGBA").load()
        total = 0.0
        n = 0
        for y in range(CELL):
            for x in range(CELL):
                a0 = bp[x, y][3]
                a1 = fp[x, y][3]
                if a0 < 20 and a1 < 20:
                    continue
                n += 1
                total += sum(abs(bp[x, y][i] - fp[x, y][i]) for i in range(3)) / 3.0
        scores.append(total / max(1, n))
    return scores


def build_kind(name: str) -> None:
    still_path = STILL_SRC[name]
    if not still_path.is_file():
        raise FileNotFoundError(f"missing still source: {still_path}")

    still = _key_still(still_path)
    still.save(OUT / f"{name}.png")
    print("wrote", f"{name}.png", still.size, "(front still)")

    frames: list[Image.Image] = []
    for i in range(1, 5):
        path = WALK / f"{name}_walk_f{i}.png"
        if not path.is_file():
            raise FileNotFoundError(f"missing walk frame: {path}")
        fr = _key_walk_frame(path)
        frames.append(fr)
        fr.save(OUT / f"{name}_f{i}.png")
        print("wrote", f"{name}_f{i}.png", fr.size)

    deltas = _frame_diversity(frames)
    print(f"  {name} frame diversity vs f1:", ", ".join(f"{d:.1f}" for d in deltas))
    if any(d < 4.0 for d in deltas):
        print(f"  WARNING: {name} walk frames look nearly identical (bob risk)")

    _film(frames, OUT / f"{name}_film.png")


def pack_pet_films() -> None:
    """Key generated pet poses into 4-frame reaction strips."""
    gen = Path(r"C:\Users\17501\.cursor\projects\d-Workspace-Amphoreus\assets")
    pet_src = SRC / "pet"
    pet_src.mkdir(parents=True, exist_ok=True)
    jobs = (
        ("chimera", 184),
        ("dromas", 184),
        ("hearth_cat", 256),
    )
    for name, cell in jobs:
        frames: list[Image.Image] = []
        for i in range(1, 5):
            src = gen / f"{name}_pet_f{i}.png"
            if not src.is_file():
                src = pet_src / f"{name}_pet_f{i}.png"
            if not src.is_file():
                raise FileNotFoundError(f"missing pet frame: {name} f{i}")
            raw = Image.open(src)
            raw.save(pet_src / f"{name}_pet_f{i}.png")
            fr = _fit_cell(_drop_islands(_dark_flood(raw)), cell=cell)
            frames.append(fr)
            fr.save(OUT / f"{name}_pet_f{i}.png")
        strip = Image.new("RGBA", (cell * len(frames), cell), (0, 0, 0, 0))
        for i, fr in enumerate(frames):
            strip.paste(fr, (i * cell, 0), fr)
        dest = OUT / f"{name}_pet_film.png"
        strip.save(dest)
        print("wrote", dest.name, strip.size)


def main() -> None:
    if not WALK.is_dir():
        raise FileNotFoundError(f"missing walk frame dir: {WALK}")
    for kind in PROFILE_KINDS:
        build_kind(kind)
    print("done — front stills + distinct side walk films for", ", ".join(PROFILE_KINDS))


if __name__ == "__main__":
    import sys
    if "pet" in sys.argv:
        pack_pet_films()
    else:
        main()
