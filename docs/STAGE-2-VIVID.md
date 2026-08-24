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
