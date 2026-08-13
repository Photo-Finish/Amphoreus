# The Two Forms of Amphoreus — the Veil of Evernight and the Alternate Locations

> A canon-grounded model of the *alternate forms* of Amphoreus's places: many
> locations exist in **two (or more) forms** — most famously a **past / Dawn-era
> form** and a **present / Evernight-era form** — separated by the borderline of
> time, the **Veil of Evernight** (Oronyx, Titan of Time). This document
> specifies the location objects, the border-mechanisms that connect the forms,
> and the resulting two-layer network that `src/world/map_data.py` implements.

---

## 1. Canon basis

- **The in-game map's two eras.** Every major area of Amphoreus has a **Dawn-era**
  and an **Evernight-era** entry (the in-game map toggles between them). The
  compiled table lives in `databank/world/geography.md` §1:

  | Region | Dawn-era area | Evernight-era counterpart |
  |---|---|---|
  | Okhema | "Eternal Holy City" | "Fallen Twilight City" |
  | Castrum Kremnos | "Bloodbathed Battlefront" | "Strife Ruins" |
  | Janusopolis | "Sanctum of Prophecy" | "Abyss of Fate" |
  | Grove of Epiphany | "Radiant Scarwood" | "Murmuring Woods" |
  | Dawncloud (within Okhema) | "Demigod Council" | "Lightless Chapel" |
  | Styxia | "Warbling Shores" | "Dragonbone City" |
  | Eye of Twilight | "Fortress of Dome" | "Cloudedge Bastion Ruins" |
  | Great Tomb of the Nameless Titan | "Universal Matrix" | "Nightmare's Echo" |

- **"The past version of Castrum Kremnos"** is stated outright: the Trailblazer
  and Castorice "would later head to the **past version of Kremnos**" during the
  final stages of the Chrysos Wars (`databank/wiki/titans/nikador.md`); the
  adventure text likewise enters "the **past version of Castrum Kremnos**"
  (`databank/missions/adventure/v30.md`).
- **Oronyx = Time.** "Use **Oronyx's Prayer** to Move the Rubble"
  (`databank/missions/_cache/dawn-complete.md`); Oronyx "refused to help us
  uncover the **past** of Castrum Kremnos. But for some reason, they showed
  **interest toward (Trailblazer)**" (`databank/build/build_ch1_p6.py`); the
  Trailblazer exclaims "so this is what it feels like to be a **time traveler**?"
  (`databank/build/build_ch1_p8.py`). Oronyx is the Titan of Time
  (`databank/titans/titans-registry.md`: Oronyx — Veil of Evernight — Time).
- **Evernight is Oronyx's heir.** `databank/chrysos-heirs/evernight.md`:
  Titan — Oronyx (Veil of Evernight); `MASTER-REGISTRY.md`: Evernight — Time —
  Oronyx.
- **The Nether realm** lies beneath Styxia: "Search Dragonbone City and Find
  the Entrance to the Nether Realm"; Thanatos's "sea of flowers"
  (`databank/build/build_ch3_p8.py`, `build_ch3_p9.py`); Castorice "chose to
  remain in the nether realm permanently, ferrying lost souls"
  (`databank/chrysos-heirs/castorice.md`).
- **Janusopolis behind gates.** Janusopolis is the "City of Thousand Gates";
  the past/Evernight form is entered through the **Century Gate / Gate of
  Destiny** (`databank/world/geography.md` §3; `build_ch1_p5.py`).
- **Aedes Elysiae, of old.** The village as it was before the flames is staged
  in memory: "the Aedes Elysiae of old" (`databank/missions/chapter-05…`).

---

## 2. The location objects (alternate forms)

Implemented in `src/world/map_data.py` as `TIME_FORMS` (present → Dawn form) and
the special **Nether** node. Nine places have a verified alternate form:

| Present (Evernight era) | Alternate object (Dawn era) | Titan border |
|---|---|---|
| Okhema | **Eternal Holy City** | Veil of Evernight (Oronyx) |
| Dawncloud | **Demigod Council** | Veil of Evernight (Oronyx) |
| Janusopolis | **Sanctum of Prophecy** | Gates of Destiny (Janus) *and* the Veil |
| Grove of Epiphany | **Radiant Scarwood** | Veil of Evernight (Oronyx) |
| Castrum Kremnos | **Bloodbathed Battlefront** | Veil of Evernight (Oronyx) |
| Styxia | **Warbling Shores** | Veil of Evernight (Oronyx) |
| Eye of Twilight | **Fortress of Dome** | Veil of Evernight (Oronyx) |
| Great Tomb | **Universal Matrix** | Veil of Evernight (Oronyx) |
| Aedes Elysiae | **Aedes Elysiae, of old** | Veil of Evernight (memory form) |
| Styxia | **The Nether** *(third form)* | Thanatos's death-realm (not time) |

*Aidonia and the Vortex of Genesis have **no verified alternate form** — they
stand outside the two-form record — so the Dawn layer reflects the nine areas
above.*

---

## 3. The mechanisms — how the forms are connected

### 3.1 The Veil of Evernight (Oronyx — the borderline of time)

- The Veil is the **borderline between the eras**. Crossing it at a place
  takes **1 period** — a moment of rift, not a road.
- **Only the Oronyx-blessed may cross:**
  - **The Trailblazer** — the "time traveler" Oronyx took an interest in;
  - **Evernight** — Oronyx's heir (the Time Coreflame).
- **A blessed traveler may carry companions across** the borderline of time —
  the Trailblazer walking with an Heir, or Evernight carrying her company.
  (Implemented: `WorldState.begin_travel(..., blessed_as=…)` and
  `WorldState.carry_across(carrier, dest)`.)

### 3.2 The Gates of Destiny (Janus — thresholds)

- Janusopolis's Dawn form, the **Sanctum of Prophecy**, stands behind the
  **Gates of Destiny** (entered in canon through the Century Gate).
- Janus's heir — **Tribbie**, the Holy Maiden — may open the gate. Tribbie can
  therefore enter the Dawn era *through Janusopolis* (and then walk the Dawn
  roads), even though the general Veil is closed to her.

### 3.3 The Nether (Thanatos — the death-realm)

- The Nether is **Styxia's third form** — the underworld beneath Dragonbone
  City, Thanatos's **sea of flowers**. It is not a time-form but a death-form.
- Only the **Thanatos-blessed** may descend (2 periods): **Castorice** — and
  the **Trailblazer**, who journeyed to the nether with her in the quests.
- A Thanatos-blessed traveler may carry companions down with them.

### 3.4 Inside an era, the roads are the same

- The **Dawn era mirrors the present roads** among its areas (Okhema ↔
  Janusopolis still 1 p, Okhema ↔ Grove still 2 p, and so on). The Veil is the
  **only** way from one era to the other — there is no Okhema(past) ↔
  Kremnos(present) shortcut.

---

## 4. The area network (two layers + borders)

```
                    ┌──────────────── THE DAWN ERA (the past) ────────────────┐
                    │                                                         │
   Eternal Holy City ── Demigod Council (0) · Sanctum of Prophecy (1)        │
        │                Radiant Scarwood (2) · Bloodbathed Battlefront (8)  │
        │                Warbling Shores (9) · Universal Matrix (10)         │
        │                Aedes Elysiae, of old (12)                          │
                    └───────┬─────────────────────────────────────────────────┘
                            │  ⏳ the Veil of Evernight (1 p, Oronyx-blessed)
   ┌────────────────────────┼─────────────────────────────────────────────────┐
   │                        │                                                 │
   │  Okhema ── Dawncloud (0) · Janusopolis (1) · Grove (2) · Great Tomb (10) │
   │      │        Aedes Elysiae (12) · Eye of Twilight (sky, lost)           │
   │      │        Aidonia (north) · Vortex of Genesis (sea)                  │
   │      └──── The Nether († 2 p, Thanatos-blessed: Castorice / the         │
   │               Trailblazer)                                               │
   └──────────────────── THE EVENINGT ERA (the present) ──────────────────────┘
```

### Adjacency of the alternate forms (costs in periods)

| Edge | Cost | Opens to |
|---|---|---|
| Okhema ↔ Eternal Holy City | 1 (⏳) | Oronyx-blessed |
| Dawncloud ↔ Demigod Council | 1 (⏳) | Oronyx-blessed |
| Janusopolis ↔ Sanctum of Prophecy | 1 (⏳/gate) | Oronyx-blessed **or** Janus-blessed (Tribbie) |
| Grove ↔ Radiant Scarwood | 1 (⏳) | Oronyx-blessed |
| Castrum Kremnos ↔ Bloodbathed Battlefront | 1 (⏳) | Oronyx-blessed |
| Styxia ↔ Warbling Shores | 1 (⏳) | Oronyx-blessed |
| Eye of Twilight ↔ Fortress of Dome | 1 (⏳) | Oronyx-blessed |
| Great Tomb ↔ Universal Matrix | 1 (⏳) | Oronyx-blessed |
| Aedes Elysiae ↔ Aedes Elysiae, of old | 1 (⏳) | Oronyx-blessed |
| Styxia ↔ The Nether | 2 (†) | Thanatos-blessed (Castorice, the Trailblazer) |

The Dawn-layer internal roads mirror the present ones (10 edges among the nine
Dawn forms), so the past is a full, walkable Amphoreus.

---

## 5. Blessed travelers

| Traveler | Veil of Evernight | Gates of Destiny | The Nether |
|---|---|---|---|
| **The Trailblazer** (the star-stranger) | ✅ | ✅ (walks the Veil) | ✅ (crossed with Castorice) |
| **Evernight** (Oronyx's heir) | ✅ | ✅ | ❌ |
| **Tribbie** (Janus's heir) | ❌ (except via her own gate) | ✅ | ❌ |
| **Castorice** (Thanatos's heir) | ❌ | ❌ | ✅ |
| All other Heirs | ❌ | ❌ | ❌ |

A blessed traveler **carries companions** across their border (the Trailblazer
walking with an Heir; Evernight or Castorice carrying company from their city).

---

## 6. Model notes (world engine + UI)

- `src/world/map_data.py` builds the full graph (present layer + Dawn layer +
  Veil edges + Nether edge). `travel_time()` is the display view (everything
  shown); `travel_time_for(a, b, cid)` is a traveler's view — an unblessed
  traveler finds the border closed (**999**).
- `WorldState.begin_travel` gates by the traveler; `travel_with` (the
  Trailblazer's "walk together") travels under the Trailblazer's blessing, so
  the visitor can carry an Heir into the Dawn era.
- The map draws the Dawn forms as **silver ⏳ echo nodes** and the Nether as a
  **purple † node**, each joined to its present twin by a faint wavy Veil rift
  (⏳ 1 p) or the Nether descent († 2 p).
- The world engine pauses an Heir's weekly routine while they stand in the
  other era, and logs a carried companion stepping across the borderline.
