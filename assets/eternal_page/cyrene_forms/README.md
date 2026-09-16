# Cyrene cycle forms — official art catalog

Research pack for a later 1-year Cyrene-slot surjection (Eternal Page / presence). **Not wired.** Cycle design is owned by another agent; this tree only stores verified official stills.

Does **not** write `assets/eternal_page/cute/`, `q_program/crops/`, `q_program/cutouts/`, or `tools/cut_q_program.py`.

Re-fetch wiki files: `python tools/fetch_cyrene_forms.py`

CDN pattern matches `tools/fetch_eternal_page_art.py` (Wikia hashed `/revision/latest`, WebP→PNG). Wiki File pages: `https://honkai-star-rail.fandom.com/wiki/File:<name>`

## Where files live

| Folder | Form |
| --- | --- |
| `assets/eternal_page/cyrene_forms/demiurge/` | Playable / later Cyrene (adult Q + splash/portrait catalog) |
| `assets/eternal_page/cyrene_forms/childhood/` | Tiny / Aedes Elysiae / PhiLia093 Q + head icon + splash ghosts |
| `assets/eternal_page/cyrene_forms/mem/` | Fairy memosprite (PPG 21 + 23, full-body art, program stills) |
| `assets/eternal_page/cyrene_forms/_source_announcement/` | Copies of special-program key art (3.0 / 3.4 / 3.7) |

**Best slot substitutes (cute / clear chibi, not only splash):**

- Demiurge: `demiurge/ppg24_01_heart.png` … `_04_orb.png`
- Childhood: `childhood/ppg24_05_wink.png` (only official cute Q found)
- Mem: `mem/npc_artwork.png` (full-body) plus PPG 21/23 stickers; pixel Q `mem/q_v37_pixel_mem_whole.png`

## Inventory

Wiki CDN URLs are `https://static.wikia.nocookie.net/houkai-star-rail/images/<hash0>/<hash2>/<FileName>/revision/latest` (HTTP 200, converted to PNG).

### 1. Cyrene (Demiurge) — playable / later

| File | Source | Full-body? | Pose / emotion | Slot? |
| --- | --- | --- | --- | --- |
| `demiurge/ppg24_01_heart.png` | `Sticker_PPG_24_Cyrene_01.png` | No (Q bust) | Eyes closed, smile, holding a heart | **Yes** — default cute |
| `demiurge/ppg24_02_look.png` | `Sticker_PPG_24_Cyrene_02.png` | No (Q bust) | Calm look, magenta eyes | **Yes** |
| `demiurge/ppg24_03_wink.png` | `Sticker_PPG_24_Cyrene_03.png` | No (Q bust) | Wink, pointing | **Yes** |
| `demiurge/ppg24_04_orb.png` | `Sticker_PPG_24_Cyrene_04.png` | No (Q bust) | Both hands on a glowing orb | **Yes** |
| `demiurge/icon.png` | `Character_Cyrene_Icon.png` | No (head) | Playable icon, rose + magenta eyes | Head only |
| `demiurge/portrait.png` | `Character_Cyrene_Portrait.png` | **Yes** | Floating full figure, white dress | Catalog / dramatic |
| `demiurge/splash_catalog.png` | `Character_Cyrene_Splash_Art.png` | **Yes** (adult center; ghosts of the other two forms) | Official drip splash | Catalog only |
| `demiurge/introduction.png` | `Character_Cyrene_Introduction.png` | Same composition as splash | HoYoLAB/Twitter introduction still | Catalog only |
| `demiurge/light_cone_artwork.png` | `Light_Cone_This_Love,_Forever_Artwork.png` | Partial (upper body) | Laughing, reaching forward | Catalog |
| `demiurge/light_cone_icon.png` | `Light_Cone_This_Love,_Forever.png` | No (card) | LC icon | Catalog |
| `demiurge/eidolon_1.png` … `_6.png` | `Character_Cyrene_Eidolon_1.png` … `_6.png` | No (close-ups) | Back of head / eye / book / laugh / rose collar / holding an orb | Catalog |

Wiki: [Cyrene/Media](https://honkai-star-rail.fandom.com/wiki/Cyrene/Media), [Pom-Pom Gallery No. 24](https://honkai-star-rail.fandom.com/wiki/Pom-Pom_Gallery/No._24). PPG 24 01–04 are the same files already in `cute/cyrene/01.png`–`04.png` (left untouched).

No official **cute full-body Q** of adult Cyrene was found. Special-program 3D SD models are video-only (see `q_program/README.md`). Version 3.7 announcement still is Mem-on-TV, not sitting adult Cyrene.

### 2. Cyrene (childhood / tiny)

| File | Source | Full-body? | Pose / emotion | Slot? |
| --- | --- | --- | --- | --- |
| `childhood/ppg24_05_wink.png` | `Sticker_PPG_24_Cyrene_05.png` | No (Q bust) | Wink, blue eye, navy dress, gold clip | **Yes** — only official cute Q |
| `childhood/npc_icon.png` | `NPC_Cyrene_Icon.png` | No (head) | Story NPC, blue eyes, gold necklace | Head only |
| `childhood/splash_ghost_whole.png` | Crop of splash (figures kept whole) | Approx. (two overlapping ghosts + book) | Translucent PhiLia093 pair | Catalog — not a clean cutout |
| `childhood/introduction_ghost_whole.png` | Crop of introduction (same pair, whole) | Approx. | Same | Catalog |

`NPC_Cyrene.png` / `NPC_Cyrene_Artwork.png` / `Young_Cyrene.png` / `Little_Cyrene.png` / `PhiLia093.png` are **404** on the wiki CDN. No standalone childhood full-body Q or overworld still is on the English wiki under those names.

PPG 24 **05** is packed with playable Cyrene but is clearly the tiny navy-dress form (blue eye), not Demiurge.

### 3. Mem — fairy / memosprite

Wiki emotion names for pack 21: Heart / Allow Me / Hugs ([Pom-Pom Gallery No. 21](https://honkai-star-rail.fandom.com/wiki/Pom-Pom_Gallery/No._21), [Mem/Media](https://honkai-star-rail.fandom.com/wiki/Mem/Media)). Pack 23 filenames exist on CDN (HTTP 200); emotions below are visual (wiki gallery dump did not include 23 labels).

| File | Source | Full-body? | Pose / emotion | Slot? |
| --- | --- | --- | --- | --- |
| `mem/ppg21_01_heart.png` | `Sticker_PPG_21_Mem_01.png` | Three-quarter chibi | Heart (star eyes, holding a heart) | **Yes** |
| `mem/ppg21_02_allow_me.png` | `Sticker_PPG_21_Mem_02.png` | Torso + dress | Allow Me (paw up, spark) | **Yes** |
| `mem/ppg21_03_hugs.png` | `Sticker_PPG_21_Mem_03.png` | Upper body, arms out | Hugs | **Yes** |
| `mem/ppg23_01_cry.png` | `Sticker_PPG_23_Mem_01.png` | Chibi bust | Crying | **Yes** |
| `mem/ppg23_02_swim.png` | `Sticker_PPG_23_Mem_02.png` | Chibi, kicking | Swimming / splash | **Yes** |
| `mem/ppg23_03_sleep.png` | `Sticker_PPG_23_Mem_03.png` | **Yes** (tail in frame) | Sleeping, Zzz, bubble | **Yes** — best PPG full fairy |
| `mem/npc_artwork.png` | `NPC_Mem_Artwork.png` | **Yes** | Official illustration, surprised, tail + paws | **Yes** — best full-body |
| `mem/npc.png` | `NPC_Mem.png` | **Yes** | In-game 3D, hovering, slight smile | **Yes** (photo, not Q) |
| `mem/npc_icon.png` | `NPC_Mem_Icon.png` | No (head) | Icon | Head only |
| `mem/profile_picture.png` | `Profile_Picture_Mem.png` | No (circle bust) | Wink, paw up | Avatar |
| `mem/q_v34_portrait_whole.png` | Crop of 3.4 program still | No (bust in a tile; Mem not split) | Eyes closed, smile, brooch | Q bust; source has no legs |
| `mem/q_v37_pixel_mem_whole.png` | Crop of 3.7 program still | **Yes** (sitting + tail) | Pixel Q, wink | **Yes** — program Q full-body |
| `mem/q_v37_tv_scene.png` | Wider 3.7 crop | Yes, on TV | Context (set + CRT) | Context |
| `mem/splash_ghost_whole.png` | Crop of splash (Mem fairy whole) | Yes, translucent | Ghost Mem beside adult hand | Catalog |
| `mem/introduction_ghost_whole.png` | Crop of introduction (Mem whole) | Yes, translucent | Same | Catalog |

3.4 announcement only **draws** Mem as a framed bust (wings + shoulders + brooch). The crop keeps that whole figure; it does not invent legs. The older `q_program` file `cyrene_v34_bust.png` (Mem split) was not copied here.

## What’s still missing

| Need | Status |
| --- | --- |
| Childhood **cute full-body** Q / standing chibi | Not on wiki CDN. No `NPC_Cyrene.png` artwork. Splash ghosts are translucent and paired. |
| Childhood in-game **full-body still** | Only `NPC_Cyrene_Icon.png` (head). |
| Adult Cyrene **cute full-body** Q | PPG 24 is busts; 3.7 key art is Mem-on-TV; 3D talk-show SD is video-only. Use `portrait.png` if a dramatic full-body is acceptable. |
| Isolated (non-ghost) childhood from splash | The two PhiLia093 ghosts overlap; a clean single cutout would split them. |
| Official 3D special-program sprite sheet | None found (same conclusion as `q_program/README.md`). |
| `cute/mem/` PPG folder | Intentionally **not** added, so existing `cute/cyrene/` PPG is untouched. |

Version **3.0** special-program still was copied and checked: no usable Cyrene/Mem Q (Hyacine’s Ica / set dressing only).

## Sources checked (public / official)

- Wikia CDN filename probe (PPG, Character_*, NPC_*, splash, introduction, eidolons, light cone)
- Wiki File/Media pages for Cyrene, Mem, Pom-Pom Gallery 21 / 24
- Local `q_program/announcement/` 3.0, 3.4, 3.7 (copies + crops only)
- Biligame API blocked (HTTP 567) from this machine; not used
- No unpaid package datamine; no overwrite of the other agent’s Q-program recrops
