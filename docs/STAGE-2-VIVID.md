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
