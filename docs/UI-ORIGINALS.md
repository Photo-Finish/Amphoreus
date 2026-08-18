# UI originals — do not lose these

The live Sanctuary UI (Visit / Walk the Land) has been rewritten in place.
The **previous settings still exist** in git and as frozen copies on disk.

Copilot-era Stage 1 files remain frozen under the project rule. This archive
is only for the land UI that Stage 2 replaced.

## Restore points (git)

| Tag | Commit | What it is |
|---|---|---|
| `ui-pre-pictorial` | `113d7c254c25507a25f6a2ffab8d30114283be91` | Last UI **before** full-bleed pictorial land. Inset region art, named Streamlit buttons / chips under the picture, Presence word list. On `origin/main`. |
| `ui-pictorial-v1` | `8a8aad193e1a4640330d8b80bd7e1ad88f7915c6` | First pictorial commit on GitHub: full-bleed art + SVG figures, still no painted films. On `origin/main`. |

Local tags (same SHAs): `git tag -l "ui-*"`

Stage 1 Copilot UI is the history **before** Stage 2 opened (`55d1c54`). Do not
rewrite those files without an explicit verbal OK.

## Frozen copies on disk

Exact files from `113d7c2`, copied verbatim:

`docs/ui-archive/pre-pictorial-113d7c2/`

- `ui_app.py`
- `ui_guide.py`
- `ui_scene_life.py`
- `ui_walk_land.py`
- `ui_weather.py`
- `2_Walk_the_Land.py` (from `src/pages/`)

These are **reference only**. The running app still loads `src/`.

## How to restore the pre-pictorial UI

From the repo root, restore only the land/Visit surfaces (does not rewind the
world engine):

```
git checkout ui-pre-pictorial -- src/ui_app.py src/ui_guide.py src/ui_scene_life.py src/ui_walk_land.py src/ui_weather.py src/pages/2_Walk_the_Land.py
```

Or copy the frozen files back over `src/` / `src/pages/`.

To look without changing the working tree:

```
git show ui-pre-pictorial:src/ui_walk_land.py
```
