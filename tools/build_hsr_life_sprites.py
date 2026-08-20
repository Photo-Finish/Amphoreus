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


# ---------------------------------------------------------------------------
# Profession outfits — recolor/composite from civilian resident still + walk
# ---------------------------------------------------------------------------

# Recipes keyed by sprite stem (matches resident_npcs.ROLE_OUTFIT values).
# fabric: chiton + drape near-whites. gold: optional trim retint. sash/apron:
# simple overlays so professions read at land scale without new source art.
OUTFIT_RECIPES: dict[str, dict] = {
    "resident_guard": {
        "fabric": (132, 46, 52),
        "gold": (210, 168, 78),
        "sash": (36, 32, 40),
        "sash_y": 0.42,
    },
    "resident_merchant": {
        "fabric": (236, 224, 196),
        "cloak": (74, 96, 148),
        "gold": (220, 176, 72),
        "pouch": True,
    },
    "resident_scholar": {
        "fabric": (78, 84, 118),
        "gold": (196, 170, 96),
        "scroll": True,
    },
    "resident_smith": {
        "fabric": (86, 72, 62),
        "gold": (168, 132, 72),
        "apron": (42, 36, 32),
    },
    "resident_weaver": {
        "fabric": (198, 176, 204),
        "gold": (188, 148, 92),
        "sash": (148, 72, 108),
        "sash_y": 0.44,
    },
    "resident_shrine": {
        "fabric": (248, 244, 232),
        "gold": (228, 188, 72),
        "laurel": True,
    },
    "resident_healer": {
        "fabric": (196, 224, 204),
        "gold": (180, 160, 88),
        "sash": (86, 138, 112),
        "sash_y": 0.45,
    },
    "resident_harbor": {
        "fabric": (82, 112, 142),
        "gold": (176, 148, 84),
    },
    "resident_field": {
        "fabric": (152, 132, 84),
        "gold": (156, 128, 64),
        "apron": (112, 100, 64),
    },
    "resident_handler": {
        "fabric": (156, 128, 100),
        "gold": (188, 148, 72),
        "harness": True,
    },
    "resident_baker": {
        "fabric": (244, 236, 220),
        "gold": (196, 156, 84),
        "apron": (226, 218, 200),
    },
}


def _is_skin(r: int, g: int, b: int, sat: float, lum: float) -> bool:
    return (
        r > 110
        and g > 70
        and b > 45
        and r >= g >= b - 8
        and 85 < lum < 200
        and 0.12 < sat < 0.55
        and (r - b) > 25
    )


def _is_gold(r: int, g: int, b: int, sat: float, lum: float) -> bool:
    return r > 145 and g > 100 and b < 120 and sat > 0.20 and lum > 105


def _is_fabric(r: int, g: int, b: int, sat: float, lum: float) -> bool:
    if _is_skin(r, g, b, sat, lum) or _is_gold(r, g, b, sat, lum):
        return False
    # Near-white / cream drapery (incl. warm folds).
    if lum >= 155 and sat <= 0.28:
        return True
    # Lit cream with a little warm bias.
    if lum >= 140 and sat <= 0.35 and r >= g >= b - 6 and (r - b) < 70:
        return True
    return False


def _shade_rgb(rgb: tuple[int, int, int], lum: float) -> tuple[int, int, int]:
    shade = 0.48 + 0.52 * (lum / 255.0)
    return (
        int(min(255, rgb[0] * shade)),
        int(min(255, rgb[1] * shade)),
        int(min(255, rgb[2] * shade)),
    )


def _recolor_outfit(im: Image.Image, recipe: dict) -> Image.Image:
    """Recolor civilian near-white drapery; preserve skin / hair / sandals."""
    out = im.convert("RGBA").copy()
    px = out.load()
    w, h = out.size
    fabric = recipe.get("fabric")
    cloak = recipe.get("cloak")
    gold = recipe.get("gold")
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 40:
                continue
            mx, mn = max(r, g, b), min(r, g, b)
            sat = (mx - mn) / mx if mx else 0.0
            lum = (r + g + b) / 3.0
            if _is_gold(r, g, b, sat, lum):
                if gold:
                    px[x, y] = (*_shade_rgb(gold, lum), a)
                continue
            if not _is_fabric(r, g, b, sat, lum):
                continue
            # Cloak bias: left side of figure (drape over shoulder/arm).
            use_cloak = bool(cloak) and x < int(w * 0.48) and y < int(h * 0.72)
            target = cloak if use_cloak else fabric
            if not target:
                continue
            px[x, y] = (*_shade_rgb(target, lum), a)
    return out


def _overlay_band(
    im: Image.Image,
    rgb: tuple[int, int, int],
    *,
    y_frac: float,
    thickness: float = 0.045,
    x0_frac: float = 0.30,
    x1_frac: float = 0.72,
    alpha: int = 150,
) -> None:
    """Paint a soft sash/apron band across the torso (in-place)."""
    from PIL import ImageDraw, ImageFilter, ImageChops

    w, h = im.size
    y = int(h * y_frac)
    th = max(2, int(h * thickness))
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    x0, x1 = int(w * x0_frac), int(w * x1_frac)
    draw.rounded_rectangle(
        [x0, y - th, x1, y + th],
        radius=max(2, th),
        fill=(*rgb, alpha),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1.2))
    base_a = im.split()[-1]
    band_a = overlay.split()[-1]
    overlay.putalpha(ImageChops.multiply(band_a, base_a))
    im.alpha_composite(overlay)


def _overlay_marks(im: Image.Image, recipe: dict) -> Image.Image:
    """Profession marks: sash, apron, pouch, scroll, laurel, harness."""
    from PIL import ImageDraw, ImageChops

    out = im.convert("RGBA").copy()
    w, h = out.size
    if recipe.get("sash"):
        _overlay_band(
            out,
            recipe["sash"],
            y_frac=float(recipe.get("sash_y", 0.45)),
            thickness=0.028,
            alpha=135,
        )
    if recipe.get("apron"):
        _overlay_band(
            out,
            recipe["apron"],
            y_frac=0.58,
            thickness=0.09,
            x0_frac=0.34,
            x1_frac=0.68,
            alpha=160,
        )
    draw_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(draw_layer)
    if recipe.get("pouch"):
        cx, cy = int(w * 0.58), int(h * 0.55)
        d.ellipse([cx - 7, cy - 9, cx + 7, cy + 9], fill=(92, 64, 40, 200))
        d.rectangle([cx - 2, cy - 12, cx + 2, cy - 6], fill=(160, 128, 64, 210))
    if recipe.get("scroll"):
        x0, y0 = int(w * 0.62), int(h * 0.48)
        d.rounded_rectangle(
            [x0, y0, x0 + 9, y0 + 26],
            radius=3,
            fill=(236, 224, 196, 210),
            outline=(168, 140, 88, 230),
        )
    if recipe.get("laurel"):
        cx, cy = int(w * 0.50), int(h * 0.14)
        d.arc([cx - 18, cy - 8, cx + 18, cy + 14], 200, 340, fill=(168, 188, 96, 210), width=3)
        d.arc([cx - 16, cy - 6, cx + 16, cy + 12], 200, 340, fill=(210, 176, 72, 200), width=2)
    if recipe.get("harness"):
        _overlay_band(
            out, (72, 56, 44), y_frac=0.36, thickness=0.022, x0_frac=0.32, x1_frac=0.70, alpha=170
        )
        _overlay_band(
            out, (72, 56, 44), y_frac=0.52, thickness=0.020, x0_frac=0.34, x1_frac=0.68, alpha=160
        )
    base_a = out.split()[-1]
    marks_a = draw_layer.split()[-1]
    draw_layer.putalpha(ImageChops.multiply(marks_a, base_a))
    out.alpha_composite(draw_layer)
    return out


def _load_resident_bases() -> tuple[Image.Image, list[Image.Image]]:
    still = Image.open(OUT / "resident.png").convert("RGBA")
    frames = [Image.open(OUT / f"resident_f{i}.png").convert("RGBA") for i in range(1, 5)]
    return still, frames


def build_profession_outfits() -> None:
    """Derive full still + walk film sets for each special profession outfit."""
    still, frames = _load_resident_bases()
    for stem, recipe in OUTFIT_RECIPES.items():
        new_still = _overlay_marks(_recolor_outfit(still, recipe), recipe)
        new_still.save(OUT / f"{stem}.png")
        print("wrote", f"{stem}.png", new_still.size)

        out_frames: list[Image.Image] = []
        for i, fr in enumerate(frames, start=1):
            nf = _overlay_marks(_recolor_outfit(fr, recipe), recipe)
            nf.save(OUT / f"{stem}_f{i}.png")
            out_frames.append(nf)
            print("wrote", f"{stem}_f{i}.png", nf.size)

        cell = out_frames[0].size[0]
        strip = Image.new("RGBA", (cell * len(out_frames), cell), (0, 0, 0, 0))
        for i, fr in enumerate(out_frames):
            strip.paste(fr, (i * cell, 0), fr)
        dest = OUT / f"{stem}_film.png"
        strip.save(dest)
        print("wrote", dest.name, strip.size)
    print("done — profession outfits:", ", ".join(OUTFIT_RECIPES))


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
    elif "outfits" in sys.argv:
        build_profession_outfits()
    else:
        main()
