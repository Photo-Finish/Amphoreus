# -*- coding: utf-8 -*-
"""Second-pass matte for the Eternal Page sill.

The first pass (`tools/cut_q_program.py`) cut each Q sit from its announcement
still but deliberately kept the sit furniture, so feet would read as planted. At
the sill's 140 px that furniture reads as a rectangular slab of the source photo,
and the crop's straight edges give the page its pasted-on look.

Two policies, chosen per sprite by looking at the result:

* ``saliency`` — official u2net salient-object model (ONNX, CPU) over the first
  pass. It separates the figure from its set cleanly where the source is a crisp
  2D announcement still.
* ``cut`` — where u2net under-reads the body (the two 360p 3D stage crops and
  three busy sofa stills), keep the first pass's silhouette and dissolve the crop
  edge with an elliptical falloff. The furniture fades instead of ending in a
  straight line; nothing is invented.

Nothing under `cutouts/` is touched. Output goes to a parallel folder,
`cutouts_matte/`, and `src/world/eternal_sill.py` prefers it — so the first pass
stays intact and one file's removal restores the old page exactly.

    python tools/matte_sill.py                 # all thirteen
    python tools/matte_sill.py --only cyrene   # one
    python tools/matte_sill.py --check         # report without writing

Model (`models/u2net/u2net.onnx`, gitignored, 168 MB):

    curl -L -o models/u2net/u2net.onnx \\
      https://gh-proxy.com/https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx
"""
from __future__ import annotations

import json
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import numpy as np  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402

from src.world.eternal_q import CUTOUTS, Q_SIT  # noqa: E402

OUT_DIR = ROOT / "assets" / "eternal_page" / "q_program" / "cutouts_matte"
QPROGRAM = ROOT / "assets" / "eternal_page" / "q_program"
MANIFEST = OUT_DIR / "manifest.json"
MODEL_DIR = ROOT / "models" / "u2net"
INPUT = 320

# saliency: u2net separates cleanly. cut: dissolve the crop edge. flood: remove
# the border-connected set through flat colour, then fill the interior holes the
# flood punches in costumes (Cyrene, Evernight, Dan Heng sit in busy sets where
# u2net reads the photograph). copy: the art is already a transparent bust.
POLICY: dict[str, str] = {
    # u2net reads these cleanly (crisp 2D announcement stills).
    "aglaea": "saliency",
    "hyacine": "saliency",
    "castorice": "saliency",
    "cipher": "saliency",
    "mydei": "saliency",
    "cerydra": "saliency",
    # Busy painted sets: the set is border-connected and flat, the costume holes
    # the flood punches are interior, so hole-filling restores the figure.
    "cyrene": "flood",
    "evernight": "flood",
    "dan-heng-permansor-terrae": "flood",
    # Her swing and flowers are her canonical seat, not a matte failure.
    "tribbie": "cut",
    # Overridden below (a bust, not a sit).
    "anaxa": "copy",
    "phainon": "copy",
    "hysilens": "copy",
}

# Flood tuning per sprite: (Lab tolerance, minimum flatness to walk through).
FLOOD_TUNING: dict[str, tuple[float, float]] = {
    "cyrene": (14.0, 0.50),
    "dan-heng-permansor-terrae": (14.0, 0.50),
    "evernight": (22.0, 0.35),
}

# Elliptical falloff: flat inside `inset` of the way to the crop edge, gone by it.
# "cut" fades hard enough to dissolve the furniture the first pass kept; the
# saliency mask is already tight, so it only needs a clean border.
FEATHER = {"cut": (0.62, 0.40), "saliency": (0.88, 0.10),
           "flood": (0.88, 0.10), "copy": (0.92, 0.08)}
SALIENCY_FLOOR = 0.32

# Colour a fading edge is pulled toward, so a half-transparent photograph stops
# glowing against the star field. Matches the page's parchment shadow.
PAGE_DARK = (10, 18, 38)
HUSH = 0.85

# Where the first pass demonstrably read the wrong person, the second pass takes
# its art from the official announcement still and writes an honestly named
# file. The first-pass cutout stays untouched, as the record of the error.
#
# anaxa — `anaxa_v34_sit.png` is a grey-haired, gold-eyed figure: the Trailblazer
# (Caelus) standing in the 3.4 stage frame, not Anaxa, who is canonically mint
# green with a black gold-patterned eyepatch (`databank/chrysos-heirs/anaxa.md`).
OVERRIDES: dict[str, dict] = {
    "anaxa": {
        "source": "announcement/Version_3.4_Special_Program_Announcement.png",
        "box": (1616, 146, 1904, 452),
        "out": "anaxa_v34_announcement_bust.png",
        "policy": "saliency",
        "note": "3.4 announcement top-right bust; replaces a misidentified Trailblazer crop",
    },
    # phainon: the wired sit is a 360p stage grab. Identity is right, but the
    # announcement's own bust is the same character at full resolution.
    "phainon": {
        "source": "announcement/Version_3.4_Special_Program_Announcement.png",
        "box": (268, 672, 498, 972),
        "out": "phainon_v34_announcement_bust.png",
        "policy": "saliency",
        "note": "3.4 announcement bottom-left bust; sharper than the 360p stage grab",
    },
    # hysilens: her Q body exists only in the 3.5 programme video at 360p; no
    # official still carries it (the 3.5 announcement substitutes The Herta), and
    # the video's API is unreachable from this machine. The operator's standing
    # call is "bust when resolution does not work out", so her body is the
    # official Pom-Pom Gallery sticker — crisp, transparent, canon.
    "hysilens": {
        "base": "assets/eternal_page/cute/hysilens",
        "source": "02.png",
        "out": "hysilens_ppg_bust.png",
        "policy": "copy",
        "note": "PPG bust: the only crisp official art of her; the 360p Q body is not rescuable",
    },
}


def session(model: str = "u2net"):
    import onnxruntime as ort

    path = MODEL_DIR / f"{model}.onnx"
    if not path.is_file():
        raise SystemExit(f"missing model: {path}")
    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def saliency(sess, im: Image.Image) -> np.ndarray:
    """u2net d1 saliency, normalised to 0..1 at the source size."""
    rgb = im.convert("RGB").resize((INPUT, INPUT), Image.LANCZOS)
    x = np.asarray(rgb, dtype=np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array(
        [0.229, 0.224, 0.225], dtype=np.float32)
    x = np.transpose(x, (2, 0, 1))[None, ...]
    preds = sess.run(None, {sess.get_inputs()[0].name: x})
    d = np.squeeze(preds[0]).astype(np.float32)
    span = float(d.max() - d.min())
    if span > 1e-6:
        d = (d - d.min()) / span
    mask = Image.fromarray((np.clip(d, 0, 1) * 255).astype(np.uint8))
    return np.asarray(mask.resize(im.size, Image.LANCZOS), dtype=np.float32) / 255.0


def largest_component(mask: np.ndarray) -> np.ndarray:
    """Keep the biggest 4-connected blob (the figure), drop stray crumbs."""
    try:
        import cv2
    except Exception:
        return mask
    n, labels = cv2.connectedComponents(mask.astype(np.uint8), connectivity=4)
    if n <= 1:
        return mask
    sizes = [(labels == i).sum() for i in range(1, n)]
    return (labels == 1 + int(np.argmax(sizes))).astype(np.uint8)


def feather(alpha: np.ndarray, inset: float, soft: float) -> np.ndarray:
    h, w = alpha.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - (w - 1) / 2.0) / (w / 2.0)) ** 2 +
                ((yy - (h - 1) / 2.0) / (h / 2.0)) ** 2)
    t = np.clip((r - inset) / max(soft, 1e-3), 0.0, 1.0)
    return alpha * (1.0 - t * t * (3.0 - 2.0 * t))


def trim(im: Image.Image) -> Image.Image:
    bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(bb) if bb else im


def _flatness(rgb: np.ndarray, blur: int = 3) -> np.ndarray:
    im = Image.fromarray(rgb).convert("L").filter(ImageFilter.GaussianBlur(1.0))
    edge = im.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(blur))
    e = np.asarray(edge, dtype=np.float32) / 255.0
    return np.clip(1.0 - e * 5.0, 0.0, 1.0)


def _lab(rgb: np.ndarray) -> np.ndarray:
    return np.asarray(Image.fromarray(rgb).convert("LAB"), dtype=np.float32)


def _flood_remove(alpha: np.ndarray, rgb: np.ndarray, tol: float,
                  flat_min: float, ring: int = 10) -> np.ndarray:
    """Where the border-connected set lives: flat, colour-similar, reachable.

    Seeded from a ring just inside the crop (the first pass leaves a transparent
    rim), walking only through low-detail pixels of similar colour, so it spreads
    across a bench or a sofa but stops at the figure's ink.
    """
    h, w = alpha.shape
    opaque = alpha > 0.05
    interior = np.zeros_like(opaque)
    interior[ring:h - ring, ring:w - ring] = True
    flat = _flatness(rgb)
    L = _lab(rgb)
    seeds = [(y, x) for y in range(h) for x in range(w)
             if opaque[y, x] and not interior[y, x]]
    kill = np.zeros((h, w), bool)
    queue: list[tuple[int, int]] = []
    for y, x in seeds:
        kill[y, x] = True
        queue.append((y, x))
    head = 0
    while head < len(queue):
        y, x = queue[head]
        head += 1
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if ny < 0 or nx < 0 or ny >= h or nx >= w or kill[ny, nx] or not opaque[ny, nx]:
                continue
            if flat[ny, nx] < flat_min:
                continue
            if float(np.sqrt(((L[ny, nx] - L[y, x]) ** 2).sum())) > tol:
                continue
            kill[ny, nx] = True
            queue.append((ny, nx))
    return kill


def _fill_holes(kept: np.ndarray) -> np.ndarray:
    """Interior holes the flood punched in a costume are not the set — restore them."""
    try:
        import cv2
    except Exception:
        return kept
    m = kept.astype(np.uint8)
    ff = m.copy()
    mask = np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 1)
    outside = ff.astype(bool)
    return kept | (~outside)


def pad(im: Image.Image, frac: float = 0.06) -> Image.Image:
    """A little transparent margin so the fade happens outside the silhouette."""
    w, h = im.size
    dx, dy = max(2, round(w * frac)), max(2, round(h * frac))
    out = Image.new("RGBA", (w + 2 * dx, h + 2 * dy), (0, 0, 0, 0))
    out.alpha_composite(im, (dx, dy))
    return out


def feather_image(im: Image.Image, inset: float, soft: float) -> Image.Image:
    a = np.asarray(im.getchannel("A"), dtype=np.float32) / 255.0
    out = im.copy()
    out.putalpha(Image.fromarray((feather(a, inset, soft) * 255).astype(np.uint8)))
    return out


def ellipse_ramp(shape: tuple[int, int], inset: float, soft: float) -> np.ndarray:
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - (w - 1) / 2.0) / (w / 2.0)) ** 2 +
                ((yy - (h - 1) / 2.0) / (h / 2.0)) ** 2)
    t = np.clip((r - inset) / max(soft, 1e-3), 0.0, 1.0)
    return 1.0 - t * t * (3.0 - 2.0 * t)


def darken_edges(im: Image.Image, inset: float, soft: float,
                 strength: float = 0.62) -> Image.Image:
    """Vignette the outer band toward the page's dark.

    A photograph that fades out still carries its own bright background, which
    reads as a glow on a night stage. Darkening by distance (not by alpha) makes
    the leftover set merge into the backdrop while the figure keeps its colour.
    """
    arr = np.asarray(im, dtype=np.float32)
    ramp = ellipse_ramp(arr.shape[:2], inset, soft)[..., None]
    k = 1.0 - strength * (1.0 - ramp)
    arr[..., :3] *= k
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def matte(sess, cid: str, src: Image.Image, policy: str | None = None) -> tuple[Image.Image, dict]:
    policy = policy or POLICY.get(cid, "cut")
    v1 = np.asarray(src.getchannel("A"), dtype=np.float32) / 255.0
    if policy == "saliency" and sess is not None:
        sal = saliency(sess, src)
        a = np.where(v1 > 0.03, np.maximum(sal, v1 * 0.25), 0.0)
        a = np.clip((a - SALIENCY_FLOOR) / (1.0 - SALIENCY_FLOOR) * 1.3, 0, 1)
        solid = largest_component((a > 0.45).astype(np.uint8))
        grown = Image.fromarray(solid * 255).filter(ImageFilter.MaxFilter(3))
        grown = grown.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
        a = np.minimum(a, np.asarray(grown, dtype=np.float32) / 255.0 + 0.2)
    elif policy == "flood":
        rgb = np.asarray(src.convert("RGB"), dtype=np.uint8)
        tol, flat_min = FLOOD_TUNING.get(cid, (14.0, 0.50))
        kill = _flood_remove(v1, rgb, tol, flat_min)
        kept = _fill_holes((v1 > 0.05) & ~kill)
        a = np.where(kept, v1, 0.0)
    else:
        # "cut" keeps the first pass; "copy" is already transparent art (a bust).
        a = v1
    out = src.copy()
    out.putalpha(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)))
    # Trim to the figure, then pad, then fade: the falloff lands in the margin
    # so no straight crop edge can survive, and one pass does all the fading.
    out = feather_image(pad(trim(out)), *FEATHER[policy])
    if policy == "cut":
        out = darken_edges(out, *FEATHER[policy], strength=0.62)
    v1_opaque = float((v1 > 0.5).sum())
    covered = float((np.asarray(out.getchannel("A")) > 127).sum()) / max(v1_opaque, 1.0)
    # No straight crop edge may survive: every border pixel must be see-through.
    border = np.asarray(out.getchannel("A"))
    edge_max = int(max(border[0].max(), border[-1].max(), border[:, 0].max(),
                       border[:, -1].max()))
    return out, {
        "policy": policy,
        "size": list(out.size),
        "covered": round(covered, 3),
        "edge_alpha_max": edge_max,
    }


def main(argv: list[str]) -> int:
    model = "u2net"
    if "--model" in argv:
        model = argv[argv.index("--model") + 1]
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    check = "--check" in argv

    need_saliency = any(
        (OVERRIDES.get(c, {}).get("policy") or POLICY.get(c, "cut")) == "saliency"
        for c in ([only] if only else Q_SIT))
    sess = session(model) if need_saliency else None
    report = {}
    for cid in ([only] if only else list(Q_SIT.keys())):
        override = OVERRIDES.get(cid)
        if override:
            src_path = (ROOT / override["base"] / override["source"]
                        if override.get("base") else QPROGRAM / override["source"])
            out_name = override["out"]
            policy = override.get("policy")
        else:
            out_name = Q_SIT[cid][0]
            src_path = CUTOUTS / out_name
            policy = None
        if not src_path.is_file():
            print(f"  skip {cid} (missing {src_path.name})")
            continue
        src = Image.open(src_path).convert("RGBA")
        if override and override.get("box"):
            src = src.crop(override["box"])
        out, stat = matte(sess, cid, src, policy)
        report[cid] = {
            "source": str(src_path.relative_to(ROOT)).replace("\\", "/"),
            "out": out_name,
            **stat,
        }
        if override and override.get("note"):
            report[cid]["note"] = override["note"]
        if not check:
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            out.save(OUT_DIR / out_name, "PNG")
        print(f"  {cid:28s} {stat['policy']:9s} {str(stat['size']):12s} "
              f"keeps {stat['covered']:5.0%}  edge alpha {stat['edge_alpha_max']:3d}")

    if not check:
        old: dict = {}
        if MANIFEST.is_file():
            try:
                old = json.loads(MANIFEST.read_text(encoding="utf-8"))
            except Exception:
                old = {}
        old.update({"model": model, "note": "second-pass sill bodies; cutouts/ untouched",
                    **report})
        MANIFEST.write_text(json.dumps(old, indent=2, sort_keys=True), encoding="utf-8")
        # Provenance: the files this run read, by hash. The suite re-checks these,
        # so "the matte was derived from exactly these files" stays a fact rather
        # than a promise — and the misread first-pass crop stays on record.
        sources = {}
        for name in sorted({spec[0] for spec in Q_SIT.values()}):
            path = CUTOUTS / name
            if path.is_file():
                sources[name] = {
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "bytes": path.stat().st_size,
                }
        for cid, override in OVERRIDES.items():
            path = (ROOT / override["base"] / override["source"]
                    if override.get("base") else QPROGRAM / override["source"])
            if path.is_file():
                try:
                    key = str(path.relative_to(QPROGRAM)).replace("\\", "/")
                except ValueError:
                    key = str(path.relative_to(ROOT)).replace("\\", "/")
                sources[key] = {
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "bytes": path.stat().st_size,
                    "note": override.get("note", ""),
                }
        (OUT_DIR / "sources.json").write_text(
            json.dumps({"note": "files read by tools/matte_sill.py",
                        "sources": sources}, indent=2, sort_keys=True),
            encoding="utf-8")
        print(f"wrote {len(report)} sprites to {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
