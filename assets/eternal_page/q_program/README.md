# Special Program Q-version Heirs

Local catalog of **official** Honkai: Star Rail Version Special Program Q (chibi) stills.

Eternal Page **wires sit/swing cutouts** as circle bodies (`src/world/eternal_q.py`).
Guests, Mem, poster busts, and tiny Bilibili 3D frames stay research-only.

Do **not** overwrite `assets/eternal_page/cute/` Pom-Pom Gallery busts.

Repeatable extract: `python tools/cut_q_program.py`

## What this is

HSR Special Programs use two official Q looks:

1. **2D announcement key art** — published as stills (wiki `File:Version_3.x_Special_Program_Announcement.png`). Guests sit/pose full-body. Usually **one idle pose per guest**.
2. **3D talk-show mascots** — full-body SD models on a stage that walk/emote during the recording. **Video-only**; no official transparent sprite sheet found.

Pom-Pom Gallery stickers already in the repo are a third class: 510×510 **bust** emotes, not these bodies.

## Verified still URLs (HTTP 200, Wikia CDN)

Wiki File pages: `https://honkai-star-rail.fandom.com/wiki/File:Version_3.x_Special_Program_Announcement.png`

| Ver | CDN (hashed `/revision/latest`) |
| --- | --- |
| 3.0 | https://static.wikia.nocookie.net/houkai-star-rail/images/f/f9/Version_3.0_Special_Program_Announcement.png/revision/latest |
| 3.1 | https://static.wikia.nocookie.net/houkai-star-rail/images/0/05/Version_3.1_Special_Program_Announcement.png/revision/latest |
| 3.2 | https://static.wikia.nocookie.net/houkai-star-rail/images/4/40/Version_3.2_Special_Program_Announcement.png/revision/latest |
| 3.3 | https://static.wikia.nocookie.net/houkai-star-rail/images/8/80/Version_3.3_Special_Program_Announcement.png/revision/latest |
| 3.4 | https://static.wikia.nocookie.net/houkai-star-rail/images/8/81/Version_3.4_Special_Program_Announcement.png/revision/latest |
| 3.5 | https://static.wikia.nocookie.net/houkai-star-rail/images/e/e6/Version_3.5_Special_Program_Announcement.png/revision/latest |
| 3.6 | https://static.wikia.nocookie.net/houkai-star-rail/images/3/3a/Version_3.6_Special_Program_Announcement.png/revision/latest |
| 3.7 | https://static.wikia.nocookie.net/houkai-star-rail/images/b/b7/Version_3.7_Special_Program_Announcement.png/revision/latest |
| 3.8 | https://static.wikia.nocookie.net/houkai-star-rail/images/6/6f/Version_3.8_Special_Program_Announcement.png/revision/latest |

Wiki serves these as WebP; copies under `announcement/` were converted to PNG.

## Official recordings (do not download whole videos into git)

Played via the official **embed** (`player.bilibili.com/player.html?bvid=…&danmaku=0&high_quality=0`) at 360p without login. Account: 崩坏星穹铁道.

| Ver | Bilibili | Played this pass |
| --- | --- | --- |
| 3.3 | https://www.bilibili.com/video/BV1MB5KzQEYL/ | Yes — 2D cartoon + 3D stage |
| 3.4 | https://www.bilibili.com/video/BV1APNWziErE/ | Yes — cinematic then 3D stage |
| 3.5 | https://www.bilibili.com/video/BV1gHhAz9EpC/ | Yes — cinematic then 3D stage |
| 3.6 | https://www.bilibili.com/video/BV1ogHezFEGB/ | Listed on official search; not played this pass |
| 3.7 | https://www.bilibili.com/video/BV1E7sBzQEBY/ | Listed on official search; not played this pass |

3.0 / 3.1 / 3.2 / 3.8 official BVs were not on the first page of the official-title search (results were dominated by 4.x). Do not use fan reuploads.

YouTube (Honkai: Star Rail) remains blocked in this environment.

## Bilibili timestamps (embed captures under `frames/`)

### 3.3 BV1MB5KzQEYL

| File | t | What |
| --- | --- | --- |
| `bilibili_3.3_BV1MB5KzQEYL_t22.jpg` | 22s | 2D Q split: Hyacine (closed-eye happy) + Castorice (gentle) |
| `bilibili_3.3_BV1MB5KzQEYL_t28.jpg` | 28s | Hyacine open-eye + Castorice |
| `bilibili_3.3_BV1MB5KzQEYL_t36.jpg` | 36s | Hyacine open-eye + Castorice closed-eye |
| `bilibili_3.3_BV1MB5KzQEYL_t42.jpg` | 42s | 3D Cipher close-up (laugh) + 2D Hyacine/Castorice insets |
| `bilibili_3.3_BV1MB5KzQEYL_t480.jpg` | 480s / 8:00 | **3D stage**, no login wall: Castorice, Hyacine, Cipher, Owlbert |
| `bilibili_3.3_cipher_zagreus.jpg` | ~intro | Cipher on Hand of Zagreus (earlier capture) |
| `bilibili_3.3_t480_stage_behind_login.png` | 480s | Same stage behind a login modal (superseded by t480.jpg) |

### 3.4 BV1APNWziErE

| File | t | What |
| --- | --- | --- |
| `bilibili_3.4_BV1APNWziErE_t22.jpg` | 22s | Cinematic (not Q) |
| `bilibili_3.4_BV1APNWziErE_t30.jpg` | 30s | Cinematic (not Q) |
| `bilibili_3.4_BV1APNWziErE_t40.jpg` | 40s | Cinematic (not Q) |
| `bilibili_3.4_BV1APNWziErE_t480.jpg` | 480s | **3D stage**: witch-hat guest, Anaxa, Phainon, Owlbert |

### 3.5 BV1gHhAz9EpC

| File | t | What |
| --- | --- | --- |
| `bilibili_3.5_BV1gHhAz9EpC_t46.jpg` | 46s | Cinematic combat (not Q) |
| `bilibili_3.5_BV1gHhAz9EpC_t480.jpg` | 480s | **3D stage**: Screwllum, Hysilens, Cerydra, Owlbert |

## Crops (`crops/`) — recrop audit

Deleted `cyrene_v34_bust.png` (Mem was split). Replaced by `cyrene_v34_mem.png` with the **full framed Mem** (wings, square, gem, body).

| Crop | Fix |
| --- | --- |
| `cyrene_v34_mem.png` | Full Mem + frame (was divided) |
| `anaxa_v34_bust.png` | Full bust + blue square (was chin-clipped) |
| `himeko_v36_sit.png` | Full hair (was left-clipped) |
| `tribbie_v31_swing.png` | Full body + swing ropes/seat |
| `mydei_v31_sit.png` | Full body + pomegranate + wine |
| `aglaea_v31_sit.png` | Full sit on branch |
| `hyacine_v33_sit.png` | Full sit + Ica in lap |
| `castorice_v33_sit.png` | Full sit + hair/butterflies |
| `cipher_v33_sit.png` | Full sit + ears/tail |
| `hysilens_v35_sit.png` | Tight sit; Screwllum/Cerydra cropped out |
| `cerydra_v35_sit.png` | Tight sit + crown; Hysilens cropped out |
| `sunday_v36_sit.png` | Guest only — not a circle body |
| `dan_heng_pt_v36_sit.png` | Tight sit + chimera; Sunday/Himeko cropped out |
| `cyrene_v37_tv.png` | Tightened to pixel Cyrene on the TV |
| `cyrene_v38_sit.png` | 3.8 sofa Cyrene (Evernight/Aglaea cropped out) |
| `evernight_v38_sit.png` | 3.8 sofa Evernight (white hat; Cyrene cropped out) |
| `mini_companion_v31.png` | Little creature complete |
| `*_bili_t*.png` | Emotion/stage variants from official 360p frames |

Neighbor faces are cropped out of circle sits (tight boxes). Sit furniture that shares the outline (branch, sofa, ice ledge, stage) may remain so feet still read as planted. Guests (Himeko, Sunday, Owlbert, Screwllum, Mem) never become circle bodies.

Circle sits: `python tools/cut_q_program.py --sits` (samples backdrop *around* the box, then Lab+Canny+GrabCut).

## Cutout algorithm (`tools/cut_q_program.py` → `cutouts/`)

Not generative. Pixels come only from the source crop.

1. **Corner Lab distance** — sample the four corners, Otsu-threshold pixels unlike that backdrop.
2. **Canny silhouette** — thicken outlines, drop hairline stage rules, flood from corners; leftover interiors are the character.
3. **AND the two**, morphological close, keep the largest *central* blob.
4. **GrabCut refine** from that mask (corners forced background).
5. Fill holes that do not touch the border; anti-alias alpha via distance transform.

Magenta QA composites (RGB on #FF00FF, not for shipping) live in `_preview/`. The Read tool ignores PNG alpha, so those previews are the real quality check.

### Quality

**Clean enough to use**

- `cutouts/anaxa_v34_bust.png` — best; square + bust, dark poster BG gone
- `cutouts/cyrene_v34_mem.png` — Mem + frame isolated; leftover sunburst title art
- `cutouts/cyrene_v37_tv.png` — pixel Cyrene off the TV; small dark-screen bite on the left
- `cutouts/phainon_v34_bust.png` — bust + frame; a few poster tiles remain
- `cutouts/cyrene_v38_sit.png` — Cyrene body kept; sofa/poster fragments
- `cutouts/evernight_v38_sit.png` — Evernight + hat; sofa kept
- `cutouts/tribbie_v31_swing.png` — swing kept; Mydei cropped out
- `cutouts/mini_companion_v31.png` — creature kept; some foliage
- Bilibili 2D Hyacine/Castorice/Cipher emotion busts — usable at 360p (Hyacine often keeps her ornate frame)

**Partial (character complete, sit furniture still glued)**

- Mydei / Aglaea (branch + window fragments)
- 3.3 sitters (stage floor / bench)
- Hysilens / Cerydra (ice pane / ledge)
- Dan Heng PT (purple sofa + table; chimera kept)

### Still cannot isolate cleanly

- Group sofas and tree branches that share cel-shading with the Heirs (3.1 branch, 3.6 couch, 3.3 stage).
- Wisteria / painterly ice / TV bezel when they touch the outline.
- 3D talk-show frames at 360p — too small for a clean matte; keep as emotion reference, not sprites.
- 3.0 / 3.2 announcement stills have no Heir Q bodies (dolls / Owlbert only).
- No official transparent sprite sheet exists; 3D emotes (wave / angry / walk) exist only in the videos.

## Local layout

- `announcement/` — full official stills
- `crops/` — padded extracts (stage may remain)
- `cutouts/` — RGBA PNGs from `cut_q_program.py`
- `frames/` — official Bilibili embed grabs (BV + timestamp in the filename)
- `_preview/` — magenta composites for matte QA
