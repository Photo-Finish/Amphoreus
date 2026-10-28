# Changelog

> The working record of the Sanctuary — one entry per day of work, oldest first,
> from the second stage onward.
>
> **What is not here.** The stage openings, closings and their signatures stay in
> [`README.md`](README.md), and so does the **GitHub Copilot Stage-1 changelog**
> (`2026-08-07` → `2026-08-16`), which is frozen and must not be moved. That
> README is the phase record and the signature book; this file is the work.

## Stage 2 — vivid society & natural world (2026-08-18 →)

### 2026-08-18
- **OPLoRA training stack** (`773aa2a`) — isolated `.venv-oplora` (PyTorch cu128 for
  Blackwell), `tools/oplora/` scaffold (OPLoRA wrapper, QLoRA SFT, config tuned for
  RTX 5070 Laptop **8 GB**), and shaped SFT datasets copied from the databank into
  `work_copies/` (originals never edited). Charter: adapters are **voice stability
  only**; RAG remains the scripture path.
- **13-Heir SFT roster complete** (`0d7a935`) — fixed 4-bit SVD materialization,
  TRL `warmup_steps`, and sequential `train_all_heirs.py`; reshaped datasets so
  **Evernight** sits with the sanctuary cards. Adapters land under
  `tools/oplora/outputs/heirs/<heir>/adapter/` (**gitignored** weights; capability
  documented here). Card id `dan-heng-permansor-terrae` → adapter folder `dan_heng`.
- **OPLoRA infer server + voice path** (`58d2bf0`) — `tools/oplora/infer_server.py`
  serves Qwen2.5-7B-Instruct (4-bit) + per-Heir LoRA over localhost HTTP so the
  Streamlit app venv never imports torch/peft; `src/core/voice_path.py` persists
  `rag` | `oplora` under `world_runtime/voice_path.json`; `verify_health.py` checks
  adapter tensors and a short Phainon generation.
- **Control Panel page + RAG/OPLoRA switch** (`9fbcb90`) — dedicated Streamlit page
  `src/pages/1_Control_Panel.py` (sidebar) plus the existing Control Panel tab;
  Control Panel gains an exclusive **Voice path** switch (RAG = Ollama + Chroma;
  OPLoRA = infer server + adapters). Visit chat honors the path: RAG retrieves
  scripture; OPLoRA skips Chroma and calls the infer client. Sidebar shows the
  active path. On 8 GB VRAM the two heavy models must not load together — switching
  starts/stops the OPLoRA server and may `ollama stop gemma3:27b`.
- **Live avenue tests** (`9fbcb90`) — RAG: Ollama `gemma3:27b` ready; Phainon reply on Aedes
  Elysiae grounded with Chroma hits (`11332` docs). OPLoRA: infer server on
  `:8765` with Phainon adapter answered a short battle-cry turn. Sequence one
  path at a time on 8 GB VRAM (`ollama stop` before loading the 7B adapter path).
- **Training refine** (`9fbcb90`) — working 13 adapters verified earlier; **no overwrite** this
  round (disk/VRAM tight). Added `tools/oplora/REFINE.md` and
  `config_refine_small.yaml` (2-epoch plan for thin sets like Evernight) targeting
  `adapter_v2/` only after verify. Infer server now prefers `local_files_only`
  against `D:\hf-cache` to avoid HF-mirror TLS stalls on load.
- **Lived world entities** (`src/world/lived_entities.py`) — Amphoreus-native physical
  stage (Dawn Device, Thief Star, sky, wind, earth, harvest, dromases, hearth, house,
  city, cloth, road, gates, market, coin, Grove, sea, harbor, fields, workshop,
  ship, forge, scroll, letter, hours, teaching hall, healer's house, shrine).
  Each has a **mechanism**. Excluded: famine, plague, war, storm-as-entity,
  and **grave/burial** (the sanctuary assumes people live on; no system here
  desperately needs a death, so that mechanism was removed). Status is derived,
  not a second weather roll: Light Calendar hour/month + Keeper sky + where the
  body stands. Night withdraws the Dawn Device even if the day's weather was blazing;
  a Grove Visit cannot grow a sea; Cultivation sows and Reaping reaps; the road is
  not a house; a tide surge thins the market without inventing famine. Control Panel
  and Admin show the ledger; Visit injects only what is here.
- **Lived day mechanisms + residents** — all 17 day-verbs mutate `world.vivid["lived"]`
  on the world-engine tick; ~110 street residents plus Copilot's untouched `NPCS`.
  Visit shows a stage paragraph plus 2–4 people here; Gazette: “This Hour in the
  World” / “Seen in the Streets.” Catalog: `docs/LIVED-WORLD.md`. Suites:
  `tools/test_lived_mechanisms.py` (63), `tools/test_resident_npcs.py` (33),
  `tools/test_lived_entities.py` (61), vivid 44/44.
- **Sanctuary Light Calendar** (`src/world/sanctuary_clock.py`) — every time-flow
  speed uses the reform (13×28 months, Membrance, Scarlet Day after Fortune in leap
  years, Dies Astrorum). **1x** follows GMT+8; **2x–60x** keep the persisted sim
  timestamp (live store: Year 4932, Month of Strife…) and never get overwritten by
  the 1x overlay. Setting: `databank/world/sanctuary-calendar.md`. Kephale's
  `calendar.md` untouched. Suite: `tools/test_sanctuary_calendar.py`.

### 2026-08-19
- **UI originals (kept)** — the last land UI before the full-bleed pictorial
  rewrite is frozen at git tag `ui-pre-pictorial` (`113d7c2`) and as copies in
  `docs/ui-archive/pre-pictorial-113d7c2/`. How to restore:
  `docs/UI-ORIGINALS.md`.
- **Pictorial land** (`8a8aad1`, `9268614`) — Visit and Walk the Land read as a
  place, not a button grid: full-bleed area art, clickable 2D life on the
  pavement, painted walk cycles, outdoor beings you can actually touch.
  Fixtures stay still; roamers walk the ground line. Classic keeps its small
  weather window. Painted life can be hidden.

### 2026-08-20
- **Pictorial overlay** (`4e910ce`, `src/ui_weather.py`) — opaque glass stripes
  are gone so land figures stay visible; copy keeps a stronger text halo.
  Travel/gift selectbox closed-controls are no longer a black bar (Streamlit
  1.61 React Aria group). File-uploader Browse buttons are gold/standout;
  Give and Set-out stay hairline.
- **Land click notices** (`18cee39`) — right-anchored lighter panel inside the
  land iframe (no page reload).
- **Sprite scale and roam films** (`8bbd051`, `cf81acd`) — per-kind stage
  height (chimera a mascot you could pick up, resident human-scale, dromas a
  ridden earth-beast). Chimera and dromas use true side-walk films from
  distinct poses, not a bobbed still; roamers cross and leave the view.
- **Pet and trade caravan** (`985964e`) — the visitor can pet chimera, hearth
  cat, and dromas (reaction films); sometimes a dromas-and-people trade
  caravan crosses the road (`src/world/ecosystem.py`).
- **Profession NPC outfits** (`src/world/resident_npcs.py`) — 11 special
  stems from the real `_CITY_ROLES` (guard, merchant, scholar, smith,
  weaver, shrine, healer, harbor, field, dromas-handler, baker); civilian
  roles keep the existing chiton. Full set per outfit: still + walk f1–f4
  + packed film (`tools/build_hsr_life_sprites.py outfits`). Runtime:
  `visual` / `_sprite_asset_key` (`src/world/ecosystem.py`,
  `src/ui_scene_life.py`). Honest: recolor/composite of the civilian
  figure, not new painted profession art.
- **Co-presence group chat** (`src/world/group_chat.py`, `src/ui_group_chat.py`,
  `tools/test_group_chat.py`; Visit wiring in `src/ui_app.py`) — when two or
  more Heirs share the selected Heir's place, Visit offers Individual vs
  Group chat. The operator invites by button; Heirs accept or decline in
  character, and a gathering starts if at least one accepts. Guests may see
  Heirs together but cannot invite. The gathering ends on leaving Visit an
  Heir (tab or page), not on closing localhost:8501.

### 2026-08-22
- **Society continuity deepens** (`src/world/society_life.py`) — shared gatherings
  stick into solo Visit as remembered hours; richer walk-in scenes (mid-letter /
  mid-Heir-talk / rumor); bond-weather cues when canon pairs share a place;
  Walk→Visit eco notices persist on `world.vivid`; long-leave return beats (≥5
  days); co-located secondhand teaching echoes (Earth topics skipped). Doc:
  `docs/COLLECTIVE-MEMORY.md`. Suite: `tools/test_society_life.py` (49) +
  `tools/test_ensemble_injectors.py` (22).
- **Multi-Heir Galgame** (`src/ui_galgame_group.py`) — when a Visit gathering is
  active, the Galgame tab shows multiple sprites and the current speaker’s line;
  classic 1:1 Galgame unchanged.
- **Named street memory** (`src/world/resident_memory.py`) — recurring residents
  recognize the visitor across meets; wired through `vivid_stage2` greet/talk.
  Suite: 18.
- **Canon companions on the land** — Pollux (Castorice's dragon companion, not
  the Workshop dromas); Membrance-month **maze fairies** at Aedes; Mountain
  Dwellers at **Okhema** (home) with thin Kremnos forge echo — never Aidonia
  (`ecosystem.py`, `databank/world/fauna.md`). Suite: `tools/test_eco_companions.py`.
- **Daybook Chronicle view** (`src/world/daybook.py`) — Gazette opens with a
  literary “Today in Amphoreus” from tick facts (not a raw log). Suite: 14.
- **Lived Map hour** — Map place popups carry a this-hour vignette from
  mechanisms / eco.
- **World engine default living** — `launch_sanctuary.cmd` starts the engine if
  idle; Visit UI also tries once per session.
- **Stable public address** — `status_guard.py` reads optional
  `world_runtime/named_tunnel.json` for Cloudflare named tunnels (no
  trycloudflare churn); github.io front door still rewritten. Guide updated.
- **Voice pillar** — speech-sanitize ensemble cases (62); OPLoRA 13 adapters
  still healthy (voice-stability only); live style probe deferred (Ollama model
  list empty this session). Castorice remains the open gate from the last report.
- **Desktop window shell** (`AmphoreusSanctuary.exe`) — same Streamlit UI in a
  native window via pywebview (Edge WebView2). The exe ships at **repo root**
  for double-click; browser tab launcher `launch_sanctuary.cmd` is unchanged.
  Build: `tools/build_desktop_exe.ps1`; also `launch_sanctuary_desktop.cmd` /
  `tools/desktop_sanctuary.py`.

### 2026-08-22 (evening) — invites, land, guest Walk
- **Heir-initiated gatherings** — co-located Heirs may propose sitting with you;
  operators accept/decline; guests look-only (`group_chat.propose_from_heir`).
- **Letter mini-scene** — mid-letter choices: read together / wait / leave
  (`society_life.letter_scene_choices`).
- **Bond weather** — Castorice–Hyacine (Cassie); Cipher locked-door air; Dan Heng
  Earth underfoot. **No unofficial festivals** — seasonal eco uses official
  Light Calendar months only.
- **Resident errands** — recurring street people, date-advancing Amphoreus work
  (`resident_errands.py`).
- **Land** — `dromas_walk_v2` → live `dromas_film.png`; **Little Ica** with
  Hyacine; Cultivation/Reaping/Joy/Weaving/Strife/Membrance density; tide-edge
  thins EDGE cities + `blacktide` Walk sky.
- **Walk → Map pin**, **guest Walk** (notice OK; care-chat operator-only),
  **absence Visit vignette**, **Chronicle daybook spine**.

### 2026-08-24 — visitor emotion
- **Visitor tone for Heirs** (`src/core/visitor_emotion.py`) — each Visit /
  group line can be read for emotion (DistilRoBERTa
  `j-hartmann/emotion-english-distilroberta-base` on CPU when installed;
  lexicon fallback otherwise). Heirs get an Amphoreus-native cue
  (“How the visitor seems”) — colour, not diagnosis; no BERT/Earth jargon
  (knowledge wall). Default **ON**; Control Panel + `AMP_VISITOR_EMOTION`.
  Install: `requirements-emotion.txt` +
  `python tools/download_visitor_emotion_model.py`. Suite:
  `tools/test_visitor_emotion.py`.

### 2026-08-23 — pictorial land polish
- **Launcher reuse** (`15171e4`) — `launch_sanctuary.cmd` waits for
  `http://127.0.0.1:8501/_stcore/health` and reuses a healthy Streamlit instead
  of spawning a second one; only stops a UI this launcher started.
- **Walk life layer** (`de769ff`) — scroll passes through the life iframe to
  the main column; page-layer sprites share one ground sill (viewport bottom);
  place-family HSR stall art; trade caravans are additive (solo dromas /
  residents / chimeras kept); stall density reserved so civic fixtures stay
  visible. Suites: `tools/test_ecosystem.py`, `tools/test_walk_map_handoff.py`,
  `tools/_audit_life_scroll.py`.
- **Scroll, ground, chimera art** (`9b98ce6`) — wheel/touch still scroll when
  Life is on; NPC/roamer feet on the page sill (no cell-scaled floor nudge);
  still sprites spaced; Little Chimera films rebuilt from wiki cuts; mosaic /
  pillar env sprites refreshed.
- **Backdrop, floor, horizon, civic lanes** (`5fe549b`) — Heir galgame photo
  mounts inside `stAppViewContainer` at z-index 0 under the life iframe (25),
  so Aglaea’s backdrop no longer buries gate/fountain/dromas; page layer hides
  painted floor ellipses and ambient ground bands; walk films align feet to
  the sill (`ground-sill`, `bottom: 0px`); Okhema civic lanes separate gate
  (28%), fountain (58%), mosaic (76%). Detail: `docs/STAGE-2-VIVID.md`.

### 2026-09-16
- **1x period ticks** — still follow GMT+8. Each Light-Calendar period
  (~4.8 real hours) gets one world-machine tick: Entry and Curtain-Fall stay
  rest; Lucid, Action, and Parting live. The overlay clock is not advanced.
- **World machine without a conversation model** — the engine keeps running
  (Keeper fallback, hearths, streets, eco). Heir decide/talk waits for a
  tagged Ollama model, OPLoRA, or an Online API key.
- **Teaching echo and land chrome** — visitor-taught names may travel
  Heir-to-Heir. Keeper fallback news/errands stay in their Titan-month.
  Resting sprites stand still. Journey chrome follows the bond.
- **Online API voice path** (`src/core/online_llm.py`, Control Panel) — a
  third avenue beside RAG and OPLoRA. Paste an OpenAI-compatible key
  (OpenAI, OpenRouter, DeepSeek, Groq, or a custom base URL); Visit chat,
  group talk, and Heir decide/react use the remote model so conversation
  does not load a local GPU. The key lives only in `secrets/online_llm.json`
  (gitignored; never `world_state.json`). Placeholder:
  `online_llm.example.json`. The world machine stays local. Suite:
  `tools/test_online_llm.py`.
- **Land z-order and scroll** — people, dromas, gates, and other figures paint
  above Visit dialogue and page wording. The land click-popup sits above
  everything else (`#amp-land-notice-host`). The life iframe no longer steals
  wheel/touch; native scroll is used. Audit: `tools/_audit_life_scroll.py`.
- **An Eternal Page** — Beyond Time as its own tab/page, distinct from Visit.
  Official cute PPG stickers stand on the parchment like desktop companions.
  Click one, several, or all thirteen, then whisper; answers rise as speech
  bubbles (not Visit chatboxes). Speakers use the same `manager.chat` history
  as Visit in Journey or Aftermath. No weather, no street life. Suite:
  `tools/test_eternal_page.py`.
- **Eternal Page faces** — companions switch among official PPG poses by
  feeling. Detection reads recent conversation (Visit/Eternal history plus
  the last bubble) and sanctuary ongoings (mood, black-tide weight, travel,
  gifts, open grievance). Missing poses fall back; Phainon’s single sticker
  still shows. Suite: `tools/test_eternal_page.py`.
- **Eternal Page companions** — clicks were swallowed by Streamlit’s sandboxed
  iframe (`parent.location` blocked; Visit pictorial CSS also turns off
  pointer events). Hits are now tested on the parent page. Desktop-pet
  gestures that fit: click to stand near, double-click for one, drag to
  rearrange, right-click to pet (mood only — never authored speech). Name
  chips remain if a picture does not answer. No chase/feed/throw/weather.
- **Eternal Page emotion VFX and gestures** — each companion carries CSS/SVG-free
  marks (flush, vein, steam, sweat, tear, sparkle, heart, ?, !, dizzy, zzz,
  shock, flower, ice, veil, note, shy hands, glow) from `data-amp-emotion`
  and the last touch. Keyboard+mouse combos pick a gesture (Shift+click pat,
  Ctrl+click poke, Alt+click tease, Shift+right-click hands, hover keys P/H/F/W/C/G/B/T/K,
  and a larger right-click menu). Reactions are pose + VFX + living-world mood
  with a factual reason — never canned Heir speech. Optional “Ask how that felt”
  uses `manager.chat`. Suite: `tools/test_eternal_page.py`.
- **Cyrene year cycle** (unwired) — three Light-Calendar blocks map pictures {childhood, demiurge, mem}; whisper always `"cyrene"`. Spec: `docs/CYRENE-CYCLE.md`. Suite: `tools/test_cyrene_cycle.py`.
- **Cyrene-form stills** — official PPG / NPC art for Demiurge, childhood, and Mem in `assets/eternal_page/cyrene_forms/` (cycle not hooked to the page).
- **Star-swirl Eternal Page** — parchment uses Vortex of Genesis (`bg-vortex-of-genesis.jpg`), not the Exotale garden plaza.
- **Q-program catalog** — official special-program announcement stills and crops in `assets/eternal_page/q_program/`. Guest Bilibili frames stay research-only (360p); idle companions use the posters.
- **No idle bob** — Eternal Page companions and galgame portraits stand still. Visit/Walk roam, weather, and emotion marks stay.
- **Visit painted sky and land** — the Dawn Device / sun is the painted emblem, not a CSS disk. Remaining geometric land glyphs (grass, wheat, wind, moon, companions, …) are painted PNGs in `assets/life_sprites/`. Suite: `tools/test_ecosystem.py`.
- **World-machine CPU ticks and boot** — ticks no longer hang on a GPU Keeper load (timeouts + CPU fallback). Launchers no longer kill Streamlit when the cmd window closes; the desktop shortcut targets `launch_sanctuary.cmd`. Suite: `tools/test_world_machine.py`.
- **Mission memories** — canon mission dialogue split into per-Heir and collective files under `databank/memories/` without editing original scripts. Gate: `tools/test_mission_memories.py`.

### 2026-09-29 — Eternal Page Phase 2a (presence), Stage 2 continues
- **Q sit as the figure, PPG as the corner emotion** — all thirteen circle Heirs use official Special Program sit/swing bodies; Pom-Pom Gallery stickers sit upper-right when someone is near, talking, or gesturing (idle hides the face). Layout is two staggered mid-stage rows (140px slots) so sprites stay in frame and do not stack. Suite: `tools/test_eternal_page.py`.
- **Identity** — Cyrene is the 3.8 third sofa sitter (cream hair), not Robin. Hysilens is the 3.5 2D Q overlay, not The Herta. Robin / The Herta / Himeko / Sunday stay guests. Phainon and Anaxa had no 2D announcement sit; their bodies are tight one-Heir crops from the official 3.4 360p stage overlay (last-resort, same class as Hysilens).
- **Face-graph matte (trial only)** — `tools/matte_q_faces.py` writes `assets/eternal_page/q_program/_matte_v2/` (Ica and other close ornaments kept). Live `cutouts/` are unchanged; Eternal Page is not wired to the trial. Suite: `tools/test_matte_q_faces.py`.
- **Still open in Stage 2 / later Eternal work** — cache/WebP/dedupe, Cyrene year cycle (spec only), wiring or refining the matte over live sits, glued sofas on some trial mattes, voice-fidelity pillar, vivid land and society already on the north star.

### 2026-10-26
- **The map recut to the trailer's six poleis** (`c3d6f3e`) — `LOCATION_POS` and
  everything that hangs off it (the nine Dawn-era echoes, the Nether beneath
  Styxia, the River of Souls path, the cloud banks, the veil labels) now follow
  the Ancient Hymn trailer's labelled layout read off the frame at 720p: Okhema
  north-centre on her lake plateau, Janusopolis west of her, Castrum Kremnos
  south-west, the Grove of Epiphany south-centre, Styxia east on the turquoise
  bay, Aidonia far north-east in the snow. `databank/world/map.md`,
  `geography.md` and `time-forms.md` carry the corrected bearings. Travel
  periods and the route graph are untouched — positions are display geometry,
  not costs. Suites: `tools/smoke_test_world.py`,
  `tools/test_walk_map_handoff.py`.
- **The Eternal Page's pixels travel lighter** — the stage inlined 4.4 MB of PNG
  as 6.2 MB of markup on *every* rerun, so a click or a whisper re-encoded the
  whole circle. `src/world/art_cache.py` encodes each sprite once to WebP, capped
  at twice its CSS box (280 px body, 160 px face), keeps it in memory, and reuses
  it from the gitignored `world_runtime/_art_cache/` after a restart. Stage HTML
  **6 213 → 735 KB**; warm art build 0.037 → 0.009 s. PNG masters are untouched;
  `AMP_ART_CACHE=off` restores plain PNG and `AMP_ART_QUALITY=lossless` is
  bit-exact. Suites: `tools/test_art_cache.py` (51 checks),
  `tools/test_eternal_page.py` (391); measure any time with
  `tools/audit_eternal_payload.py`.
- **Art duplicate audit** — `tools/audit_asset_duplicates.py` hashes the 714
  images under `assets/`: **54 duplicate groups, 18.4 MB (10.6%) reclaimable** —
  mostly special-program announcement stills stored twice and the dromas walk
  films. Read-only by design; nothing was deleted, because that tree is the
  master copy.
- **Still open** — the Cyrene year cycle (its whisper half needs a register hint
  carried through `manager.chat`, its picture half has no full-body childhood
  art), the face-graph matte over the live sits, Eternal Page catalog hygiene,
  and the voice-fidelity pillar.
- **The sill is matted** — the thirteen Q sitters no longer stand inside
  rectangular slabs of their source photographs. A second pass
  (`tools/matte_sill.py`, CPU u2net) writes cleaned bodies to
  `assets/eternal_page/q_program/cutouts_matte/`: six separate cleanly by
  saliency, seven keep the first pass's silhouette with a feathered, darkened
  edge, and **every** body has see-through borders so no straight crop edge can
  reach the page. `src/world/eternal_sill.py` prefers them; the first-pass
  `cutouts/` are untouched and still the fallback, with their hashes recorded in
  `cutouts_matte/sources.json`. The page also gains a contact shadow (the bodies
  no longer bring their bench), and the sixteen-line control legend — which sat
  over the artwork — collapses into a `Controls` toggle. Honest limit: the seven
  feather-edged bodies keep a soft aura, because Anaxa, Phainon and Hysilens only
  exist as 360p stage grabs. Suites: `tools/test_eternal_sill.py` (18),
  `tools/test_eternal_page.py` (391). Detail: `docs/ETERNAL-SILL.md`.
- **The art pipeline is recorded, not rewritten** — `docs/ART-PROVENANCE.md`
  lists every script and catalog this project inherited, with hashes, plus the
  commands that prove nothing in `assets/` moved. The short version after
  2026-10-26's work: `git status -- assets` reports only the one new
  `cutouts_matte/` folder, and no existing art file is modified or deleted.

### 2026-10-27
- **Anaxa was not Anaxa** — the sill's `anaxa_v34_sit.png` is a grey-haired,
  gold-eyed figure: the **Trailblazer**, standing in the 3.4 stage frame, not
  Anaxa, who is canonically mint green with a black gold-patterned eyepatch
  (`databank/chrysos-heirs/anaxa.md`, and the project's own `cute/anaxa/`
  stickers agree). The mislabelled cutout is kept untouched as the record; the
  page now draws the 3.4 announcement's own bust, matted and named honestly
  (`anaxa_v34_announcement_bust.png`). Phainon takes the same sharper treatment.
  `tools/test_eternal_sill.py` will not let the Trailblazer come back: it asserts
  Anaxa's body is that bust and that his hair reads mint green.
- **Cyrene's year cycle is wired** — `src/world/cyrene_face.py` binds her three
  Light-Calendar faces to official stills and turns `talk_persona` into one
  register paragraph, carried by the new `manager.chat(extra_system=...)`. Her
  **picture** follows the calendar; her **speaker** does not — the whisper still
  addresses the `cyrene` card, Mem is never given a card or a speaker id, and the
  hint says only which of her own voices to use. Suites:
  `tools/test_cyrene_face.py` (24), `tools/test_eternal_page.py` (395).
- **The page is checked in a real browser** — `tools/shoot_eternal_stage.py`
  renders the stage markup to PNG (the Read tool ignores alpha, so a composite is
  the only honest look at the art), and `tools/validate_live_page.py` drives the
  *running* app: signs in, opens the tab, finds the component iframe, and counts
  what the browser actually received. Verified live — 13 companions, 13 names,
  inlined WebP bodies, no console errors, with the voice ready and 11 332 canon
  documents indexed on the RAG path.
- **Housekeeping** — the four dead Copilot-era `tools/_*_8501.py` probes moved to
  the gitignored `.cache/legacy_scratch/`; the `_matte_v2` face-graph trial is
  recorded as **superseded, not deleted** (its files and 129-check suite stay;
  nothing on the page reads it). `docs/ART-PROVENANCE.md` carries both the
  correction and the trial's status.

### 2026-10-27 — the phone
- **An Android shell** (`android/`) — a ~29 KB signed APK that loads the real
  network UI, so every tab and every administrator command is there unchanged:
  Visit, Walk the Land, the Gazette, the Map, the Galgame view, An Eternal Page,
  the Admin Console and the Control Panel. It adds only what a phone needs — a
  remembered server address, in-app back, a file picker for the senses, the
  microphone for speech, and a gear for reload/change-server. No Gradle, no
  AndroidX: `aapt2 → javac → d8 → zipalign → apksigner`.
  `tools/serve_for_phone.py` binds the UI to the LAN and prints the address to
  type. Build: `pwsh -File android/build_apk.ps1`; detail: `android/README.md`.
  Verified by driving the **LAN address** (not localhost) with Chromium —
  10 checks, including that the Admin Console and Control Panel open in the same
  session. Not yet run on a physical handset.

### 2026-10-27 — the last five bodies, and Hysilens
- **Three sets removed properly** — Cyrene, Evernight and Dan Heng no longer wear
  a faded photograph: a border flood removes the flat, border-connected set and
  interior hole-filling restores the costume it punched through. No faded photo
  remains on the sill: nine clean cutouts, three portraits, and Tribbie keeping
  her swing (that is her pose, not a matte failure).
- **Hysilens is a portrait** — her Q body exists only in the 3.5 programme video
  at 360p; the 3.5 announcement substitutes The Herta and no official still
  carries it. Higher-quality streams and fan archives were searched for and none
  are reachable from this machine, so per the standing call she uses the official
  Pom-Pom Gallery bust. Portraits now draw 80 % tall so a bust's head matches the
  sitters'. Suites: `tools/test_eternal_sill.py` (30),
  `tools/test_eternal_page.py` (395). Detail: `docs/ETERNAL-SILL.md`.

### 2026-10-27 — art and music taste, made functional
- **A real taste model** (`src/core/aesthetic.py`) — eight universal axes (order,
  ornament, restraint, motion, warmth, light, age, craft), a stance for each of
  the thirteen, and per-Heir notes on what they notice first, what earns approval
  and scorn, what they will not praise, and their own vocabulary.
- **The prompt asks for a reading, not applause** — name what is actually there,
  weigh it on two of the Heir's leanings, commit to one verdict from a finite set
  (including *it leaves me cold* and *it offends me*), name one thing they would
  change, five sentences, banned stock phrases. Vision and music both use it; the
  old invitations stay in the file as the record, and `AMP_AESTHETIC_TASTE=0`
  restores them exactly. Suite: `tools/test_aesthetic.py` (31 checks).
  Design and the failure it replaces: `docs/AESTHETIC-TASTE.md`.

### 2026-10-27 — super-resolution for the low-res art
- **`tools/upscale_art.py`** — Real-ESRGAN on the art, with the two things a naive
  pass gets wrong fixed: transparency is preserved (premultiplied RGB and alpha
  upscaled separately, then un-premultiplied), and this build's broken `-s 2` is
  avoided by running the model at its native factor and resampling. Masters are
  never overwritten; upscales land beside them as `@2x` and
  `eternal_sill.hi_res_path()` makes the page prefer one automatically.
- **What it is for, measured** — the Eternal Page parchment (1216×603 painted
  across a 2200 px stage) is the only genuinely under-resolved asset; the sill
  sprites, PPG faces and galgame backgrounds are already large enough for where
  they are shown. `python tools/upscale_art.py --plan` prints that table.
- **What it cannot do** — make a 360p Hysilens separable. She upscales cleanly to
  500×880 and still keeps the blue stage baked into 96 % of her pixels; the matte
  failure is lack of an edge, not lack of pixels. She stays a portrait.
  Suite: `tools/test_upscale_art.py` (13). Detail: `docs/UPSCALING.md`.
### 2026-10-27 — the Heirs, rebuilt and honestly measured
- **All thirteen cards rebuilt** — every inherited `AUTO REFINEMENT` block removed (69
  sentence templates across twelve cards: "begin sentences with transitional
  phrases", "use 'hmph' alone", "end with trailing ellipses"), replaced with a
  **CANON COMPLEXITY** block drawn from `databank/chrysos-heirs/`: what each Heir
  notices, carries, hides and cannot forgive. Behaviour, never phrasing.
- **A mechanical canon audit** — `tools/audit_heir_claims.py` checks Coreflame,
  Titan, MBTI, race, hometown, titles and nicknames against the databank, and exits
  non-zero on drift. It found three wrong identities: Hyacine listed Human (she is
  **Skyfolk**), Cipher's home given as Okhema (she is from **Dolos**), Anaxa's as the
  Grove (he only studied there). Six cards also gained the nickname vocabulary they
  never had — including Cerydra's eight Dux titles.
- **Mydei's parentage fixed** — the card made Gorgo both his father and his mother
  while naming Eurypon as the father. `chapter-02-light-slips.md` calls him "son of
  Gorgo" repeatedly, so the card now says son of the king — Gorgo in the chapters,
  Eurypon in the chronicle — and the invented mother is gone. Castorice's
  twin-brother-becomes-Thanos origin and Hyacine's descent from an unnamed Heir have
  **no** support in the databank and are recorded as open questions instead of being
  rewritten.
- **Picture appreciation is two-stage** — a neutral eye describes, then the Heir's own
  model judges. Same picture, three Heirs: Mydei on restraint and forged stone,
  Hyacine on hope and warmth, Tribbie on stars and flowers in the plural; cross-Heir
  overlap 0.07–0.12, against one shared critic's voice before.
- **Eyesight was broken, not weak** — `VISION_MODEL=gemma3n` refuses images through
  Ollama ("does not support multimodal requests") and `qwen3-vl:8b` returns empty;
  `qwen2.5vl:7b` answers. Both `SENSES_MODE` branches now set the eye that works, and
  the README stops claiming one model both hears and sees.
- Suites: `test_aesthetic` 51, `test_eternal_page` 395.

### 2026-10-28 — the instrument corrected
- **The gate was measuring itself.** Ollama samples deterministically, so
  reject-and-retry repeated the *same* request up to thirteen times and got the same
  line back — Castorice produced thirteen copies of one canon quote. `llm.chat` now
  takes a `seed` and the gate passes the attempt number; Tribbie's skip vanished and
  Castorice's dropped from two to one.
- **Exhaustion is no longer scored** — a case with nothing surviving is **skipped**
  and reported as missing coverage instead of judging a literal `"..."` at 45/25
  (five of the previous run's sixteen failures were that artefact). `--report`
  defaults to a dated file so a run can never overwrite a tracked measurement, and
  `--debug-exhausted` prints every rejection and its reason.
- **The anti-cheat re-baselined on evidence** — the premise was wrong: Mydei's canon
  lines average 14.5 words, so he is not terse. The relaxation keys on the *line
  produced* (six words or fewer ⇒ exact repeats and crutches only).
- **Result: 45 of 50 scored cases pass (90 %), one skipped** — against 37/52 (71 %)
  when the work began. Most of the gain is the instrument, and the document says so.
- `tools/test_style_gate.py` (19 checks) now covers the filter logic itself, and
  `tools/run_all_tests.py` runs **28 suites, 1855 checks** in one command — it
  immediately caught a stale assertion still demanding Earth topics be suppressed
  after `b47cd14` had deliberately changed that policy.

### 2026-10-28 — the book
- **The UI adopted the in-game "As I've Written" page**, chosen from screenshots
  actually seen rather than remembered: a cream two-page spread with a gold
  egg-and-dart frieze, a radiating corner bracket, Roman-numeral index tabs,
  terracotta chevrons and warm-brown serif ink, on a deep indigo world with a low
  horizon. The archive page where `δ-me13.exe` sits as a tile turned out to be another
  page of the same book.
- `src/ui_theme.py` holds the measured palette, an offline Palatino stack and the
  ornaments as CSS only; it covers the app background, headings, tabs, buttons, chat
  cards, inputs, expanders, metrics, alerts, sidebar, captions, code, tables, labels,
  slider, uploader and tooltips. The Eternal Page menu became a paper slip with an
  egg-and-dart header. Layout and behaviour untouched.
- **Motion audit** — two stage screenshots three seconds apart differ in **0** of
  2,464,000 pixels: nothing floats on the Eternal Page at idle. Emotion marks bob;
  sprites roam horizontally; everything else is foliage and chrome.
- Detail: `docs/UI-AIW.md`.


### 2026-10-28 — the world kept running
- **The little Amphoreus is running again** — `--interval 900 --catch-up`, so the
  clock advances a day every fifteen minutes of real time and the seven days the
  world spent at rest are being generated rather than skipped. Chronicle grew
  2621 → 2639 lines in the first two minutes as the gap filled.
- **The calendar is verified against GMT+8**, not assumed: the stored clock and
  `WorldClock.from_gmt8()` render identically (Year 4933, Month of Mourning, Week 3,
  Day 7 — Action Hour at 2026-10-28 12:59 +08:00).
- **`tools/start_world.ps1`** — start, `-Stop` (which marks the rest so the next
  start can catch up) and `-Status`, with the log at `world_runtime/engine_run.log`.
- The rest marker had stood since **2026-09-16 20:08**, i.e. 42 civil days missed;
  `rest_catchup` caps a catch-up at 7 days by design, so the most recent week is the
  one being written. The earlier five weeks remain unwritten and are recorded here
  rather than silently replayed.
- **Ten stale engines were running.** Inspecting the processes showed ten copies at
  `--interval 86400` — the default, started without the flag and never reaped — all
  writing to the same chronicle while a new one ran at 900 s. They were stopped;
  exactly one engine remains (pid 41504 and its child), and the chronicle kept
  climbing 2746 → 2786 lines over three minutes with no duplicates. **Known defect,
  not yet fixed:** `world_engine` start does not refuse when `world_runtime/engine.pid`
  points at a live process, which is how ten copies accumulated. The guard is the
  next change; the pid file was in fact holding a stale pid when the new run began.
- **Backfilled the weeks the 7-day catch-up could not reach.** `tools/backfill_lore.py`
  (`--from`, `--to`, `--dry-run`) writes specific historical days through the same
  engine that writes every other day, because the world was designed to run
  unattended and an operator may decide the earlier weeks should exist. Running now
  for **2026-09-17 → 2026-10-21, 35 days**; the live engine was stopped first so the
  chronicle has one writer. Chained after it: the voice gate for Aglaea and Hysilens,
  then the engine restarts with `--catch-up`.
- **One writer per chronicle, enforced.** `world_engine` now refuses to start when
  `world_runtime/engine.pid` names a live process (`--force` overrides). The first
  version of that check used `os.kill(pid, 0)` — which on Windows is not a probe at
  all but `TerminateProcess`, so the liveness check could kill the engine it was
  asking about. Replaced with `OpenProcess` + `GetExitCodeProcess`, and proved:
  a live pid is detected, a dead pid is ignored, and the checked process is still
  alive afterwards.
- **The anomaly is in the Heirs' memories.** The world rested from 2026-09-16 and the
  missing span was generated in one sitting; the Heirs now carry that as a `world`
  memory (importance 4, all thirteen): the days came back all at once, the streets
  were right but their own feelings arrived out of order, things not yet lived were
  already worn into them. It happened, so they remember it.
- **Nothing was rewound.** There is no snapshot of the world state at the breakpoint —
  `world_state.json` is a single live file, and the only dated states on disk are
  August test fixtures — so a true replay from the breakpoint is impossible without
  inventing the start state. The generator has always run *forward* from the
  breakpoint; the only residual artefact is that the earliest generated days carry
  the present state's bonds and projects.
- **Slower, jittered cadence.** At 1× the engine already waits for the next GMT+8
  overlay period, so the world is calendar-locked by construction; the wait is now
  multiplied by a random factor (`AMP_WORLD_JITTER`, default 1.8×, i.e. up to ~1.8
  periods between days). Uneventful days are accepted — the world lives them rather
  than filling them.
- **Collective memory is logged.** `tools/log_collective_memory.py` writes a
  timestamped JSON of every Heir's stored memories plus a one-line digest, under
  `world_runtime/collective_memory/`; `--every N` keeps logging on an interval.
  First snapshot: 40 memories per Heir, all thirteen.
- **Voice cloning deliberately not started** — a performer's voice carries consent and
  licensing questions the charter has to answer before any code exists.
- **Keyed lorebook activation** (`src/knowledge/lorebook.py`) — the one external idea
  worth adopting, implemented as mechanism rather than rewrite: entries listen for
  keys, carry a priority, may be sticky for a few turns and cool down after firing.
  `from_markdown()` turns each Heir profile into entries keyed by its `##` headings, so
  "what is your Coreflame?" pins the Coreflame section before vector results are
  added. Suite: `tools/test_lorebook.py` (17). **Not yet wired** into the vector store
  — the caller decides how much room pinned entries get.
- **Checkpoints are taken, and a restore door exists.** `tools/checkpoint_world.py`
  writes a dated folder holding `world_state.json` and all thirteen Heirs' stores
  (49 files, 875 KB on the first run) with a `manifest.json` naming every file, its
  origin and its size. `--list` shows them; `--keep N` prunes; `restore(name)` copies
  a checkpoint back and is callable from the admin side. Deliberately **unproven**:
  no lock, no integrity check, no test that a restored world equals the saved one —
  the manifest exists so a future restore has something to check against.
- **Administrators can take and restore checkpoints from the Control Panel.** The
  checkpoint logic moved to `src/world/checkpoints.py` so the CLI and the UI share one
  implementation; the panel lists the last five, offers "Take a checkpoint now", and
  gates **Restore** behind a confirmation box with the warning above it — *never been
  verified, no lock, no integrity check*. Proven by booting the real app
  (`streamlit run src/ui_app.py --server.port 8502`) and driving it with Chromium:
  signed in, opened the Control Panel tab, expanded the section, three checkpoints
  listed, the save button present, Restore disabled until ticked, **zero console
  errors** (`world_runtime/art_review/admin_checkpoints.png`).
- **`test_sanctuary_live` repaired** — it froze Year 4932 / Month of Strife and failed
  the moment the world legitimately advanced. It now asserts what must be true of any
  live store (plausible year, month in range, overlay equal to `WorldClock.from_gmt8()`,
  sim untouched underneath) and compares scale-switch results against the copy's own
  origin. 163 passed, 0 failed; whole tree **1872 passed, 0 failed across 29 suites**.
- **The anti-cheat only knew the current scene.** `all_canon` is the lines of the part
  under test, so a Heir could quote its own canon from another chapter and pass —
  measured exactly: Aglaea answered *"I've woven many unforeseen events into the
  tapestry of fate…"*, verbatim from `chapter-03-through-petals.md`, and scored **22**
  instead of being refused. The quote check now receives a **global corpus** per Heir
  (every line they speak anywhere in the databank; 732 for Aglaea), cached. Effect:
  **Aglaea 3/4 → 4/4** (avg style 88), her best score, with no change to her voice.
- **Hysilens 2/4 → 3/4** (avg style 86): her card now says the banquet is her past, not
  a line she reaches for, and forbids opening with a sigh. The remaining 78 is a
  register near-miss.
- **A failed hypothesis, retraced.** I first tried forbidding the tapestry phrase in
  Aglaea's card; it added two 78s and did not stop the quote (3/4 → 1/4). Reverted to
  the previous card and fixed the real cause instead. Recorded because a card edit that
  looks like progress can just be noise.
- **Full gate on the corrected harness: 48 of 49 scored cases pass (98 %), one skipped**
  — up from 45/50 (90 %) *despite* the gate now being stricter for every Heir, because
  refusing canon quotes forces lines that are actually theirs. Per Heir: Aglaea, Anaxa,
  Cerydra, Cipher, Hyacine, Mydei, Phainon, Tribbie 4/4; Castorice 3/3 with one skip;
  Cyrene, Evernight, Hysilens 3/4. The three remaining near-misses are Cyrene (78),
  Evernight (58) and Hysilens (78).
- **Reports are unique per run** — the dated name collided when two runs happened on the
  same day and one measurement replaced another; the default now carries the time.
- **Night was already gated — the assumption was mine, not the code's.** `is_rest_time()`
  is True at Curtain-Fall **and** Entry Hour, and `run_day()` returns before any Heir
  speech, errand or project, writing one night line instead. The queue item
  "period-aware day generation" was based on a wrong reading: at 1× the clock does not
  advance inside `run_day` at all, the overlay supplies the period, and the engine is
  called once per period. What *was* wrong: the night branch did
  `return [night]`, dropping every fact the hour had already written from its result
  (the chronicle kept them, callers did not). Now `return lines + [night]`, and the line
  says the city *settles* rather than rests — a note left for the visitor at night is
  not a contradiction.
- **The handset view was broken, and the phone test found it.** At 360 px the sidebar
  was `initial_sidebar_state="expanded"`, so it laid itself over the content and
  intercepted every tap — the tabs were literally unreachable, with Playwright
  reporting "subtree intercepts pointer events" forty times before failing. Now
  `"auto"`, so a handset collapses it. Verified in a 360×740 Chromium context with a
  mobile UA and touch: 9 tabs visible, the AIW theme applied, **no horizontal overflow**
  (`scrollWidth` 360), the Control Panel reachable, the checkpoint section expandable
  with its warning legible, and **zero console errors**
  (`world_runtime/art_review/phone_checkpoints_360.png`).
