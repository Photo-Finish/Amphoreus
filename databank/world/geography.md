# Geography of Amphoreus — How the Locations Are Interconnected

> A researched determination of Amphoreus's geographic interconnection, compiled
> from the English HSR wiki (fetched 2026-08-13 via `tools/fetch_wiki_amphoreus.py`
> + a targeted re-fetch of the world/area pages), the local wiki databank
> (`databank/wiki/locations/`, 89 pages), the quest/mission transcripts
> (`databank/build/` and `databank/missions/`), and the official HoYoLAB
> "Chronicles of Amphoreus" articles mirrored in the databank.
> *(Reddit was unreachable from this machine — 403 — so forums were not used;
> the official HoYoLAB chronicles and the wiki serve as the authoritative
> "forum-class" lore essays instead.)*

---

## 1. The world at a glance

Amphoreus (The Eternal Land) was an isolated, memoria-and-data sandbox world
(Scepter δ-me13's experiment), reborn after the Scepter's destruction. During its
last cycle — the "Era Nova" — the world was divided into regions, each carrying
one or more explorable **areas**. The in-game map groups areas by era:

| Region | Dawn-era area | Evernight-era counterpart |
|---|---|---|
| Okhema | "Eternal Holy City" Okhema | "Fallen Twilight City" Okhema |
| Castrum Kremnos | "Bloodbathed Battlefront" Castrum Kremnos | "Strife Ruins" Castrum Kremnos |
| Janusopolis | "Sanctum of Prophecy" Janusopolis | "Abyss of Fate" Janusopolis |
| Grove of Epiphany | "Radiant Scarwood" Grove | "Murmuring Woods" Grove |
| Dawncloud (within Okhema) | "Demigod Council" Dawncloud | "Lightless Chapel" Dawncloud |
| Styxia | "Warbling Shores" Styxia | "Dragonbone City" Styxia |
| Eye of Twilight | "Fortress of Dome" Eye of Twilight | "Cloudedge Bastion Ruins" Eye of Twilight |
| Great Tomb of the Nameless Titan | "Universal Matrix" Great Tomb | "Nightmare's Echo" Great Tomb |

**Outworld** (areas outside the city-state web): **Vortex of Genesis**, **Aedes
Elysiae**, and **"Memortis Shore" Ruins of Time**.
**Exotale**: "Beyond Time: An Eternal Page".

The **six major city-states** (per the wiki's Geography section, citing the
*Ancient Hymn* trailer): Okhema, Janusopolis, Grove of Epiphany, Castrum Kremnos,
Styxia, and Aidonia. Aedes Elysiae and the Eye of Twilight are separate great
places (the village beyond the veil; the fallen sky kingdom).

---

## 2. Parent → sub-area structure

- **Okhema** ("Eternal Holy City", beneath the slumbering Kephale and the Dawn
  Device): Kephale Plaza, Marmoreal Market, Marmoreal Palace (baths), Hall of
  Respite, Garden of Life, Hero's/Overflowing baths, Damionis, Path of Parting,
  Court of Seasons, Dromas Workshop, Seal Slammers Arena, the Ancient City
  (Main Gate, Market).
- **Dawncloud** (the council seat *within* Okhema; Demigod Council): Sacred Path
  of Dawncloud, Central Assembly Hall, **Titan Cliff** (where Kephale's form
  slumbers — also where Anaxa is found), Demigod Council Forecourt, Hand of
  Zagreus; Evernight counterpart **Lightless Chapel**.
- **Janusopolis** ("City of Thousand Gates" / "Abyss of Fate" / Temple of the
  Three Fates): Sanctum of Prophecy (Dawn), Abyss of Fate (Evernight), Gate of
  Destiny, Archive of Prophecies, the Century Gate approach.
- **Grove of Epiphany** ("Home of Sages"): Radiant Scarwood (Dawn), Murmuring
  Woods (Evernight), Library of Philia, Sealed Chamber, the seven schools' halls.
- **Castrum Kremnos** ("Capital of Might", a *mobile fortress*): Bloodbathed
  Battlefront (Dawn), Strife Ruins (Evernight), Kremnos Arena, Hall of Strife,
  the convict-built outer city (bridge to the outer city).
- **Styxia** ("Pearly Shores" / City-State of Dragons and Waves): Warbling Shores
  (Dawn), Dragonbone City (Evernight), Twin Moon Spire, Seabed of Luminous
  Remains, the River of Souls itself.
- **Aedes Elysiae** (Outworld): Sacrament Courtyard, **Voyager's Wharf**, the
  Membrance Maze, Wondrous Woods, the Garmentmaker.
- **Eye of Twilight** ("Sky Castrum"): Fortress of Dome (Dawn), Cloudedge Bastion
  Ruins (Evernight), the Twilight Courtyard.
- **Great Tomb of the Nameless Titan**: Universal Matrix (Dawn), Nightmare's Echo
  (Evernight), Data Advection Sector, Tidal Cooling Sector, the Demiurge Matrix,
  Space-Time Superposition Room.
- **Vortex of Genesis** (Outworld): the Apocalypse Altar and the sanctuary of the
  primal Coreflames.

---

## 3. The interconnection matrix (evidence-based)

"Type" abbreviations: **same-city** · **direct** (in-game map connection) ·
**road/travel** (quest journey) · **sea** · **river** · **sky** · **gate** ·
**removed** (existed, then cut in-story) · **model** (the world engine's current
graph; plausible but not canon-explicit).

| Connection | Type | Evidence (source) |
|---|---|---|
| **Okhema ↔ Dawncloud** | same-city | Dawncloud is the Demigod Council seat **within** Okhema; travel time 0. (`city-states.md`, `map.md`) |
| **Okhema ↔ Janusopolis** | direct + gate | Okhema's wiki **Connections** lists "Abyss of Fate" Janusopolis; the quest: "When you reached the Abyss of Fate **through the Century Gate**…" (`city-states.md`; `build/build_ch1_p5.py`) |
| **Okhema ↔ Grove of Epiphany** | direct | Okhema's **Connections** lists "Murmuring Woods" Grove; the Grove is where the Heirs research (Library of Philia). (`city-states.md`; `build/build_ch3_p3.py`) |
| **Okhema ↔ Styxia** | direct | Okhema's **Connections** lists "Dragonbone City" Styxia; the River of Souls runs toward Styxia. (`city-states.md`) |
| **Okhema ↔ Castrum Kremnos** | road/travel | The party "arrive[s] at Castrum Kremnos" and makes "the two trips to and from Castrum Kremnos"; the journey is long and draining. (`build/build_ch1_p4.py`, `build_ch1_p5.py`, `build_ch1_p8.py`) |
| **Okhema ↔ Vortex of Genesis** | direct, **one-way**, sea | Okhema's **Connections** lists the Vortex "(one-way)"; Aglaea interrogates the Trailblazer *at* the Vortex early on; the Vortex is "the starting point of the world, **hidden by the waves**". (`city-states.md`; `build/build_ch1_p3.py`; `major-locations.md`) |
| **Okhema ↔ Great Tomb** | model | No direct in-game link found; the world engine routes it via Okhema (10 p). Plausible (Okhema is the hub). |
| **Okhema ↔ Aedes Elysiae** | travel | Phainon travels from Aedes Elysiae to Okhema ("Phainon of Aedes Elysiae… heading toward us"); the world engine routes 12 p. (`build/build_ch3_p4.py`) |
| **Okhema ↔ Eye of Twilight** | model (ruin) | No present-day link; the sky bridge (below) is gone. The engine marks it an unreachable ruin on the horizon. |
| **Dawncloud ↔ Eye of Twilight** | sky, **removed** | Dawncloud's wiki **Connections**: "Okhema; 'Fortress of Dome' Eye of Twilight **(both connections removed during 'Dawn, Shine at the World's End')**". The Eye of Twilight is the city-state *in the clouds* that "looks down upon the world from the skies". (`major-locations.md`) |
| **Grove ↔ Great Tomb** | direct | Great Tomb's wiki **Connection**: "'Radiant Scarwood' Grove of Epiphany"; "a short descent from the Grove". (`major-locations.md`; `map.md`) |
| **Grove ↔ Castrum Kremnos** | model | The engine routes 6 p. No canon statement found; plausible (both inland regions). |
| **Janusopolis ↔ Oleinus** | direct | "Oleinus was an **agricultural city-state directly connected to Janusopolis**" with stable trade. (`databank/wiki/lore/oleinus.md`) |
| **Janusopolis ↔ Aedes Elysiae** | model | The engine routes a "coastal road" (9 p). Plausible — both are coastal; not canon-explicit. |
| **Styxia ↔ Aidonia** | river/land | Both cities sit on/behind the River of Souls and the northern snow plains; Aidonia lies "in the desolate northern wasteland". (`wiki/locations/aidonia.md`, `city-states.md`) |
| **Styxia ↔ Vortex of Genesis** | sea | "The palace that worshiped the ocean, **the sanctuary connected to the Vortex**, was also once the battlefield of the first Flame-Chase…" — Styxia was the ocean-worshipping city; the Vortex is reached by sea. (`build/build_ch6_p6.py`; `major-locations.md`) |
| **Styxia ↔ Kremnos / Aidonia ↔ Vortex / Kremnos ↔ Vortex** | model | The engine's southern sea-cluster (6–8 p). Plausible given the Vortex's sea access. |
| **Aedes Elysiae ↔ the rest** | sea + Veil | Aedes Elysiae is **Outworld**: "protected by the Veil of Evernight and **left behind outside of the rest of the world**"; grain is shipped out **by boat from Voyager's Wharf**; "wheat fields, windmills, and the ocean watch over". (`major-locations.md`, fetched wiki page) |
| **Vortex of Genesis ↔ the rest** | sea | "hidden by the waves"; the sanctuary of the primal Coreflames; the final confrontation with the Flame Reaver takes place there. (`major-locations.md`) |
| **Great Tomb ↔ the world's end** | narrative | "**As I've Written is closely connected to this tomb**" — the tomb stores the pasts of all worlds; the Demiurge (Mem) was imprisoned there. (`build/build_ch7_p6.py`) |

---

## 4. Physical geography (what binds or separates the places)

- **The River of Souls** — the great river and the world's central artery of death:
  - "**The River of Souls surrounding the city-state [Styxia]**… ha[s] been… the
    last reflection in the eyes of the dying." (`hoyolab … dragonbone-city-styxia.md`)
  - Styxia "was originally a coastal city, but long ago, **the River of Souls did
    not flow beneath its bridge**" — the river came later, with disaster.
  - The quest arc: "the heroes' **journey across the River of Souls** toward the
    final confrontation" and "**Zagreus's demigod will become a guide to traverse
    the River of Souls**". (`build/build_ch3_p1.py`, `build/build_ch3_p6.py`)
  - "**Set Sail Upon the River of Souls**" is a quest title; Castorice is the
    "**Daughter of the River of Souls**"; lost souls "remain unable to cross to
    the other shore"; the **Sea of Souls** lies at its end (where the twins of
    Death reunite). → The river *separates the living realm from the nether*, runs
    past/around **Styxia**, and links the snow lands of **Aidonia** and the
    southern sea cluster.
- **The Ocean / sea routes** — Aedes Elysiae (Voyager's Wharf, grain exports by
  boat, sea seals), the Vortex of Genesis ("hidden by the waves", reached by sea),
  Styxia (originally a coastal city), Hysilens (Sea Siren, "Daughter of the Sea").
- **The Veil of Evernight** — seals off Aedes Elysiae from the rest of the world
  ("left behind outside of the rest of the world").
- **The sky** — the Eye of Twilight is a city-state *in the clouds*, once connected
  to Dawncloud (a sky bridge, now removed); the "Dawn Device" holds back the night
  over Okhema; Kephale slumbers on the **Titan Cliff** above Okhema.
- **Mountains & wastes** — Aidonia stands on the **northern snow wasteland**
  ("advanced north… desolate northern wasteland… snow fell relentlessly all year");
  Castrum Kremnos's very name means "cliff" (*krēmnós*).
- **Bridges & gates** — the **Century Gate** (Okhema → Abyss of Fate/Janusopolis);
  the bridge to Kremnos's outer city; a bridge inside Okhema; the bridge under
  which the River of Souls flows in Styxia; the bridge to Dragonbone City from
  Twin Moon Spire; the "Mending Silver Bridge" at Memortis Shore.
- **The black tide** — a creeping "fog"/corruption from beyond the horizon
  ("a threat from beyond the fog") that devoured city after city, leaving only
  Okhema under the Dawn Device's light.

---

## 5. The Flame-Chase Journey route (travel order from the quests)

1. Arrive → **Okhema** (the sanctuary; Aglaea's trust is won).
2. Okhema → **Vortex of Genesis** (the trial/interrogation by Aglaea).
3. Okhema → **Castrum Kremnos** (the fallen mobile fortress; the Nikador war).
4. Kremnos → **Okhema** (return; regroup).
5. Okhema → **Abyss of Fate / Janusopolis** (via the Century Gate; Oronyx's power).
6. (Later) Okhema ↔ **Grove** (research at the Library of Philia; Titan Cliff).
7. Era of Fate: **across the River of Souls** → **Styxia** (the "pivot") → the
   **nether realm** → back to the living.
8. The First Flame-Chase era: the Deliverer arrives in **Janusopolis**, then
   **Okhema**; the first battlefields included the ocean sanctuary tied to the
   **Vortex**.
9. Endgame: **Great Tomb** (the Demiurge/As I've Written), the **Vortex of
   Genesis** (final confrontation with the Flame Reaver), the **Memortis Shore**
   (the Twelve Titans meet the heroes), and **Aedes Elysiae** (awakening after
   Era Nova).

---

## 6. Canon vs. the world engine's model (`src/world/map_data.py`, `databank/world/map.md`)

The engine's graph is **largely consistent** with the canon:

- ✅ Okhema ↔ Dawncloud (0), ↔ Janusopolis (1), ↔ Grove (2), ↔ Kremnos (8),
  ↔ Styxia (9), ↔ Vortex (14), ↔ Aedes (12), ↔ Great Tomb (10) — all justified
  (Okhema is the hub; every quest arc departs from and returns to it).
- ✅ Grove ↔ Great Tomb (2, "a short descent from the Grove").
- ✅ Styxia ↔ Aidonia (3) and the southern sea cluster (Styxia/Aidonia/Kremnos ↔
  Vortex, 6–8) — consistent with the River of Souls and the sea routes.
- ✅ Janusopolis ↔ Aedes (9, coastal road) — plausible; the two most coastal hubs.

**Two canon nuances worth recording (kept as documentation, not graph changes):**

1. **The Vortex of Genesis is effectively one-way** — Okhema's Connections list
   says "(one-way)", and the Vortex is "hidden by the waves" (you arrive by sea;
   there is no road back). The engine's graph is undirected (Dijkstra travel),
   so this is documented here rather than modelled as a directed edge.
2. **A sky bridge once linked Dawncloud ↔ Eye of Twilight** — both directions were
   "removed during 'Dawn, Shine at the World's End'", matching the engine's
   treatment of the Eye as an unreachable ruin on the horizon. If a later story
   era restores it, a direct Dawncloud ↔ Eye edge (high cost) would be canonical.

---

## 7. Sources & method

- **Online wiki** (fetched 2026-08-13 via the MediaWiki API through the local
  proxy + pinned Cloudflare IP): Amphoreus, Okhema, Janusopolis, Castrum Kremnos,
  Styxia, Aidonia, Grove of Epiphany, Aedes Elysiae, Vortex of Genesis, Great
  Tomb, Dawncloud, Eye of Twilight, the Corridor of the Evernight, Moon Veil
  Mountain, Necropolis of the Fallen.
- **Local wiki databank**: `databank/wiki/locations/` (89 pages), incl. the
  official **HoYoLAB "Chronicles of Amphoreus"** essays (e.g. the Dragonbone
  City/Styxia chronicle with the River of Souls lore).
- **Quest dialogues**: `databank/build/*.py` and `databank/missions/*` (Chapters 1,
  3, 5–8) — travel arcs, the Century Gate, the River of Souls crossing, the
  Kremnos journeys.
- **Curated world docs**: `databank/world/{map, city-states, major-locations,
  history, ambient, amphoreus-script}.md` — including the wiki **Connections**
  fields transcribed into `city-states.md` and `major-locations.md`.
- **Forums**: Reddit returned HTTP 403 from this network; not used. HoYoLAB
  chronicles (official) substitute as the authoritative essay-class source.
