# The Keeper's Canon — grounding for the Ambient World Director

The *Keeper of Amphoreus* (`src/world/ambient.py`) is the second intelligence
that sets the day's stage — weather, errands, and news — without authoring the
Heirs. Its knowledge is grounded in the canon compiled in this databank, so the
world it generates *feels* like Amphoreus and never invents modern or alien
concepts.

## Cities & patrons

| City | Character | Patron | Notes |
|---|---|---|---|
| Okhema | "Eternal Holy City" | Kephale (Worldbearing) | Stands under the slumbering Titan + the Dawn Device; baths, chimeras, dromases; Council of Elders |
| Janusopolis | "City of Thousand Gates" | Oronyx, Janus, Talanton (Three Fates) | Temple of the Three Fates; pilgrims pass through its gates |
| Grove of Epiphany | "Home of Sages" | Cerces (Reason) | Scholars, prophets, ceremonial officiants |
| Castrum Kremnos | "Capital of Might" | Nikador (Strife) | Warrior fortress-city; forges and drills; the Kremnoan Detachment |
| Styxia | "Pearly Shores" | Phagousa (Ocean) | Pale city of the afterlife; sea sirens; the bell of Styxia |
| Aidonia | "Snow City" | Thanatos (Death) | Frozen city of death-rites on the snow plains |
| Dawncloud | Demigod Council | — (over Okhema) | Citizens' assembly; Festival of Phagousa plays |
| Aedes Elysiae | Wheat village | Oronyx (Veil) | Cyrene & Phainon's home; windmills, Voyager's Wharf, Membrance Maze |
| Vortex of Genesis | Primal sanctuary | the Twelve Titans | Coreflames gathered to remake the world |
| Great Tomb | Universal Matrix | the Nameless Titan | Deepest ruin; Cyrene's archives of all recurrences |

## The Light Calendar (weather & festival seeds)

The Director's weather and errand flavor follow the 12 months:

- **Month of Gate** (Janus) — renewal; doors open; old keepsakes discarded
- **Month of Balance** (Talanton) — contracts, judgments; day = night
- **Month of Evernight** (Oronyx) — sunlight weakens; instinct over reason
- **Month of Cultivation** (Georios) — sowing; busiest month; dromases vigorous
- **Month of Joy** (Phagousa) — brewing, festivities, fishing; best celebrations
- **Month of Everday** (Aquila) — hottest; Dawn Device brightest
- **Month of Freedom** (Kephale) — unstructured idleness
- **Month of Reaping** (Cerces) — harvest; second busiest month
- **Month of Weaving** (Mnestia) — memory & storytelling; weaving festivals
- **Month of Strife** (Nikador) — war season; sacrificial rites
- **Month of Mourning** (Thanatos) — burial & comfort; priests busiest
- **Month of Fortune** (Zagreus) — gambling & chaos; Scarlet/Golden ghost days

Weather is Titan-flavored (light as doors, veils of evernight, golden harvest,
ash and long shadows, silver tides). Amphoreus has no rain as we know it.

## Living details the Keeper uses

- **The black tide** devoured most cities; Okhema stands under the Dawn Device.
  The frontier is dangerous and shrinking.
- **The Thief Star** (Zagreus' meteor) marks day's end; crimson = ill omen.
- **Creatures**: dromases (earth-eating burden beasts of Georios), chimeras
  (Okhema's small mascots, they howl "Awoo"), sea sirens of Phagousa, Mountain
  Dwellers.
- **Events**: Festival of Phagousa plays, chimera work-squads, the Seal Slammers
  Arena, expedition squads beyond the light, dromas anomalies.

## Files

- `src/world/ambient.py` — `KEEPER_KNOWLEDGE`, `MONTH_LORE`, `CITY_ERRAND`,
  `NEWS_PALETTE`, `DIRECTOR_SYSTEM`, and the deterministic fallback.
- `src/world/world_engine.py` — calls the Keeper once per day (default model
  `deepseek-r1-distill:32b`; `--ambient-model` to override).
