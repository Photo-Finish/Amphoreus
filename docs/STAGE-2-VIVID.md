# Stage 2 — Vivid society & natural world (first delivery)

**Date:** 2026-08-18 (first delivery); extended 2026-08-22 … 2026-08-23  
**North star:** make the society and natural world as vivid as possible.

## Canon fit

| Choice | Official setting |
|---|---|
| Shared scenes | Organic co-presence; system hosts, never authors Heir speech |
| Black tide refusals | Journey-mode edge surges; Mydei watches Kremnos; Aftermath peaceful |
| Overhear | Aglaea’s golden threads; Cipher’s locked doors |
| NPCs | Alive-only roster in `world_events.NPCS` |
| Voice fidelity | Pillar under life — not this delivery’s product |

## Cross-checks exercised

- Mydei + black tide surge at Castrum Kremnos → invite declined; quiet tide → accepted
- Overhear near Phainon → Aglaea injector differs from Phainon’s / Hyacine’s
- Aftermath → tide-edge prompt empty; journey → non-empty for Mydei under surge
- Styxia NPC under surge → line tightens; Gorgo rejected
- Lived road to surged Aidonia → sky/tide wording; `ui_travel` uses lived vignette
- Place-hour lists co-located Heirs; letters/rumors/bond drift surface in continuity
- Lived entities: night withdraws the Dawn Device; Grove has no sea; Cultivation sows, Reaping reaps; road ≠ house; surge thins the market without inventing famine

## Lived entities (positive, coarse)

Full user catalog: [`docs/LIVED-WORLD.md`](LIVED-WORLD.md) (31 entities, 17 mechanisms, contradiction table).

`src/world/lived_entities.py` — Amphoreus-native physical stage (Dawn Device, sky, harvest, market, road, Grove, sea, forge, shrine, …). No famine / plague / war / storm-as-entity. Status is derived from Light Calendar + Keeper weather + place.

Shown in **Control Panel** and **Admin Console** (`src/ui_world_stage.py`) together with Keeper ambient (weather, errands, news). Visit “This hour” and the Heir prompt only inject entities that are *here* this hour.

Suite: `tools/test_lived_entities.py` (59 checks) plus the original 44 vivid checks.

## Lived day mechanisms (tick verbs)

`src/world/lived_mechanisms.py` — the 17 day-verbs mutate `world.vivid["lived"]` on `run_day` (after Keeper ambient, before rest-early-return). Feeding/growing once per Light Calendar **date**. Rest = Curtain-Fall or Entry Hour. Night withdraws the Dawn Device even if today's weather was blazing.

## Residents (street, not protagonists)

`src/world/resident_npcs.py` — ~110 templated Amphoreus residents across real map cities. Copilot `world_events.NPCS` left verbatim (merge at read-time). On tick: visible set this hour from period + mechanism flags; 1–3 Heir–resident encounters. Grove has no harbor-fishers. Resting hour: hearths, not a feast square.

## Visitor UI (notice, don't inventory)

- **Visit:** one literary stage paragraph for *this* place and hour; 2–4 people actually here to greet. No 17-mechanism catalog, no Here/Near/Elsewhere census.
- **Gazette:** “This Hour in the World” (handful of tick facts) and “Seen in the Streets” (encounters). Heirs Abroad remain the spine.
- **Road:** existing lived vignette plus a sheltering/carrying clause.
- **Control Panel / Admin:** the dense ledger stays there.

Suites: `tools/test_lived_mechanisms.py` (63), `tools/test_resident_npcs.py` (33),
`tools/test_lived_entities.py` (61), plus the original 44 vivid checks.

## Second delivery — society continuity & land handoff (2026-08-22)

| Feature | What the visitor feels |
|---|---|
| Multi-Heir Galgame | Gathering → visual-novel with several sprites |
| Shared hour memory | Solo Visit remembers a past gathering |
| Walk-in scenes | Arrive mid-letter / mid-talk / rumor |
| Resident recognition | Street people remember you |
| Bond weather | Soft rivalry / thread / loyalty cues when co-located |
| Pollux / Maze fairies / Mountain Dwellers | Castorice's dragon; Aedes fairies in Membrance; Okhema smiths (not Aidonia) |
| Walk→Visit eco | Care/notice on Walk is known on Visit |
| Map this-hour | Place popup carries a lived vignette |
| Daybook | Gazette’s “Today in Amphoreus” |
| Absence return | Soft beat after ≥5 days away |
| Collective memory honesty | Doc + secondhand teaching echo |
| Engine default + named tunnel | World lives on launch; stable hostnames when configured |

Modules: `society_life.py`, `resident_memory.py`, `daybook.py`, `ui_galgame_group.py`.
Charter unchanged.

## Third delivery — invites, land, guest path (2026-08-22)

| Feature | Note |
|---|---|
| Heir-initiated sit | Co-located Heir proposes; operator accepts |
| Letter mini-scene | read / wait / leave |
| Bond weather | Cassie; Cipher doors; Earth underfoot |
| Resident errands | Date-advancing street work |
| dromas_walk_v2 | Promoted to live film |
| Little Ica | With Hyacine only |
| Seasonal eco | Official Light Calendar months only — no invented festivals |
| Tide on land | Surge thins EDGE cities + blacktide sky |
| Walk → Map | Pin + vignette |
| Guest Walk | Notice OK; care chat operator-only |
| Absence chrome | Visit return vignette |
| Daybook spine | First on Chronicle/Gazette |
| Desktop exe | Repo-root `AmphoreusSanctuary.exe` |

## Fourth delivery — pictorial land polish (2026-08-23)

| Feature | Note |
|---|---|
| Launcher reuse | `launch_sanctuary.cmd` reuses healthy `:8501`; does not kill foreign Streamlit |
| Scroll with Life on | Wheel/touch on the life iframe forwards to `stMain`; sprites stay clickable |
| One ground sill | Page-layer walkable sprites at viewport `bottom: 0px` (`ground-sill`); no mid-frame floor strip |
| Backdrop under life | `#amp-land-photo-host` first child of `stAppViewContainer` (z0); life iframe z25 |
| Stall HSR art | Place-family stalls from `market_stall` pipeline (`build_place_env_sprites.py`) |
| Chimera wiki cuts | Color variants from Little Chimera wiki sources (`build_hsr_life_sprites.py`) |
| Caravan balance | Trade caravan additive; cap preserves chimera + solo roamers |
| Civic spacing | Gate 28% / fountain 58% / mosaic 76%; ≥13% gate–fountain gap after layout |
| Mosaic / pillar | Env sprites rebuilt for Okhema / Grove / Aidonia families |

Modules: `src/ui_scene_life.py`, `src/ui_weather.py`, `src/ui_look.py`,
`src/world/ecosystem.py`. Suites: `tools/test_ecosystem.py` (258),
`tools/test_walk_map_handoff.py` (13), `tools/_audit_life_scroll.py`.
Charter unchanged.

## Fifth delivery — visitor emotion (2026-08-24)

| Feature | Note |
|---|---|
| DistilRoBERTa tone | `j-hartmann/emotion-english-distilroberta-base` on CPU when installed |
| Lexicon fallback | Chat never stalls if torch/transformers/weights missing |
| Prompt block | `# How the visitor seems` — Amphoreus colour, no BERT/Earth jargon |
| Wiring | `AgentManager.chat` + teaching path + `group_chat.heir_speak` |
| Toggle | Control Panel / `AMP_VISITOR_EMOTION` — default ON |
| Install | `requirements-emotion.txt` + `tools/download_visitor_emotion_model.py` |

Module: `src/core/visitor_emotion.py`. Suite: `tools/test_visitor_emotion.py`.
Charter unchanged (knowledge wall).

## Sixth delivery — 1x period ticks & world machine (2026-09-16)

| Feature | Note |
|---|---|
| 1x ticks | One GMT+8 overlay **period** (~4.8 h), not one 24 h sample of whatever hour the daemon started. Entry / Curtain-Fall stay rest. Lucid / Action / Parting live. Overlay clock is not advanced. |
| World machine | Engine keeps running without a conversation model (Keeper fallback, hearths, streets, eco). Heir decide/talk waits for a tagged Ollama model. |
| Teaching echo | Visitor → Heir → other Heirs (talk / letter / echo) may carry Earth names already taught. |
| Keeper fallback | News/errands that name a Titan-month stay in that month. |
| Rest sprites | Resting status uses still art; roamers do not cross the square at night. |
| Journey chrome | Sidebar follows the bond (not a forever-stranger caption). |

Suites: `tools/test_sanctuary_calendar.py`, `tools/test_society_life.py`, `tools/test_world_machine.py`.

## Seventh delivery — online conversation API (2026-09-16)

| Feature | Note |
|---|---|
| Voice path | **Online API** alongside RAG and OPLoRA. Control Panel stores provider, base URL, model, and key. |
| Key storage | `secrets/online_llm.json` only (gitignored). Placeholder: `online_llm.example.json`. Never in git or `world_state.json`. |
| What goes remote | Visit chat, group talk, Heir decide/react. |
| What stays local | World machine (Keeper fallback, hearths, streets, eco). Pictures/music still use local senses models if those are configured. |
| GPU | Conversation does not load Ollama / OPLoRA. Switching back to RAG restores the local endpoint. |

Suite: `tools/test_online_llm.py`.

## Eighth delivery — land z-order & native scroll (2026-09-16)

| Feature | Note |
|---|---|
| Sprites above dialogue | Life iframe z55, above chat/wordings (z40) and copy (z5). Tabs / look chrome stay higher. |
| Click popup on top | `#amp-land-notice-host` on the parent page at z400 — above sidebar, tabs, and chat. |
| Scroll | Life iframe stays `pointer-events: none`. Capture-phase wheel hijack removed so the page scrolls natively. Sprite clicks are hit-tested from the parent. |

Audit: `tools/_audit_life_scroll.py`.

## Ninth delivery — An Eternal Page (2026-09-16)

| Feature | Note |
|---|---|
| Distinct page | Tab **An Eternal Page** and sidebar page `3_An_Eternal_Page.py` — not Visit chatboxes. |
| Cute companions | Official Pom-Pom Gallery stickers (`assets/eternal_page/cute/`). No geometric placeholders. |
| Desktop-buddy talk | Click to stand near, double-click for one, drag to rearrange, right-click to pet (mood only). All thirteen / Clear / name chips. Whisper dock, speech bubbles. Parent hit-test (iframe sandbox cannot navigate). |
| Shared memory | Speakers call `manager.chat` (same history.jsonl / bonds as Visit). Listeners still hear the line. Journey and Aftermath use the same store. |
| No land systems | No weather, ecosystem, chimera, or dromas on this page. Wheel over the stage is passed to the parent. |
| Faces follow feeling | Official PPG poses swap from conversation history plus sanctuary ongoings (mood, tide, travel, gifts, grievance). `src/world/eternal_emotion.py`. |
| Star-swirl stage | Official Vortex of Genesis area art (`assets/galgame/ground/bg-vortex-of-genesis.jpg`) — cosmic swirl, not the Exotale garden plaza used by Visit/Walk. |

Suite: `tools/test_eternal_page.py`. Art: `python tools/fetch_eternal_page_art.py`.

## Tenth delivery — Eternal Page emotion VFX & gestures (2026-09-16)

| Feature | Note |
|---|---|
| Emotion marks | CSS overlay on each PPG bust: flush, vein, steam, sweat, tear, sparkle, heart, ?, !, dizzy, zzz, shock, flower, ice, veil, note, shy hands, glow. Driven by `data-amp-emotion` plus a short gesture overlay. |
| Gesture set | Click near, double-click solo, drag rearrange (kept). Shift+click pat, Ctrl+click poke, Alt+click tease, Shift+right-click hold hands, more combos and hover keys (P/H/F/W/C/G/B/T/K). Right-click menu lists them. Legend on the stage. |
| Heir reaction | Gesture → VFX + pose/emotion overlay + `living_world` mood nudge with a factual reason. Light temperament table (e.g. Mydei poke → anger vein). No authored Heir speech. Optional “Ask how that felt” is an explicit `manager.chat` turn. |
| Bridge | Parent hit-test still; `ep_act`/`ep_id` query params plus the command bus. Wheel still scrolls the parent. |

Suite: `tools/test_eternal_page.py`.

## Eleventh delivery — mission dialogue → per-Heir / collective memories (2026-09-16)

Canon mission dialogue is now split by **who was actually there**. Original
`databank/missions/` chapter and adventure files (and wiki Tribbie/Dialogue) stay
verbatim. New files live under `databank/memories/` plus rebuilt
`<HeirFolder>/personal-memories.md` rollups for the voice digest.

| Rule | What happens |
|---|---|
| One Heir on-stage | Full unit → that Heir's personal file |
| Two or more Heirs | Full unit → `collective/`; each Heir gets a pointer + witness excerpt |
| No Heir present | Skipped (NPC/visitor-only beats) |
| Titans / memosprites | Not treated as that Heir speaking (Oronyx ≠ Evernight, Thanatos ≠ Castorice, Dolimem ≠ Cyrene) |

Rebuild: `python tools/extract_mission_memories.py`  
Gate: `python tools/test_mission_memories.py`  
Layout notes: `databank/memories/README.md`. Not added to Chroma `GLOBAL_PATTERNS` (chapters remain the RAG dialogue source).

## Accepted spec — Cyrene year cycle (2026-09-16)

Three Light-Calendar blocks occupy the Cyrene seat's **picture** `{childhood, demiurge, mem}`. Whisper always uses card id `"cyrene"` (Mem has no talk card; Fairy still speaks to childhood Cyrene). Unwired — no Eternal Page / Visit change. Spec: [`docs/CYRENE-CYCLE.md`](CYRENE-CYCLE.md). Module: `src/world/cyrene_cycle.py`. Suite: `tools/test_cyrene_cycle.py`.

## Twelfth delivery — Visit painted sky / land glyphs (2026-09-16)

The Visit sun was two SVG circles because `dawn.png` (Dawn Device) was on disk but not used. Sprites now take a PNG whenever one exists. Clear weather overlays the Device picture instead of a radial-gradient disk; twilight uses a painted moon. Grass / wheat / wind / leaf ambient is painted tufts, not CSS bars. New emblems live in `assets/life_sprites/`. Suite: `tools/test_ecosystem.py`.

