# Art provenance — what past editors left, and how to know it is intact

**Date:** 2026-10-26
**Purpose:** keep the record of the art pipeline as it was handed over, and make
"has anything been changed?" a question with a mechanical answer.

Nothing in this file is a rule about how the art *should* be made. It is the
inventory: who wrote what, what it does, and its hash at the time of hand-over.

---

## The rule this file serves

Stage-1 (GitHub Copilot) artifacts are frozen — `.cursor/rules/copilot-legacy.mdc`.
The Stage-2 art pipeline below is not Copilot's, but it is **someone else's work**,
and the same courtesy applies: read it, run it, record it — do not quietly
re-derive it. New passes go in new files and new folders:

- first-pass cutouts → `assets/eternal_page/q_program/cutouts/` (**read-only now**)
- second-pass matte → `assets/eternal_page/q_program/cutouts_matte/` (new)
- new tools → `tools/matte_sill.py`, `src/world/eternal_sill.py` (new)

## The pipeline, as handed over

| Script | Lines | What it does | sha256 (first 16) |
|---|---|---|---|
| `tools/cut_q_program.py` | 522 | Splits the official special-program stills into per-Heir crops and mattes them (corner Lab distance → Canny silhouette → GrabCut → distance-transform alpha). Writes `crops/` and `cutouts/`. | `dd5b3b2df5c9bb10` |
| `tools/matte_q_faces.py` | 978 | Face-graph matte trial for the PPG busts; writes `q_program/_matte_v2/`. Not wired. | `46e4d7721ea03fd1` |
| `tools/fetch_eternal_page_art.py` | 194 | Fetches the Pom-Pom Gallery busts into `assets/eternal_page/cute/`. | `c7c6062d0aa29732` |
| `tools/fetch_cyrene_forms.py` | 212 | Fetches the official Demiurge / childhood / Mem stills into `assets/eternal_page/cyrene_forms/`. | `d6981930a878d0f4` |
| `tools/build_hsr_life_sprites.py` | 987 | Builds the Visit/Walk life sprites from wiki cuts. | `9e1612ef7c958944` |
| `tools/cut_hsr_life_sprites.py` | 128 | Cut pass for the life sprites. | `20685a3c218284ae` |
| `tools/build_place_env_sprites.py` | 418 | Builds place-family stalls, mosaic, pillars. | `9d6592b56f83bec3` |
| `tools/test_matte_q_faces.py` | 174 | Suite for the face-graph trial. | `188a4169b0135bf7` |
| `tools/test_eternal_page.py` | 682 | Suite for the page (391 checks). | `7fa61bdac5014c03` |

Added on 2026-10-26 (not part of the hand-over): `tools/matte_sill.py`,
`tools/test_eternal_sill.py`, `tools/audit_eternal_payload.py`,
`tools/audit_asset_duplicates.py`, `src/world/art_cache.py`,
`src/world/eternal_sill.py`.

## The catalogs

| Folder | Role | State |
|---|---|---|
| `assets/eternal_page/q_program/announcement/` | Official version announcement stills (9, 3.0–3.8) | untouched |
| `assets/eternal_page/q_program/crops/` | Padded per-Heir extracts | untouched |
| `assets/eternal_page/q_program/cutouts/` | First-pass RGBA cutouts (wired before 2026-10-26) | **byte-identical**, hash-checked |
| `assets/eternal_page/q_program/frames/` | Official Bilibili embed grabs | untouched |
| `assets/eternal_page/q_program/_preview/` | Magenta matte-QA composites | untouched |
| `assets/eternal_page/q_program/_matte_v2/` | Face-graph trial | untouched |
| `assets/eternal_page/cute/` | Pom-Pom Gallery busts (510×510) | untouched |
| `assets/eternal_page/cyrene_forms/` | Demiurge / childhood / Mem stills | untouched |

## How to check it yourself

```powershell
# 1. No existing art file differs or was deleted (the new folder shows as ??):
git status --porcelain -- assets
git diff --stat -- assets
git ls-files --deleted -- assets

# 2. Every first-pass cutout still hashes to what the matte read:
python tools\test_eternal_sill.py          # "none of the first-pass cutouts changed"

# 3. The record of those hashes, written when the matte was derived:
Get-Content assets\eternal_page\q_program\cutouts_matte\sources.json

# 4. If a file ever were changed, restore it from the published history:
git checkout -- assets/eternal_page/q_program/cutouts/
#    …or, on a different clone, straight from GitHub:
git fetch origin; git checkout origin/main -- assets/
```

Upstream: `github.com/Photo-Finish/Amphoreus`. Both 2026-10-26/27 rounds are
pushed, so every catalog above is one `git checkout` away.

## A mislabel found on 2026-10-27 — and what was done about it

`cutouts/anaxa_v34_sit.png` does **not** show Anaxa. It is a grey-haired,
gold-eyed figure — Caelus, the Trailblazer, standing in the 3.4 stage frame.
Anaxa is canonically mint green with a black gold-patterned eyepatch over his
left eye (`databank/chrysos-heirs/anaxa.md`), which the project's own
`assets/eternal_page/cute/anaxa/` stickers show correctly.

- **The mislabelled file stays where it is**, untouched: this record is the
  point. `cutouts_matte/sources.json` hashes it and carries the note.
- **The page no longer draws it.** `tools/matte_sill.py` has an `OVERRIDES`
  table; Anaxa's body is now the 3.4 announcement's own bust, matted, under the
  name `anaxa_v34_announcement_bust.png` (`src/world/eternal_sill.py: ALIAS`).
  Phainon got the same treatment for sharpness, not identity.
- `tools/test_eternal_sill.py` guards it: Anaxa's body must be the announcement
  bust and its hair must read mint green, so the Trailblazer cannot quietly come
  back.

If you ever need to re-audit identities, compare each body against its
`cute/<id>/` Pom-Pom Gallery sticker — that is how this one surfaced.

## Status of the inherited trials

- `q_program/_matte_v2/` (face-graph matte trial, `tools/matte_q_faces.py`) —
  **superseded, not deleted.** Its goal was a cleaner *face* sticker; the faces
  are already transparent official art, and the 2026-10-26 sill pass now handles
  the bodies. The files and their 129-check suite stay in place as the record;
  nothing on the page reads them. `tools/test_matte_q_faces.py` still passes.
- `cyrene_forms/` — still a catalog; `docs/CYRENE-CYCLE.md` now says which three
  stills the wired cycle actually uses.

## What changed on 2026-10-26, precisely

- **Added** `assets/eternal_page/q_program/cutouts_matte/` — 13 PNGs + `manifest.json`
  + `sources.json`. No existing art file was read-modified or replaced.
- **Added** `src/world/art_cache.py`, `src/world/eternal_sill.py`,
  `tools/matte_sill.py`, `tools/test_eternal_sill.py`,
  `tools/audit_eternal_payload.py`, `tools/audit_asset_duplicates.py`.
- **Edited** `src/ui_eternal_page.py` (sill body lookup, legend collapsed to a
  `Controls` toggle, contact shadow) and `README.md` / `docs/IMPLEMENTATION.md` /
  `docs/STAGE-2-VIVID.md` (append-only changelog notes).
- **Untouched**: every `src/characters/*.json` card, `databank/`, all art
  catalogs, and every script listed in the table above.
