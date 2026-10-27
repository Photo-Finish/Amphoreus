# The As-I've-Written UI

**Date:** 2026-10-28
**Reference:** the in-game *As I've Written* (如我所书) book page in Honkai: Star Rail
**Module:** `src/ui_theme.py` · **Preview:** `python .cache/theme_preview.py`

---

## Why this reference, and what was actually seen

The style was chosen from **real screenshots, not memory**. Both candidate surfaces
were found and looked at before a line of CSS was written:

| Surface | What it is | Where it was seen |
|---|---|---|
| **As I've Written — book page** | cream two-page spread, gold frieze, Roman-numeral tabs, terracotta chevrons | miyoushe screenshot of 如我所书 → 翁法罗斯英雄纪 |
| **As I've Written — archive page** | deep navy tile grid of `.exe`/`.wav` entries, scanlines, radar ring | same source, 如我所书 → 神话之外 |

The archive page is also where **`δ-me13.exe`** appears as one of the tiles, so the
two styles the operator offered are two *pages of the same in-game book*. The book
page was chosen: it is the Greek-like surface, and the Sanctuary is already made of
parchment.

Reference URLs (fetched 2026-10-28):

- `https://upload-bbs.miyoushe.com/upload/2025/01/19/410523792/33708376550fa3b4566aa5aa7a02d832_4435563819675030086.jpg` — the book page
- `https://upload-bbs.miyoushe.com/upload/2025/07/02/345546365/5de6c3c853e266f158212cac8b92f9d2_7463363579564631334.jpg` — the archive page
- `https://hoyo.global/wp-content/uploads/2026/03/as-written-official-hsr.webp` — the official key art (book cover)

## What the screenshots actually show

Read off the book page, element by element:

- **Two facing pages of warm cream paper** (`#f4ecdc`–`#fbf6ea`), the fold visible down
  the middle, deckled edge and a soft drop shadow onto the world behind.
- **A gold egg-and-dart frieze** running along the top edge, with a **gold corner
  bracket** at the left whose corner carries a radiating arc.
- **Index tabs on the right edge** — cream tabs with Roman numerals (I, II) and a
  glyph tab, each with a gold hairline.
- **Terracotta chevrons** for page turns at the bottom left and right, gold-bordered;
  a matching **terracotta "return to index"** button at top centre.
- **Pagination dots** under the spread, one filled gold.
- **Text in a warm brown serif** (`#3b2c1e`), generous margins, small bird glyphs
  watermarked into the paper and a faint gold sun rosette at the top left.
- Behind it all, a **deep indigo world** (`#0d1631`–`#16224a`) with a low horizon,
  a scatter of stars and a soft sky-glow.
- One footnote line on the right page is **underlined in gold** — annotation, not
  emphasis.

## The design system

`src/ui_theme.py` carries the palette sampled from those screenshots, a Palatino-led
serif stack (no webfont download — the project stays offline), and the ornaments:
`frieze()`, `corner_bracket()`, `rulings()`. CSS-only, so nothing new is downloaded
and nothing is drawn from an unlicensed asset.

Applied to Streamlit the theme gives:

| Surface | Treatment |
|---|---|
| app background | indigo gradient with a low sky-glow and a scatter of stars |
| headings | gold display serif, letter-spaced, with a hairline rule beneath |
| tabs | the book's index tabs — parchment when selected, gold hairline |
| buttons | terracotta with a gold border and a light top edge |
| chat messages | parchment cards with warm-brown ink |
| inputs, expanders, metrics, alerts | parchment fields and gold-ruled frames |
| sidebar | the book's spine — near-black indigo with a gold rule |

Layout, structure and behaviour are untouched: only colour, type and ornament move.

## Verified

`.cache/theme_preview.py` renders a page that mirrors the DOM the CSS targets
(Streamlit's own selectors) and screenshots it with Chromium; the rendered result was
inspected by eye against the reference. `tools/run_all_tests.py` — 1855 checks —
stays green.

## Still to do

The custom HTML surfaces — the Eternal Page parchment, the galgame chrome, the walk
scene and the admin console — carry their own hard-coded colours and are restyled
next, using the same palette through `ui_theme.palette()`.

## Motion audit — is anything still floating?

Asked whether a "ghostly floating" animation remains. Measured rather than assumed:
two screenshots of the Eternal Page stage **3 seconds apart** differ in **0 pixels**
(out of 2,464,000) — at idle nothing on that page moves at all, so there is no
floating sprite there.

The loops that do exist, and what they animate:

| Animation | What it moves | Verdict |
|---|---|---|
| `amp-float` | the ♥ / `zzz` / ♪ marks above a Heir's head | intentional, small, only while a mark is set |
| `amp-twinkle`, `amp-fall`, `amp-steam`, `amp-spin` | the same emotion marks | intentional |
| `amp-sprite-roam` | a walking sprite, horizontal only | locomotion, not levitation — no vertical motion |
| `amp-grass-sway`, `amp-wheat-nod`, `amp-leaf-drift` | foliage and falling leaves | scenery |
| `ampPulse`, `galblink`, weather glow | a 7 px travel dot, a ▼ caret, a sun disc | UI chrome |

No rule animates `.buddy` or `.stage` itself. If a floating effect is still being
seen, the emotion-mark bob is the only vertical motion in the tree — it can be
switched off by removing `amp-float` from the `.mk-*::after` rules, and that is a
one-line change if it should go.
