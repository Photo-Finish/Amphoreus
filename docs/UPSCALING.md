# Upscaling the low-resolution art

**Date:** 2026-10-27
**Tool:** `tools/upscale_art.py` · **Suite:** `tools/test_upscale_art.py` (13 checks)
**Model:** Real-ESRGAN (ncnn-vulkan), `models/realesrgan/` — gitignored

---

## The short answer

Yes — and it works well on the art this project has. `realesrgan-x4plus-anime`
turns the 125×220 Hysilens Q still into a clean 500×880 with **alpha intact**
(the naive path destroys transparency; see below). It is not a fix for a bad
matte, though, and it does not make a 360p photograph into 1080p truth.

## What it is for

Super-resolution pays off where the UI paints an image **larger than the file
can fill** — a full-bleed background on a 2× display, not a 140 px sprite.

| Asset | Source | Where it is shown | Verdict |
|---|---|---|---|
| the Eternal Page parchment | 1216×603 | full-bleed on a 1100×560 stage at 2× DPR = 2200 px | **under-resolved ~1.8×** — the one that matters |
| galgame backgrounds | 1600×900 | ≤1400 px wide | fine |
| sill sprites | 175–351 px tall | 140 px box | fine, no gain |
| PPG faces | 510² | ~34 px sticker | fine |

`python tools/upscale_art.py --plan` prints this measurement from the files.

## What it does not fix

**A matte.** Hysilens' 360p body upscales beautifully and is *still* inseparable:
96 % of that file is opaque, the blue stage is baked in, and the flood matte at 4×
punches through her costume rather than around it. Better pixels do not create an
edge that the source never had. She stays a portrait — that decision was made on
separability, not resolution, and SR does not change it.

## Two bugs in this build, and the workarounds

Both were found by measuring, and both are handled in the tool:

1. **`-s 2` crops instead of downsampling.** Asking the binary for 2× with an x4
   model returns a 4× render *cropped to the 2× rectangle*: the image shifts to
   the bottom-right and loses a quarter of itself. The tool always runs the model
   at its **native factor** and resamples down with Lanczos afterwards.
2. **Tiling scrambles sizes that are not multiples of the model's scale.** A
   1216×603 input came back as a collage of misplaced tiles (603 is not divisible
   by 4). The tool pads to a multiple of 16 by replicating edge pixels, then crops
   the result back to the true size.

If the GPU is busy with another model, large images fail loudly
(`vkQueueSubmit failed`): that is device memory, not the tool — use `--tile 256`
or wait. A tile of 2048 on a 1216 px image is a single tile and can exhaust the
GPU while the 27B voice model is loaded.

## Transparency

The binary is RGB-only: a cut-out sprite passed straight through comes back with
a **solid background painted into it**. The tool premultiplies RGB by alpha,
upscales the premultiplied image and the alpha mask separately, then
un-premultiplies — the only way to avoid a fringe of the discarded background.
The suite checks exactly this: a transparent square stays transparent at the
corners, opaque in the middle, at 2×.

## Usage

```powershell
# one-time model fetch (~43 MB, gitignored)
curl -L -o models/realesrgan/sr.zip https://gh-proxy.com/https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip
Expand-Archive models/realesrgan/sr.zip models/realesrgan

python tools/upscale_art.py --check          # binary, models, download hint
python tools/upscale_art.py --plan           # what the UI under-resolves
python tools/upscale_art.py --image <file> --scale 2
python tools/upscale_art.py                 # the PLAN list
```

Output is written **beside** the original as `name@2x.png` — masters are never
overwritten. `src/world/eternal_sill.py::hi_res_path()` looks for that sibling, so
the page picks an upscale up automatically once one exists; nothing else has to
change, and deleting the file returns the page to the original.

## Measured

| | before | after |
|---|---|---|
| Hysilens Q body | 125×220, 3.7 % transparent | 500×880, alpha preserved |
| parchment (planned) | 1216×603, 141 KB | 2432×1206 → re-encoded 2400 px, ~235 KB |

The parchment gain is nearly free in bytes: super-resolution smooths rather than
adds noise, so the 2× JPEG compresses better than the same bitrate at 1×.
