# -*- coding: utf-8 -*-
"""Upscale low-resolution art with Real-ESRGAN, alpha intact.

    python tools/upscale_art.py --check
    python tools/upscale_art.py --image assets/galgame/ground/bg-vortex-of-genesis.jpg
    python tools/upscale_art.py --dir assets/eternal_page/q_program/crops --scale 2
    python tools/upscale_art.py --plan          # what the UI actually under-resolves

Wraps `realesrgan-ncnn-vulkan` (models/realesrgan/, gitignored). Masters are never
overwritten: an upscaled file is written beside the original with a `@2x` / `@4x`
suffix, or into `--out`.

**Alpha is handled properly.** The ncnn binary is RGB-only and writes opaque PNGs,
so a cut-out sprite passed straight through comes back with a solid background
painted into it. This tool premultiplies RGB by alpha, upscales the premultiplied
image and the alpha mask separately, then un-premultiplies — which is the only way
to upscale a cut-out without a fringe of the discarded background.

Text and flat ink survive this well; photographic texture gets invented, which is
the honest trade of any super-resolution model.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from PIL import Image  # noqa: E402

EXE = ROOT / "models" / "realesrgan" / "realesrgan-ncnn-vulkan.exe"
MODELS = ("realesrgan-x4plus-anime", "realesrgan-x4plus", "realesr-animevideov3-x2")


def available() -> bool:
    return EXE.is_file()


def models_present() -> list[str]:
    d = EXE.parent / "models"
    if not d.is_dir():
        return []
    return sorted({p.stem.rsplit("-x", 1)[0] if p.stem.endswith(("x2", "x3", "x4")) else p.stem
                    for p in d.glob("*.param")})


def native_scale(model: str) -> int:
    """The factor the model itself produces. `-s 2` is broken in this build: it
    crops the 4x result instead of resampling it, which shifts the image."""
    return 2 if model.endswith("-x2") else 4


def run(in_path: Path, out_path: Path, *, scale: int = 4, model: str = "realesrgan-x4plus-anime",
        gpu: int = 0, tile: int = 0) -> None:
    cmd = [str(EXE), "-i", str(in_path), "-o", str(out_path), "-n", model,
           "-s", str(native_scale(model)), "-g", str(gpu), "-f", "png"]
    if tile:
        cmd += ["-t", str(tile)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out_path.is_file():
        tail = (proc.stdout or "")[-300:] + (proc.stderr or "")[-300:]
        raise RuntimeError(f"realesrgan failed ({proc.returncode}): {tail}")


def _pad_for_model(im, align: int = 16):
    """Pad to a multiple of `align`, replicating edge pixels.

    The x4 model tiles on a grid of its own scale, and a height that is not a
    multiple of 4 (603 px, say) makes ncnn assemble the tiles in the wrong order —
    the output comes back as a collage of misplaced patches. Padding to a clean
    multiple and cropping the result back is the workaround.
    """
    import numpy as np

    w, h = im.size
    nw, nh = (w + align - 1) // align * align, (h + align - 1) // align * align
    if (nw, nh) == (w, h):
        return im, (w, h)
    arr = np.asarray(im)
    pad = ((0, nh - h), (0, nw - w)) + (((0, 0),) if arr.ndim == 3 else ())
    return Image.fromarray(np.pad(arr, pad, mode="edge")), (w, h)


def upscale(im: Image.Image, *, scale: int = 4, model: str = "realesrgan-x4plus-anime",
            gpu: int = 0, tile: int = 0) -> Image.Image:
    """Upscale an RGB or RGBA image, keeping transparency clean.

    Always runs the model at its own factor and resamples down if a smaller one
    was asked for: this build's `-s 2` crops the 4× result instead of resampling
    it, which shifts the whole image.
    """
    native = native_scale(model)
    target_factor = scale
    has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
    rgb = im.convert("RGBA") if has_alpha else im.convert("RGB")

    def finish(img: Image.Image, ow: int, oh: int) -> Image.Image:
        img = img.crop((0, 0, ow * native, oh * native))
        target = (ow * target_factor, oh * target_factor)
        return img if img.size == target else img.resize(target, Image.LANCZOS)

    with tempfile.TemporaryDirectory(prefix="sr_") as tmp:
        tmp = Path(tmp)
        if not has_alpha:
            src, (ow, oh) = _pad_for_model(rgb)
            src.convert("RGB").save(tmp / "in.png")
            run(tmp / "in.png", tmp / "out.png", model=model, gpu=gpu, tile=tile)
            return finish(Image.open(tmp / "out.png").convert("RGB"), ow, oh)
        # Premultiply, so the invisible colour cannot bleed into the edge.
        arr = rgb.convert("RGBA")
        alpha = arr.getchannel("A")
        prem = Image.composite(arr.convert("RGB"),
                               Image.new("RGB", arr.size, (0, 0, 0)), alpha)
        prem_p, (ow, oh) = _pad_for_model(prem)
        alpha_p, _ = _pad_for_model(alpha)
        prem_p.save(tmp / "rgb.png")
        alpha_p.save(tmp / "a.png")
        run(tmp / "rgb.png", tmp / "rgb_out.png", model=model, gpu=gpu, tile=tile)
        run(tmp / "a.png", tmp / "a_out.png", model=model, gpu=gpu, tile=tile)
        rgb_up = finish(Image.open(tmp / "rgb_out.png").convert("RGB"), ow, oh)
        a_up = finish(Image.open(tmp / "a_out.png").convert("L"), ow, oh)
        # Un-premultiply: colour / (alpha/255), guarded against divide-by-zero.
        out = Image.new("RGBA", rgb_up.size)
        px, ap, op = rgb_up.load(), a_up.load(), out.load()
        for y in range(out.size[1]):
            for x in range(out.size[0]):
                a = ap[x, y]
                if a == 0:
                    op[x, y] = (0, 0, 0, 0)
                else:
                    f = 255.0 / a
                    r, g, b = px[x, y]
                    op[x, y] = (min(255, int(r * f)), min(255, int(g * f)),
                                min(255, int(b * f)), a)
        return out


def out_path(src: Path, scale: int, out_dir: Path | None) -> Path:
    suffix = f"@{scale}x"
    target = (out_dir / f"{src.stem}{suffix}{src.suffix}") if out_dir else \
        (src.parent / f"{src.stem}{suffix}{src.suffix}")
    return target


# The places the UI paints an image larger than the file can fill. Measured from
# the code, not guessed: the stage is 1100×560 CSS and the page asks for 2× DPR.
PLAN = [
    ("assets/galgame/ground/bg-vortex-of-genesis.jpg",
     "the Eternal Page's full-bleed parchment: 1216 px stretched across a 2200 px stage"),
    ("assets/eternal_page/q_program/announcement/Version_3.5_Special_Program_Announcement.png",
     "the only 1200×675 announcement (every other is 1920×1080), and the source of Cerydra's crop"),
    ("assets/eternal_page/q_program/cutouts/hysilens_v35_sit.png",
     "the 360p Hysilens Q body: the reason she became a portrait"),
]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Upscale low-resolution art.")
    ap.add_argument("--image")
    ap.add_argument("--dir")
    ap.add_argument("--glob", default="*.png")
    ap.add_argument("--scale", type=int, default=4, choices=(2, 3, 4))
    ap.add_argument("--model", default="realesrgan-x4plus-anime")
    ap.add_argument("--gpu", type=int, default=0, help="-1 for CPU if the build allows it")
    ap.add_argument("--tile", type=int, default=0,
                    help="ncnn tile size; 0=auto. Large images can exhaust the GPU "
                         "while another model is loading — use 256 to be gentle")
    ap.add_argument("--out")
    ap.add_argument("--plan", action="store_true", help="list what the UI under-resolves")
    ap.add_argument("--check", action="store_true", help="report the tool's readiness")
    ap.add_argument("--force", action="store_true", help="overwrite an existing upscale")
    args = ap.parse_args(argv)

    if args.check:
        print(f"binary : {EXE}  ({'present' if available() else 'MISSING'})")
        print(f"models : {', '.join(models_present()) or 'none'}")
        if not available():
            print("\nfetch it with:")
            print("  curl -L -o models/realesrgan/sr.zip https://gh-proxy.com/https://github.com/"
                  "xinntao/Real-ESRGAN/releases/download/v0.2.5.0/"
                  "realesrgan-ncnn-vulkan-20220424-windows.zip")
            print("  Expand-Archive models/realesrgan/sr.zip models/realesrgan")
        return 0

    if args.plan:
        for path, why in PLAN:
            p = ROOT / path
            if not p.is_file():
                print(f"missing  {path}")
                continue
            with Image.open(p) as im:
                print(f"{im.size[0]:5d}x{im.size[1]:<5d}  {path}\n              {why}")
        return 0

    if not available():
        print("realesrgan is not installed — run with --check for the download commands")
        return 1

    out_dir = None
    if args.out:
        out_dir = Path(args.out)
        out_dir = out_dir if out_dir.is_absolute() else (ROOT / out_dir)
    targets: list[Path] = []
    if args.image:
        targets = [Path(args.image)]
    elif args.dir:
        targets = sorted(Path(args.dir).glob(args.glob))
    else:
        targets = [ROOT / p for p, _why in PLAN if (ROOT / p).is_file()]

    done = 0
    for src in targets:
        if not src.is_file():
            print(f"skip {src} (missing)")
            continue
        dst = out_path(src, args.scale, out_dir)
        if dst.exists() and not args.force:
            print(f"skip {dst.name} (exists; --force to redo)")
            continue
        with Image.open(src) as im:
            before = im.size
            has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
            up = upscale(im, scale=args.scale, model=args.model, gpu=args.gpu,
                         tile=args.tile)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.suffix.lower() in {".jpg", ".jpeg"}:
            up.convert("RGB").save(dst, quality=95)
        else:
            up.save(dst, "PNG")
        done += 1
        print(f"{src.name}: {before[0]}x{before[1]} -> {up.size[0]}x{up.size[1]}"
              f"{' (alpha kept)' if has_alpha else ''}  -> {dst}")
    print(f"\n{done} image(s) upscaled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
