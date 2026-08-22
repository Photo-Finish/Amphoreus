---
name: amphoreus-world-map
description: >-
  Amphoreus places, roads, Dawn/Evernight forms, travel periods, backdrop
  fitness, and ecosystem place rules. Use when placing Heirs or life on the
  map, computing travel, naming Dawn-era counterparts, picking galgame
  backgrounds, checking chimera/dromas/shore fitness, or editing lived-world /
  walk-land / geography features.
---

# Amphoreus world map

Canon geography lives in **databank + `map_data`**. Do not invent cities, roads, or Dawn forms.

## Source of truth (read in this order)

1. `databank/world/map.md` — places, direct roads (periods), longest journeys
2. `databank/world/geography.md` — adjacency, parent→sub-area, HoYoLAB/wiki grounding
3. `databank/world/time-forms.md` — Dawn vs Evernight forms, Veil, Nether, gates
4. `src/world/map_data.py` — engine graph: `LOCATION_POS`, `ROADS`, `TIME_FORMS`, `travel_time` / `travel_days` / `can_cross_to`
5. Place depth: `databank/wiki/locations/<slug>.md`
6. Daily texture: `docs/LIVED-WORLD.md`, `src/world/lived_entities.py`, `src/world/ecosystem.py`

City-state essays: `databank/world/city-states.md`, `major-locations.md`. Fauna: `databank/world/fauna.md`.

## Hub layout (summary)

- **Okhema** hub; **Dawncloud** same city (0 periods)
- Twin **Janusopolis** east (~1); **Grove of Epiphany** west (~2); **Great Tomb** near Grove
- **Aidonia** northern snow; **Styxia** on River of Souls; Styxia↔Aidonia ~3
- **Eye of Twilight** fallen sky castrum — **no road** (sky bridge lost)
- **Aedes Elysiae** / **Vortex of Genesis** sea / veil routes — long journeys

Travel unit = Light-Calendar **period** (5 per day). Engine refuses teleport: use `map_data.travel_days` / `travel_description`.

## Dawn forms (`TIME_FORMS` in map_data)

| Present (Evernight-era) | Dawn-era form |
|---|---|
| Okhema | Eternal Holy City |
| Dawncloud | Demigod Council |
| Janusopolis | Sanctum of Prophecy |
| Grove of Epiphany | Radiant Scarwood |
| Castrum Kremnos | Bloodbathed Battlefront |
| Styxia | Warbling Shores |
| Eye of Twilight | Fortress of Dome |
| Great Tomb | Universal Matrix |
| Aedes Elysiae | Aedes Elysiae, of old |

Special: **The Nether** under Styxia (Thanatos-blessed). Cross-era rules in `time-forms.md` / `can_cross_to` — Veil (Oronyx / Evernight / Trailblazer), Janus gates (Tribbie), Nether (Castorice line).

## Backdrop fitness

`src/ui_backgrounds.py` — `LOCATION_MATCHES` (ordered substrings) → `assets/galgame/bg-<slug>.jpg`. Prefer specific Dawn/ruin names before parent city (e.g. `dragonbone` before `styxia`). Heir home art: `PER_HEIR_BG`.

## Ecosystem / life place fitness

`src/world/ecosystem.py` + place sets in `lived_entities.py`. Use `logic_faults(scene, place)` mentally:

| Life / prop | Belongs in |
|---|---|
| Chimera | Holy-city family (`CHIMERA_CITIES`) — not Grove/tomb picnic |
| Dromas | `DROMAS_ROADS` places |
| Pollux | Only where **Castorice** stands (dragon companion; not Workshop dromas Pollux) |
| Maze fairy | Aedes Elysiae family in **Month of Membrance** only |
| Mountain Dweller | **Okhema** family (+ thin Kremnos forge echo) — **not Aidonia** |
| Shore / siren / net / tidepool | Working seashore (`WORKING_SHORE`) |
| Boat | Shore or River of Souls places |
| Forge / banner | Kremnos family |
| Market stall | Market cities (not Grove) |
| Mill | Field places (e.g. Aedes) |
| Fountain | Civic plazas only (`FOUNTAIN_PLACES`): Okhema family, Janus/Sanctum, Styxia/Warbling, Grove/Scarwood, Demigod Council — never with a well |
| Well | Practical cisterns only (`WELL_CITIES`): Aedes, Aidonia, Castrum Kremnos — never with a fountain |

Forbidden statuses: dead / starving / plague. Grove: no chimera or shore life. Vortex: no fishing-shore clutter. Never author Heir speech from the ecosystem layer.

## Search patterns

```text
path: databank/world/map.md
path: databank/world/geography.md
pattern: Okhema ↔|TIME_FORMS|travel_days    path: src/world/map_data.py
pattern: dragonbone|Warbling Shores         path: databank/wiki/locations
pattern: logic_faults|DROMAS_ROADS|CHIMERA  path: src/world/ecosystem.py
pattern: LOCATION_MATCHES|bg-               path: src/ui_backgrounds.py
```

## Related Stage-2 docs

- `docs/STAGE-2-VIVID.md`, `docs/LIVED-WORLD.md`
- Charter constraints: skill `amphoreus-charter`
- Lore quotes: skill `amphoreus-databank-rag`
