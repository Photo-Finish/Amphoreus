# -*- coding: utf-8 -*-
"""Trial ink-graph / paint-face matte for official Q sits.

Writes only under assets/eternal_page/q_program/_matte_v2/.
Does not touch live cutouts/, crops/, _preview/, or Eternal Page wiring.

    python tools/matte_q_faces.py
    python tools/matte_q_faces.py --guests

Official pixels only: RGB stays from the still; this pass deletes alpha.
No inpaint, no generated pixels.
"""
from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.cut_q_program import (  # noqa: E402
    CROP_BOXES,
    FRAME_CROPS,
    FRAMES,
    QP,
    SIT_CUTOUTS,
    _clamp_box,
    _fill_internal_holes,
    _magenta_preview,
    _open_rgb,
    _source_path,
    _upsample_cutout,
    isolate_rgb,
)

MATTE_ROOT = QP / "_matte_v2"
MATTE_CUTOUTS = MATTE_ROOT / "cutouts"
MATTE_PREVIEWS = MATTE_ROOT / "_preview"
MATTE_DEBUG = MATTE_ROOT / "debug"
LIVE_CUTOUTS = QP / "cutouts"

# Optional extras — never treated as circle bodies.
GUEST_SITS: tuple[str, ...] = (
    "robin_v38_sit.png",
    "the_herta_v35_sit.png",
    "himeko_v36_sit.png",
    "sunday_v36_sit.png",
    "witch_guest_v34_bili_t480.png",
)

# Working scale so 360p outlines have a usable stroke width.
WORK_MIN_LONG = 280
# Paint-face flood: neighbor Lab (per channel). Weak shading walks; ink dams.
LAB_LO = (12, 10, 10)
LAB_UP = (12, 10, 10)
# Second-pass merge of adjacent faces (Euclidean Lab).
LAB_MERGE = 12.0
# Ink: true dark strokes only. Weak shading / AA colour edges are NOT dams.
INK_L_HARD = 58
INK_L_SOFT = 88
INK_RIDGE = 16.0
INK_GRAD_PCTL = 78
STROKE_MIN_SRC = 0.7
STROKE_MAX_SRC = 6.5
# Morphological core.
CORE_ERODE_FRAC = 22
BAND_DILATE_FRAC = 12
# Ornament vs furniture area fractions of the tight crop.
ORNAMENT_MAX_FRAC = 0.11
FURNITURE_MIN_FRAC = 0.022
TINY_AREA = 22
FEATHER_PX = 1.8
PAD_COLORED = 16.0


def _refuse_outside_trial(dest: Path) -> Path:
    dest = dest.resolve()
    root = MATTE_ROOT.resolve()
    live = LIVE_CUTOUTS.resolve()
    if live == dest or live in dest.parents:
        raise RuntimeError(f"refusing to write live cutouts: {dest}")
    if dest != root and root not in dest.parents:
        raise RuntimeError(f"refusing to write outside _matte_v2: {dest}")
    return dest


def _spec_for(name: str) -> tuple[str, tuple[int, int, int, int]]:
    if name in CROP_BOXES:
        return CROP_BOXES[name]
    if name in FRAME_CROPS:
        return FRAME_CROPS[name]
    raise KeyError(f"no crop box for {name}")


def assert_identity_boxes() -> None:
    """Guardrails: Cyrene is 3.8 third sofa sitter; Hysilens is 3.5 overlay."""
    cyrene_src, cyrene_box = CROP_BOXES["cyrene_v38_sit.png"]
    if cyrene_box[0] < 740:
        raise RuntimeError(f"Cyrene box is not the third sofa sitter: {cyrene_box}")
    if "3.8" not in cyrene_src:
        raise RuntimeError(f"Cyrene sit must come from 3.8: {cyrene_src}")
    robin_box = CROP_BOXES["robin_v38_sit.png"][1]
    if robin_box[0] >= 700:
        raise RuntimeError(f"Robin guest box drifted: {robin_box}")
    hy_src, hy_box = CROP_BOXES["hysilens_v35_sit.png"]
    if "bilibili_3.5" not in hy_src or hy_box[2] > 220:
        raise RuntimeError(f"Hysilens is not the 3.5 overlay: {hy_src} {hy_box}")
    herta_src = CROP_BOXES["the_herta_v35_sit.png"][0]
    if "Announcement" not in herta_src:
        raise RuntimeError(f"The Herta must stay on the announcement: {herta_src}")
    ax_src, ax_box = CROP_BOXES["anaxa_v34_sit.png"]
    ph_src, ph_box = CROP_BOXES["phainon_v34_sit.png"]
    if "bilibili_3.4" not in ax_src or "bilibili_3.4" not in ph_src:
        raise RuntimeError("Anaxa/Phainon sits must be the 3.4 stage overlay")
    if ax_box[0] < 100 or ax_box[2] > 185 or ph_box[0] < 180 or ph_box[2] > 280:
        raise RuntimeError(f"Anaxa/Phainon boxes mixed: {ax_box} {ph_box}")


def padded_context(full: Image.Image, box: tuple[int, int, int, int]) -> dict:
    """Tight crop plus pad ring. Matches cutout_from_announcement geometry.

    Filled canvas is for the isolate seed; natural canvas keeps official ring
    pixels so sofa/ice can connect to the pad without crossing ink.
    """
    rgb_full = np.array(full.convert("RGB"))
    H, W = rgb_full.shape[:2]
    l, t, r, b = _clamp_box(box, W, H)
    tw, th = r - l, b - t
    ring = max(28, min(tw, th) // 5)
    el, et = max(0, l - ring), max(0, t - ring)
    er, eb = min(W, r + ring), min(H, b + ring)
    context = rgb_full[et:eb, el:er]
    tl, tt = l - el, t - et
    margin = np.ones(context.shape[:2], dtype=bool)
    margin[tt : tt + th, tl : tl + tw] = False
    if int(margin.sum()) >= 80:
        bg = np.median(context[margin], axis=0)
    else:
        bg = np.median(context.reshape(-1, 3), axis=0)
    filled_ctx = context.copy()
    filled_ctx[margin] = bg.astype(np.uint8)
    halo = 18
    ch, cw = context.shape[:2]
    filled = np.empty((ch + 2 * halo, cw + 2 * halo, 3), np.uint8)
    filled[:, :] = bg.astype(np.uint8)
    filled[halo : halo + ch, halo : halo + cw] = filled_ctx
    natural = np.empty_like(filled)
    natural[:, :] = bg.astype(np.uint8)
    natural[halo : halo + ch, halo : halo + cw] = context
    y0, x0 = halo + tt, halo + tl
    pad_mask = np.ones(filled.shape[:2], dtype=bool)
    pad_mask[y0 : y0 + th, x0 : x0 + tw] = False
    return {
        "filled": filled,
        "natural": natural,
        "bg": bg.astype(np.float32),
        "pad_mask": pad_mask,
        "crop": (y0, y0 + th, x0, x0 + tw),
        "tight_rgb": rgb_full[t:b, l:r],
        "box": (l, t, r, b),
        "size": (tw, th),
        "halo": halo,
    }


def _maybe_upscale(
    filled: np.ndarray,
    natural: np.ndarray,
    pad_mask: np.ndarray,
    crop: tuple[int, int, int, int],
    min_long: int = WORK_MIN_LONG,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[int, int, int, int], float]:
    h, w = filled.shape[:2]
    long = max(h, w)
    if long >= min_long:
        return filled, natural, pad_mask, crop, 1.0
    scale = min_long / float(long)
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    filled2 = cv2.resize(filled, (nw, nh), interpolation=cv2.INTER_LINEAR)
    natural2 = cv2.resize(natural, (nw, nh), interpolation=cv2.INTER_LINEAR)
    pad2 = cv2.resize(pad_mask.astype(np.uint8), (nw, nh), interpolation=cv2.INTER_NEAREST) > 0
    y0, y1, x0, x1 = crop
    crop2 = (
        int(round(y0 * scale)),
        int(round(y1 * scale)),
        int(round(x0 * scale)),
        int(round(x1 * scale)),
    )
    crop2 = (
        max(0, crop2[0]),
        min(nh, crop2[1]),
        max(0, crop2[2]),
        min(nw, crop2[3]),
    )
    return filled2, natural2, pad2, crop2, scale


def detect_ink(lab: np.ndarray, scale: float = 1.0) -> np.ndarray:
    """Ink = dark ridge strokes of width ~1–6 px. Weak shading is not a dam."""
    L = lab[:, :, 0].astype(np.float32)
    gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    g_floor = float(np.percentile(mag, INK_GRAD_PCTL))
    high_g = mag >= max(28.0, g_floor)
    # Darker than the local neighbourhood = a stroke, not a colour step between mids.
    neigh = cv2.blur(L, (7, 7))
    ridge = (neigh - L) >= INK_RIDGE
    dark = L <= INK_L_HARD
    dark_aa = (L <= INK_L_SOFT) & high_g & ridge
    cand = (ridge & (dark | dark_aa)).astype(np.uint8)
    if int(cand.sum()) < 12:
        return cand
    stroke_min = STROKE_MIN_SRC * scale
    stroke_max = STROKE_MAX_SRC * scale
    dt = cv2.distanceTransform(cand, cv2.DIST_L2, 3)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(cand, 8)
    h, w = cand.shape
    ink = np.zeros_like(cand)
    min_dim = min(h, w)
    for i in range(1, num):
        x, y, bw, bh, area = stats[i]
        if area < max(8, int(round(6 * scale))):
            continue
        # Long hairline stage rules — not character ink.
        if (min(bw, bh) <= max(2, int(round(3 * scale)))) and (
            max(bw, bh) > min_dim * 0.45
        ):
            continue
        widths = dt[labels == i]
        max_w = float(widths.max()) * 2.0
        if max_w < stroke_min * 0.5:
            continue
        if max_w > stroke_max * 1.45:
            continue
        ink[labels == i] = 1
    if int(ink.sum()) < 8:
        return ink
    # Close 1 px AA gaps in true outlines only.
    ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return (ink > 0).astype(np.uint8)


def paint_faces(lab: np.ndarray, ink: np.ndarray) -> tuple[np.ndarray, int]:
    """Faces = paint regions. Merge neighbors with small Lab distance not split by ink."""
    h, w = ink.shape
    # Flatten weak shading so it is not treated as a dam.
    img = cv2.bilateralFilter(np.ascontiguousarray(lab), 5, 18, 4)
    mask = np.zeros((h + 2, w + 2), np.uint8)
    mask[1:-1, 1:-1][ink > 0] = 1
    face_id = np.zeros((h, w), np.int32)
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
    lo = LAB_LO
    up = LAB_UP
    fid = 0
    remaining = (ink == 0)
    idx = 0
    ys, xs = np.where(remaining)
    n_seed = int(ys.size)
    while idx < n_seed:
        y, x = int(ys[idx]), int(xs[idx])
        idx += 1
        if face_id[y, x] or ink[y, x] or mask[y + 1, x + 1]:
            continue
        fid += 1
        cv2.floodFill(img, mask, (x, y), 0, lo, up, flags)
        filled = mask[1:-1, 1:-1] == 255
        if not np.any(filled):
            face_id[y, x] = fid
            mask[y + 1, x + 1] = 1
            continue
        face_id[filled] = fid
        mask[1:-1, 1:-1][filled] = 1
    return face_id, fid


def _face_means(face_id: np.ndarray, lab: np.ndarray, n: int) -> np.ndarray:
    flat = face_id.ravel()
    counts = np.bincount(flat, minlength=n + 1).astype(np.float64)
    means = np.zeros((n + 1, 3), np.float64)
    labf = lab.reshape(-1, 3).astype(np.float64)
    for c in range(3):
        means[:, c] = np.bincount(flat, labf[:, c], minlength=n + 1)
    counts_safe = np.maximum(counts, 1.0)
    means /= counts_safe[:, None]
    means[counts == 0] = 0
    return means


def _remap_faces(face_id: np.ndarray, mapping: np.ndarray) -> tuple[np.ndarray, int]:
    remapped = mapping[face_id]
    unused = remapped == 0
    inkish = face_id == 0
    remapped[unused & ~inkish] = 0
    ids = np.unique(remapped)
    ids = ids[ids > 0]
    compact = np.zeros(int(mapping.max()) + 1, np.int32)
    for i, fid in enumerate(ids, start=1):
        compact[fid] = i
    out = compact[remapped]
    out[face_id == 0] = 0
    return out, int(ids.size)


def merge_faces(face_id: np.ndarray, lab: np.ndarray, n: int) -> tuple[np.ndarray, int]:
    """Merge tiny faces and adjacent paint with small Lab distance."""
    if n <= 1:
        return face_id, n
    h, w = face_id.shape
    means = _face_means(face_id, lab, n)
    counts = np.bincount(face_id.ravel(), minlength=n + 1)
    parent = np.arange(n + 1, dtype=np.int32)

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = int(parent[x])
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if counts[ra] < counts[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        tot = counts[ra] + counts[rb]
        if tot > 0:
            means[ra] = (means[ra] * counts[ra] + means[rb] * counts[rb]) / tot
            counts[ra] = tot

    adj: dict[tuple[int, int], int] = {}

    def add_pairs(a: np.ndarray, b: np.ndarray) -> None:
        mask = (a > 0) & (b > 0) & (a != b)
        if not np.any(mask):
            return
        aa = a[mask].astype(np.int32)
        bb = b[mask].astype(np.int32)
        lo = np.minimum(aa, bb)
        hi = np.maximum(aa, bb)
        packed = lo.astype(np.int64) * (n + 1) + hi
        uniq, cnt = np.unique(packed, return_counts=True)
        for code, c in zip(uniq.tolist(), cnt.tolist()):
            i = int(code // (n + 1))
            j = int(code % (n + 1))
            adj[(i, j)] = adj.get((i, j), 0) + int(c)

    add_pairs(face_id[:, :-1], face_id[:, 1:])
    add_pairs(face_id[:-1, :], face_id[1:, :])

    for (i, j), border in adj.items():
        if i == 0 or j == 0:
            continue
        di = float(np.linalg.norm(means[i] - means[j]))
        tiny = counts[i] < TINY_AREA or counts[j] < TINY_AREA
        small_both = max(counts[i], counts[j]) < max(80, int(0.012 * h * w))
        if tiny and border >= 2:
            union(i, j)
        elif small_both and di <= LAB_MERGE and border >= 4:
            union(i, j)

    mapping = np.array([find(i) for i in range(n + 1)], dtype=np.int32)
    mapping[0] = 0
    return _remap_faces(face_id, mapping)


def face_adjacency(face_id: np.ndarray, n: int) -> list[set[int]]:
    adj: list[set[int]] = [set() for _ in range(n + 1)]

    def walk(a: np.ndarray, b: np.ndarray) -> None:
        mask = (a > 0) & (b > 0) & (a != b)
        if not np.any(mask):
            return
        aa = a[mask]
        bb = b[mask]
        packed = np.minimum(aa, bb).astype(np.int64) * (n + 1) + np.maximum(aa, bb)
        for code in np.unique(packed).tolist():
            i = int(code // (n + 1))
            j = int(code % (n + 1))
            adj[i].add(j)
            adj[j].add(i)

    walk(face_id[:, :-1], face_id[:, 1:])
    walk(face_id[:-1, :], face_id[1:, :])
    return adj


def split_bimodal_faces(
    face_id: np.ndarray, lab: np.ndarray, n: int, min_area: int, min_delta: float = 18.0
) -> tuple[np.ndarray, int]:
    """Split large paint faces that mix character and backdrop colour."""
    out = face_id.copy()
    nxt = n
    labf = lab.astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 14, 0.8)
    for fid in range(1, n + 1):
        mask = face_id == fid
        area = int(mask.sum())
        if area < min_area:
            continue
        pts = labf[mask]
        if pts.shape[0] < 40:
            continue
        flags = cv2.KMEANS_PP_CENTERS
        _, labels, centers = cv2.kmeans(pts, 2, None, criteria, 4, flags)
        if float(np.linalg.norm(centers[0] - centers[1])) < min_delta:
            continue
        n0 = int((labels == 0).sum())
        n1 = int((labels == 1).sum())
        if min(n0, n1) < max(25, int(0.10 * area)):
            continue
        nxt += 1
        ys, xs = np.where(mask)
        pick = labels.ravel() == 1
        out[ys[pick], xs[pick]] = nxt
    return out, nxt


def split_large_straddles(
    face_id: np.ndarray, core: np.ndarray, n: int, min_part: int
) -> tuple[np.ndarray, int]:
    """Split large faces that sit both in the eroded core and outside it."""
    core_b = core > 0
    out = face_id.copy()
    nxt = n
    for fid in range(1, n + 1):
        mask = face_id == fid
        area = int(mask.sum())
        if area < min_part * 2:
            continue
        inside = mask & core_b
        outside = mask & ~core_b
        inn, outn = int(inside.sum()), int(outside.sum())
        if inn >= min_part and outn >= min_part:
            nxt += 1
            out[outside] = nxt
    return out, nxt


def rough_core(
    filled: np.ndarray,
    natural_lab: np.ndarray,
    pad_mask: np.ndarray,
    crop: tuple[int, int, int, int],
    bg_lab: np.ndarray,
) -> np.ndarray:
    """Eroded character core from current-style isolate + central / unlike-pad."""
    h, w = pad_mask.shape
    y0, y1, x0, x1 = crop
    alpha = isolate_rgb(filled)
    fg = (alpha > 127).astype(np.uint8)
    dist_pad = np.full((h, w), 1e6, np.float32)
    for c in _color_centers(natural_lab, pad_mask) or [bg_lab]:
        dist_pad = np.minimum(
            dist_pad,
            np.linalg.norm(natural_lab.astype(np.float32) - c.reshape(1, 1, 3), axis=2).astype(
                np.float32
            ),
        )
    th, tw = y1 - y0, x1 - x0
    # Face/torso colour from a small central patch — sofa behind the sitter is not this.
    pr = max(12, min(th, tw) // 6)
    pcx = (x0 + x1) // 2
    pcy = y0 + int(th * 0.40)
    patch = np.zeros((h, w), np.uint8)
    cv2.ellipse(patch, (pcx, pcy), (pr, int(pr * 1.25)), 0, 0, 360, 1, -1)
    cv2.ellipse(
        patch, (pcx, y0 + int(th * 0.52)), (int(pr * 0.85), pr), 0, 0, 360, 1, -1
    )
    patch = (patch > 0) & (fg > 0) & (~pad_mask)
    char_centers = _color_centers(natural_lab, patch)
    if not char_centers:
        char_centers = _color_centers(natural_lab, (fg > 0) & (~pad_mask))
    dist_char = np.full((h, w), 1e6, np.float32)
    for c in char_centers or [bg_lab]:
        dist_char = np.minimum(
            dist_char,
            np.linalg.norm(natural_lab.astype(np.float32) - c.reshape(1, 1, 3), axis=2).astype(
                np.float32
            ),
        )
    unlike = np.zeros((h, w), np.uint8)
    work = fg > 0
    floor = 16.0
    if int(work.sum()) >= 40:
        vals = dist_pad[work]
        floor = max(15.0, float(np.percentile(vals, 45)))
        unlike[(dist_pad >= floor) & work] = 1
    near_char = (dist_char <= 24.0) | (dist_char + 3.0 < dist_pad)
    body = np.zeros((h, w), np.uint8)
    bx0 = x0 + int(tw * 0.20)
    bx1 = x0 + int(tw * 0.80)
    by0 = y0 + int(th * 0.02)
    by1 = y0 + int(th * 0.78)
    body[by0:by1, bx0:bx1] = 1
    seed = ((fg > 0) & near_char).astype(np.uint8)
    seed |= ((fg > 0) & (body > 0) & (unlike > 0) & near_char).astype(np.uint8)
    seed[pad_mask] = 0
    # Strip pad-like sit furniture under the feet from the core.
    by_feet = y0 + int(th * 0.82)
    bottom = np.zeros((h, w), np.uint8)
    bottom[by_feet:y1, x0:x1] = 1
    seed[(bottom > 0) & (unlike == 0)] = 0
    if int(seed.sum()) < 40:
        seed = fg.copy()
        seed[pad_mask] = 0
    seed = cv2.morphologyEx(seed, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    num, labels, stats, cents = cv2.connectedComponentsWithStats(seed, 8)
    core = np.zeros((h, w), np.uint8)
    if num <= 1:
        core = seed
    else:
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        best = None
        for i in range(1, num):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < (th * tw) * 0.012:
                continue
            mx, my = cents[i]
            score = area - 0.35 * area * (abs(mx - cx) / max(tw, 1) + abs(my - cy) / max(th, 1))
            if best is None or score > best[0]:
                best = (score, i)
        if best is None:
            i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            core[labels == i] = 1
        else:
            core[labels == best[1]] = 1
    k = max(3, min(th, tw) // CORE_ERODE_FRAC)
    if k % 2 == 0:
        k += 1
    eroded = cv2.erode(core, np.ones((k, k), np.uint8))
    if int(eroded.sum()) < max(120, int(0.06 * th * tw)):
        k2 = max(3, k - 2)
        if k2 % 2 == 0:
            k2 += 1
        eroded = cv2.erode(core, np.ones((k2, k2), np.uint8))
    if int(eroded.sum()) < 80:
        eroded = core
    return eroded


def _color_centers(lab: np.ndarray, mask: np.ndarray) -> list[np.ndarray]:
    pts = lab[mask].astype(np.float32).reshape(-1, 3)
    if pts.shape[0] < 12:
        return [pts.mean(axis=0)] if pts.shape[0] else []
    centers = [pts.mean(axis=0)]
    L = pts[:, 0]
    med = float(np.median(L))
    light = pts[L >= med]
    dark = pts[L < med]
    if light.shape[0] >= 16:
        centers.append(light.mean(axis=0))
    if dark.shape[0] >= 16:
        centers.append(dark.mean(axis=0))
    return centers


def _min_lab_dist(mu: np.ndarray, centers: list[np.ndarray]) -> float:
    if not centers:
        return 999.0
    return float(min(np.linalg.norm(mu - c) for c in centers))


def _lowest_solid_row(core: np.ndarray, crop: tuple[int, int, int, int]) -> int:
    y0, y1, x0, x1 = crop
    sl = core[y0:y1, x0:x1]
    if sl.size == 0:
        return y1
    counts = sl.sum(axis=1)
    need = max(4, sl.shape[1] * 0.05)
    solid = np.where(counts >= need)[0]
    if solid.size:
        return y0 + int(solid[-1])
    any_row = np.where(counts > 0)[0]
    if any_row.size:
        return y0 + int(any_row[-1])
    return y1


def _border_ink_and_neighbors(
    face_id: np.ndarray,
    fid: int,
    ink: np.ndarray,
    char_ids: set[int],
    env_ids: set[int],
) -> tuple[float, int, int, int, int]:
    """ink-border fraction, neighbor paint counts, ink-toward-character count."""
    mask = face_id == fid
    if not np.any(mask):
        return 0.0, 0, 0, 0, 0
    dil = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8))
    border = (dil > 0) & (~mask)
    bcount = int(border.sum())
    if bcount == 0:
        return 0.0, 0, 0, 0, 0
    ink_n = int((border & (ink > 0)).sum())
    nb = face_id[border]
    adj_char = int(np.isin(nb, np.fromiter(char_ids, np.int32) if char_ids else np.array([], np.int32)).sum())
    adj_env = int(np.isin(nb, np.fromiter(env_ids, np.int32) if env_ids else np.array([], np.int32)).sum())
    # Ink pixels on the border that also touch Character₀.
    if char_ids:
        char_mask = np.isin(face_id, np.fromiter(char_ids, np.int32))
        ink_toward = int((border & (ink > 0) & cv2.dilate(char_mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)).sum())
    else:
        ink_toward = 0
    return ink_n / bcount, adj_char, adj_env, bcount, ink_toward


def classify_faces(
    face_id: np.ndarray,
    n: int,
    lab: np.ndarray,
    ink: np.ndarray,
    core: np.ndarray,
    pad_mask: np.ndarray,
    crop: tuple[int, int, int, int],
    bg_lab: np.ndarray,
) -> tuple[np.ndarray, dict]:
    """Core lock, environment flood, ambiguous-band clustering. Returns keep mask."""
    h, w = face_id.shape
    y0, y1, x0, x1 = crop
    crop_area = max(1, (y1 - y0) * (x1 - x0))
    counts = np.bincount(face_id.ravel(), minlength=n + 1)
    means = _face_means(face_id, lab, n)
    core_b = core > 0
    core_counts = np.bincount(face_id[core_b], minlength=n + 1) if np.any(core_b) else np.zeros(n + 1, np.int64)
    pad_counts = np.bincount(face_id[pad_mask], minlength=n + 1) if np.any(pad_mask) else np.zeros(n + 1, np.int64)

    adj = face_adjacency(face_id, n)
    pad_faces = {i for i in range(1, n + 1) if pad_counts[i] > 0}
    # G′: faces reachable from the pad without crossing ink (edges already skip ink).
    env0: set[int] = set()
    dq: deque[int] = deque(sorted(pad_faces))
    seen = set(pad_faces)
    while dq:
        u = dq.popleft()
        env0.add(u)
        for v in adj[u]:
            if v and v not in seen:
                seen.add(v)
                dq.append(v)

    env_pix_early = pad_mask & (face_id > 0)
    if int(env_pix_early.sum()) >= 20:
        env_mean_early = lab[env_pix_early].astype(np.float32).mean(axis=0)
    else:
        env_mean_early = bg_lab.astype(np.float32)
    env_centers_early = _color_centers(lab, pad_mask) or [env_mean_early]

    char0: set[int] = set()
    env_sure: set[int] = set()
    undecided: set[int] = set()
    for i in range(1, n + 1):
        if counts[i] <= 0:
            continue
        frac_core = core_counts[i] / max(counts[i], 1)
        frac_pad = pad_counts[i] / max(counts[i], 1)
        d_env = _min_lab_dist(means[i], env_centers_early)
        pad_colored = d_env <= PAD_COLORED
        too_big = counts[i] > 0.35 * h * w
        if (
            frac_core >= 0.50
            and frac_pad < 0.12
            and not pad_colored
            and not too_big
        ):
            char0.add(i)
        elif i in env0 and core_counts[i] < max(6, int(counts[i] * 0.06)) and (
            pad_colored or frac_pad > 0.08
        ):
            env_sure.add(i)
        elif i in env0 and pad_colored and frac_core < 0.35:
            # Sofa/ice continuing from the pad, even if isolate glued some of it.
            env_sure.add(i)
        else:
            undecided.add(i)

    # Morphological band between dilated core and Environment₀.
    k = max(3, min(y1 - y0, x1 - x0) // BAND_DILATE_FRAC)
    if k % 2 == 0:
        k += 1
    dilated = cv2.dilate(core.astype(np.uint8), np.ones((k, k), np.uint8))
    band = (dilated > 0) & (~core_b)
    band_ids = set(np.unique(face_id[band]).tolist()) - {0}
    for i in band_ids:
        if i not in char0:
            env_sure.discard(i)
            undecided.add(i)
    # Environment₀ overlapping eroded core → step 4, never auto-delete —
    # except pad-colored furniture whose mass is still mostly outside the core.
    for i in list(env0):
        if i in char0:
            continue
        if core_counts[i] >= 6:
            frac_core = core_counts[i] / max(counts[i], 1)
            d_env = _min_lab_dist(means[i], env_centers_early)
            if d_env <= PAD_COLORED and frac_core < 0.45:
                continue
            env_sure.discard(i)
            undecided.add(i)

    # Enclosed leftovers (not env-reachable, not char0) stay character interiors.
    enclosed = {i for i in range(1, n + 1) if counts[i] > 0 and i not in env0 and i not in char0}
    for i in enclosed:
        undecided.discard(i)
        env_sure.discard(i)
        char0.add(i)

    char_mask_ids = char0
    env_mask_ids = env_sure
    # Two-seed cluster: eroded-core colours vs pad ring colours (not poisoned faces).
    d_to_env = np.full((h, w), 1e6, np.float32)
    for c in env_centers_early:
        d_to_env = np.minimum(
            d_to_env,
            np.linalg.norm(lab.astype(np.float32) - c.reshape(1, 1, 3), axis=2).astype(np.float32),
        )
    core_seed = core_b & (d_to_env > PAD_COLORED)
    if int(core_seed.sum()) >= 40:
        char_mean = lab[core_seed].astype(np.float32).mean(axis=0)
    elif np.any(core_b):
        char_mean = lab[core_b].astype(np.float32).mean(axis=0)
    else:
        char_mean = bg_lab + np.array([20.0, 0.0, 0.0], np.float32)
    env_mean = env_mean_early
    env_centers = env_centers_early
    char_centers = _color_centers(lab, core_seed if int(core_seed.sum()) >= 40 else core_b)
    if not char_centers:
        char_centers = [char_mean]

    lowest = _lowest_solid_row(core, crop)
    keep_ids = set(char0)
    del_ids = set(env_sure)
    th, tw = y1 - y0, x1 - x0

    # Tiny faces follow a later pass; first classify the rest.
    tiny_ids = {i for i in undecided if counts[i] < TINY_AREA}
    work_ids = [i for i in sorted(undecided) if i not in tiny_ids]

    for i in work_ids:
        mu = means[i]
        d_char = _min_lab_dist(mu, char_centers)
        d_env = _min_lab_dist(mu, env_centers)
        area = int(counts[i])
        ys, xs = np.where(face_id == i)
        cy = float(ys.mean()) if ys.size else 0.0
        cx = float(xs.mean()) if xs.size else 0.0
        ink_frac, adj_char, adj_env, bcount, ink_toward = _border_ink_and_neighbors(
            face_id, i, ink, char_mask_ids, env_mask_ids
        )
        below = cy > (lowest - 0.03 * th)
        near_side = (cx < x0 + 0.12 * tw) or (cx > x1 - 0.12 * tw)
        near_bottom = cy > y0 + 0.80 * th
        pad_like = d_env + 1.8 < d_char
        pad_like_strong = d_env <= 14.0 and d_env + 4.0 < d_char
        nearer_char = d_char + 1.2 < d_env
        nearer_env = d_env + 1.2 < d_char
        ink_locked = (adj_char >= 4 and ink_frac >= 0.12) or (ink_toward >= 3 and adj_char >= 2)
        little_ink_to_body = ink_toward <= max(2, int(0.08 * max(bcount, 1)))
        ornament_size = area <= ORNAMENT_MAX_FRAC * crop_area
        furniture_size = area >= FURNITURE_MIN_FRAC * crop_area
        # Lap companion prior: inside the core bbox, above the feet line, attached.
        in_lap = (cy <= lowest - 0.02 * th) and (cy >= y0 + 0.35 * th) and (
            x0 + 0.18 * tw <= cx <= x1 - 0.18 * tw
        )
        bright = mu[0] >= 150
        keep = False
        delete = False
        # Giant pad-connected paint is sit furniture, not an ornament.
        if (i in env0) and area >= 0.16 * crop_area and (pad_like or nearer_env or d_env <= PAD_COLORED + 4):
            del_ids.add(i)
            env_mask_ids.add(i)
            continue
        if ink_locked and ornament_size and not pad_like_strong:
            keep = True
        elif in_lap and (ink_locked or adj_char >= 6) and (nearer_char or bright) and not pad_like_strong:
            keep = True
        elif (below or near_bottom) and furniture_size and little_ink_to_body and not (
            ink_locked and ornament_size
        ):
            delete = True
        elif (below or near_bottom or (near_side and pad_like)) and pad_like and little_ink_to_body:
            delete = True
        elif nearer_char and not (below and furniture_size):
            keep = True
        elif nearer_env and not ink_locked:
            delete = True
        elif adj_char > adj_env * 1.4 and not pad_like_strong and not (below and furniture_size):
            keep = True
        elif pad_like and (below or near_bottom or near_side) and not ink_locked:
            delete = True
        elif ink_locked and ornament_size:
            keep = True
        else:
            delete = nearer_env or (i in env0) or (below and furniture_size)

        if keep and delete:
            # Ink-lock / lap ornaments win unless the region is large pad-like furniture.
            if furniture_size and pad_like_strong and (below or near_bottom):
                keep, delete = False, True
            else:
                keep, delete = True, False
        if keep:
            keep_ids.add(i)
            char_mask_ids.add(i)
        else:
            del_ids.add(i)
            env_mask_ids.add(i)

    # Tiny faces follow the dominant neighbor.
    for i in sorted(tiny_ids):
        nbs = [v for v in adj[i] if v]
        score_k = sum(counts[v] for v in nbs if v in keep_ids)
        score_d = sum(counts[v] for v in nbs if v in del_ids)
        if score_k > score_d:
            keep_ids.add(i)
        elif score_d > score_k:
            del_ids.add(i)
        else:
            mu = means[i]
            if np.linalg.norm(mu - char_mean) <= np.linalg.norm(mu - env_mean):
                keep_ids.add(i)
            else:
                del_ids.add(i)

    keep_mask = np.zeros((h, w), np.uint8)
    if keep_ids:
        keep_mask[np.isin(face_id, np.fromiter(keep_ids, np.int32))] = 1
    # Reclaim ink that touches a kept face (character outlines, not stage rules).
    if np.any(ink):
        touch = cv2.dilate(keep_mask, np.ones((3, 3), np.uint8))
        keep_mask[(ink > 0) & (touch > 0)] = 1

    debug = {
        "char0": char0,
        "env_sure": env_sure,
        "undecided": undecided,
        "keep_ids": keep_ids,
        "n_faces": n,
        "lowest": lowest,
    }
    return keep_mask, debug


def keep_to_alpha(keep: np.ndarray, crop: tuple[int, int, int, int]) -> np.ndarray:
    y0, y1, x0, x1 = crop
    fg = keep.copy()
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    sl = fg[y0:y1, x0:x1]
    sl = _fill_internal_holes(sl)
    fg[y0:y1, x0:x1] = sl
    dist_bg = cv2.distanceTransform((1 - fg).astype(np.uint8), cv2.DIST_L2, 3)
    alpha = np.zeros(fg.shape, np.float32)
    alpha[fg > 0] = 1.0
    edge = (dist_bg > 0) & (dist_bg < FEATHER_PX)
    alpha[edge] = np.clip(1.0 - dist_bg[edge] / FEATHER_PX, 0, 1)
    return (alpha[y0:y1, x0:x1] * 255.0).astype(np.uint8)


def _debug_map(
    rgb: np.ndarray,
    ink: np.ndarray,
    face_id: np.ndarray,
    keep: np.ndarray,
    core: np.ndarray,
    pad_mask: np.ndarray,
    crop: tuple[int, int, int, int],
    debug: dict,
) -> np.ndarray:
    vis = rgb.copy()
    char0 = debug.get("char0") or set()
    env_sure = debug.get("env_sure") or set()
    undecided = debug.get("undecided") or set()
    overlay = vis.astype(np.float32)
    if char0:
        m = np.isin(face_id, np.fromiter(char0, np.int32))
        overlay[m] = overlay[m] * 0.55 + np.array([40, 200, 70], np.float32) * 0.45
    if env_sure:
        m = np.isin(face_id, np.fromiter(env_sure, np.int32))
        overlay[m] = overlay[m] * 0.55 + np.array([220, 40, 40], np.float32) * 0.45
    if undecided:
        m = np.isin(face_id, np.fromiter(undecided, np.int32))
        overlay[m] = overlay[m] * 0.55 + np.array([230, 210, 40], np.float32) * 0.45
    overlay[ink > 0] = overlay[ink > 0] * 0.25 + np.array([20, 20, 20], np.float32) * 0.75
    y0, y1, x0, x1 = crop
    out = np.clip(overlay, 0, 255).astype(np.uint8)
    cv2.rectangle(out, (x0, y0), (x1 - 1, y1 - 1), (0, 180, 255), 1)
    return out[y0:y1, x0:x1]


def matte_from_announcement(
    full: Image.Image,
    box: tuple[int, int, int, int],
    dest: Path,
    preview_dir: Path | None = None,
    debug_dir: Path | None = None,
) -> dict:
    dest = _refuse_outside_trial(dest)
    ctx = padded_context(full, box)
    filled, natural, pad_mask, crop, scale = _maybe_upscale(
        ctx["filled"], ctx["natural"], ctx["pad_mask"], ctx["crop"]
    )
    lab = cv2.cvtColor(natural, cv2.COLOR_RGB2LAB)
    bg_lab = cv2.cvtColor(ctx["bg"].reshape(1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2LAB)[0, 0].astype(
        np.float32
    )
    ink = detect_ink(lab, scale=scale)
    face_id, n = paint_faces(lab, ink)
    face_id, n = merge_faces(face_id, lab, n)
    core = rough_core(filled, lab, pad_mask, crop, bg_lab)
    y0c, y1c, x0c, x1c = crop
    crop_area = max(1, (y1c - y0c) * (x1c - x0c))
    min_bimodal = max(90, int(0.045 * crop_area))
    face_id, n = split_bimodal_faces(face_id, lab, n, min_area=min_bimodal)
    face_id, n = split_bimodal_faces(face_id, lab, n, min_area=min_bimodal)
    min_part = max(40, int(0.02 * crop_area))
    band_k = max(9, min(y1c - y0c, x1c - x0c) // 10)
    if band_k % 2 == 0:
        band_k += 1
    core_for_split = cv2.dilate(core, np.ones((band_k, band_k), np.uint8))
    face_id, n = split_large_straddles(face_id, core_for_split, n, min_part=min_part)
    keep, debug = classify_faces(face_id, n, lab, ink, core, pad_mask, crop, bg_lab)
    alpha_work = keep_to_alpha(keep, crop)
    tw, th = ctx["size"]
    if alpha_work.shape[0] != th or alpha_work.shape[1] != tw:
        alpha = cv2.resize(alpha_work, (tw, th), interpolation=cv2.INTER_LINEAR)
    else:
        alpha = alpha_work
    rgb = ctx["tight_rgb"]
    if int((alpha > 32).sum()) < 40:
        # Fail-soft: keep the isolate seed rather than an empty sprite.
        y0, y1, x0, x1 = crop
        fallback = isolate_rgb(filled)[y0:y1, x0:x1]
        if fallback.shape[0] != th or fallback.shape[1] != tw:
            fallback = cv2.resize(fallback, (tw, th), interpolation=cv2.INTER_LINEAR)
        alpha = fallback
        debug["fallback_isolate"] = True
    rgba = np.dstack([rgb, alpha])
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(dest, "PNG")
    if preview_dir is not None:
        preview_dir = _refuse_outside_trial(preview_dir)
        preview_dir.mkdir(parents=True, exist_ok=True)
        prev = _magenta_preview(rgba)
        Image.fromarray(prev, "RGB").save(preview_dir / dest.name, "PNG")
    if debug_dir is not None:
        debug_dir = _refuse_outside_trial(debug_dir)
        debug_dir.mkdir(parents=True, exist_ok=True)
        y0, y1, x0, x1 = crop
        rgb_work = natural[y0:y1, x0:x1]
        if rgb_work.shape[0] != th or rgb_work.shape[1] != tw:
            labels = _debug_map(natural, ink, face_id, keep, core, pad_mask, crop, debug)
            labels = cv2.resize(labels, (tw, th), interpolation=cv2.INTER_NEAREST)
        else:
            labels = _debug_map(natural, ink, face_id, keep, core, pad_mask, crop, debug)
        Image.fromarray(labels, "RGB").save(debug_dir / dest.name, "PNG")
    cov = float(alpha.mean()) / 255.0
    return {
        "file": dest.name,
        "coverage": round(cov, 3),
        "size": f"{tw}x{th}",
        "faces": int(debug.get("n_faces") or n),
        "path": str(dest),
    }


def matte_sit(name: str, cache: dict[str, Image.Image] | None = None) -> dict:
    spec = _spec_for(name)
    src_name, box = spec
    cache = cache if cache is not None else {}
    if src_name not in cache:
        cache[src_name] = _open_rgb(src_name)
    dest = MATTE_CUTOUTS / name
    info = matte_from_announcement(
        cache[src_name],
        box,
        dest,
        MATTE_PREVIEWS,
        MATTE_DEBUG,
    )
    src_path = _source_path(src_name)
    if src_path.parent == FRAMES:
        _upsample_cutout(dest, MATTE_PREVIEWS / name)
        im = Image.open(dest)
        info["size"] = f"{im.width}x{im.height}"
        info["upsampled"] = True
    return info


def matte_names(include_guests: bool = False) -> list[str]:
    names = list(SIT_CUTOUTS)
    if include_guests:
        for g in GUEST_SITS:
            if g not in names:
                try:
                    _spec_for(g)
                except KeyError:
                    continue
                names.append(g)
    return names


def matte_all(include_guests: bool = False, only: list[str] | None = None) -> list[dict]:
    assert_identity_boxes()
    MATTE_CUTOUTS.mkdir(parents=True, exist_ok=True)
    MATTE_PREVIEWS.mkdir(parents=True, exist_ok=True)
    MATTE_DEBUG.mkdir(parents=True, exist_ok=True)
    names = only if only else matte_names(include_guests=include_guests)
    reports: list[dict] = []
    cache: dict[str, Image.Image] = {}
    for name in names:
        try:
            info = matte_sit(name, cache)
        except FileNotFoundError as exc:
            print(f"skip {name}: {exc}")
            continue
        reports.append(info)
        print(
            f"matte {info['file']} coverage={info['coverage']} "
            f"{info['size']} faces={info.get('faces')}"
        )
    return reports


def write_readme() -> None:
    dest = _refuse_outside_trial(MATTE_ROOT / "README.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        """# Q-sit face-graph matte (trial v2)

Independent trial of the ink-graph / paint-face backdrop eraser.

**Not wired** into Eternal Page (`src/world/eternal_q.py` still reads `../cutouts/`).
Live `cutouts/`, `crops/`, and `_preview/` from `tools/cut_q_program.py` are untouched.

- `cutouts/` — RGBA; official RGB, alpha only
- `_preview/` — magenta-on-#FF00FF composites (the Read tool ignores PNG alpha)
- `debug/` — face labels: green Character₀, red environment, yellow undecided, dark ink

Run: `python tools/matte_q_faces.py` (add `--guests` for optional extras)

Close ornaments (Ica, chimera, crown, hat, tail, Tribbie's swing if held) are
meant to stay. Sofa / ice / window / branch the character sits on are meant to go.
Guests in this folder are extras, not circle bodies.

Known trial limits: 360p sits (Hysilens, Phainon, Anaxa) stay muddy; some sofas
(Evernight, Castorice) and Mydei's cup/fruit may still glue or vanish.
""",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Trial Q-sit face-graph matte → _matte_v2/")
    ap.add_argument("--guests", action="store_true", help="also matte optional guest sits")
    ap.add_argument("--only", nargs="*", help="subset of filenames")
    args = ap.parse_args()
    write_readme()
    matte_all(include_guests=bool(args.guests), only=args.only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
