# The sill's second matte

**Date:** 2026-10-26
**Module:** `src/world/eternal_sill.py` · **Tool:** `tools/matte_sill.py` ·
**Suite:** `tools/test_eternal_sill.py`

The Eternal Page stands thirteen Q sitters on a parchment. The first pass
(`tools/cut_q_program.py`, 2026-09) cut each one from its announcement still and
deliberately kept the sit furniture — a bench, an ice ledge, a sofa — so a figure
would read as planted. At the sill's fixed 140 px those leftovers read as a
**rectangular slab of the source photograph**, and every crop ended in a straight
edge. That was the "bad photoshopping".

This pass keeps the character and dissolves the set. `cutouts/` is **not
touched**: the new bodies go to a parallel folder, `cutouts_matte/`, and the
lookup prefers them, so the first pass stays the record and the fallback.

---

## What was tried

| Attempt | Result |
|---|---|
| Seed-colour flood from the crop border through flat, colour-similar pixels | Leaked through flat costume areas and punched holes in dresses |
| Border-colour stripping (the 360p frames with near-uniform backgrounds) | Ate into hair and outfits; unusable |
| Radial "hush" without a model | Softened the edge but left the whole photo as a glowing blob |
| **u2net** salient-object model (official ONNX, CPU) | Clean on crisp 2D announcement art; reads the *photo* on 360p frames and busy sofa stills |
| u2net with percentile normalisation | Marginally better, same failures |

The pattern is the same one the first pass recorded: where the source is a crisp
2D still the figure separates cleanly, and where the figure sits deep in a
painted set — or the whole frame is a 360p video grab — no automatic method gets
it apart without eating the character.

## What ships

Two policies, chosen per sprite by looking at the result:

| Policy | Heirs | What it does |
|---|---|---|
| `saliency` | aglaea, hyacine, castorice, cipher, mydei, cerydra | u2net mask ∩ the first pass, largest blob, feathered |
| `cut` | hysilens, evernight, cyrene, tribbie, dan-heng | first-pass silhouette, elliptical falloff, edges darkened toward the page |
| `override` | anaxa, phainon | the 3.4 announcement's own bust, cropped at full resolution and matted |

The two `override` bodies exist because the first pass had the wrong or the
weaker source (`OVERRIDES` in `tools/matte_sill.py`, `ALIAS` in
`src/world/eternal_sill.py`): **Anaxa's sit crop is the Trailblazer**, not Anaxa,
and Phainon's is a 360p stage grab of a character who has a crisp official bust.
Neither catalog file was touched — the corrected bodies sit beside them under
their own honest names.

Every body is then trimmed, padded by 6 %, and given one elliptical falloff so
**no border pixel is opaque** — the invariant the suite enforces. A `cut` body
also has its outer band darkened by distance: a photograph that fades to 40 %
alpha still carries its own bright background, which reads as a glow on a night
stage, so the leftover set merges into the backdrop instead.

Tuning lives in `POLICY` / `FEATHER` / `OVERRIDES` at the top of
`tools/matte_sill.py`; the manifest records each sprite's policy, its source, and
the percentage of first-pass opacity kept, so a future pass can see what was
decided and why.

## Where it still falls short

The five `cut` bodies keep a soft aura of their source set. They read as
figures-in-shadow beside the clean ones, not as equals. Fixing them properly
needs art that does not exist in the catalogs:

- **Hysilens** — the 3.5 2D overlay only, at 360p.
- **Tribbie, Evernight, Cyrene, Dan Heng** — crisp stills, but the figure sits in
  a painted set that shares its cel shading.

The honest options, none of them free: hand-trace those five, or commission/redraw
missing Q bodies. This pass takes neither — it removes the rectangles and keeps
the record.

*(Anaxa and Phainon left this list on 2026-10-27: their announcement busts are
official, crisp, and in Anaxa's case the only art of the right person.)*

## Regenerating

```powershell
# model (gitignored, 168 MB) — see docs/DOWNLOADS.md
curl -L -o models/u2net/u2net.onnx `
  https://gh-proxy.com/https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx

python tools/matte_sill.py              # all thirteen
python tools/matte_sill.py --only cyrene
python tools/matte_sill.py --check      # report, write nothing
python tools/test_eternal_sill.py       # 18 checks
python tools/audit_eternal_payload.py   # what the page actually ships
```

Removing `assets/eternal_page/q_program/cutouts_matte/` restores the previous
page exactly; nothing else depends on it.

**Charter:** the model runs locally on CPU, nothing leaves the machine, no art is
invented, and the first pass stays byte-identical — verified by hash in
`cutouts_matte/sources.json` and re-checked by the suite.

---

## 2026-10-27 — the last four, and one portrait

The five bodies that still carried a photo aura were split by cause, not by taste:

| Cause | Heirs | Outcome |
|---|---|---|
| Busy painted set, crisp source | Cyrene, Evernight, Dan Heng | **`flood`** — the set is border-connected and flat, the costume holes the flood punches are interior, so filling interior holes restores the figure and leaves the set gone |
| Her canonical seat | Tribbie | unchanged: the swing and flowers are her pose, not a matte failure |
| No crisp Q art anywhere | Hysilens | **`copy`** — the official Pom-Pom Gallery bust |

**Why Hysilens is a portrait.** Her Q body exists only inside the 3.5 special
programme video at 360p; the 3.5 announcement substitutes The Herta, and no
official still carries her Q form. Better sources were searched for — the
programme's own higher-quality stream (bilibili's API is unreachable from this
machine; `app.bilibili.com` answers but refuses the query), fan archives of the
preview stream (JS-rendered, no hotlinkable stills), and character-art pages
(splash art, not a chibi). Per the operator's standing call — *bust when the
resolution does not work out* — her body is the official sticker: crisp,
transparent, and canon.

Portraits are drawn 80 % tall (`.buddy[data-amp-bust]`) so a bust's head is not
half again a sitting Heir's, and Hysilens carries no corner-face sticker because
her body *is* that art.

**Result:** no faded photograph remains on the sill. Nine clean cutouts, three
portraits, one Heir with her swing.

Suites: `tools/test_eternal_sill.py` (30 checks — including that the flood bodies
removed their set rather than fading it, and that the three portraits are the
three `PORTRAIT_BODIES`), `tools/test_eternal_page.py` (395).
