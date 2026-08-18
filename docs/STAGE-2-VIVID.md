# Stage 2 — Vivid society & natural world (first delivery)

**Date:** 2026-08-18  
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

`src/world/lived_entities.py` — Amphoreus-native physical stage (Dawn Device, sky, harvest, market, road, Grove, sea, forge, shrine, …). No famine / plague / war / storm-as-entity. Status is derived from Light Calendar + Keeper weather + place.

Shown in **Control Panel** and **Admin Console** (`src/ui_world_stage.py`) together with Keeper ambient (weather, errands, news). Visit “This hour” and the Heir prompt only inject entities that are *here* this hour.

Suite: `tools/test_lived_entities.py` (59 checks) plus the original 44 vivid checks.
