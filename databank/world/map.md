# The Map of Amphoreus

> Amphoreus is a wide world. The Heirs do not live in one city — they are spread
> across city-states, groves, fortresses, snow plains and a village frozen in
> time. This document is the geographic model the world engine lives by: the
> places, the roads between them, and how long the commuting actually takes.
>
> Travel is measured in **Light-Calendar periods**. There are **five periods in a
> day** (Entry, Lucid, Action, Parting, Curtain-Fall), so a journey of 5 periods
> is a full day on the road.

---

## The Places

| Place | Character | Region / Notes |
|---|---|---|
| **Okhema** | "Eternal Holy City" | The sanctuary city beneath Kephale; the council seat of the Heirs. **Aglaea, Cerydra, Hysilens, Cipher, Evernight and Dan Heng live here.** |
| **Dawncloud** | "Demigod Council" | The council seat **within** Okhema (travel time 0 — it is part of the same city). |
| **Janusopolis** | "City of Thousand Gates" | The twin city of thresholds. **Tribbie** lives here. |
| **Grove of Epiphany** | "Home of Sages" | The scholar's grove. **Anaxa and Hyacine** live and work here. |
| **Great Tomb** | "Universal Matrix" | The deep ruin of all worlds, a short descent from the Grove. |
| **Castrum Kremnos** | "Capital of Might" | The mobile fortress of the spear. **Mydei** holds it. |
| **Styxia** | "Pearly Shores" | The city by the River of Souls, where the dead are remembered. |
| **Aidonia** | "Snow City" | The frozen kingdom of death in the **northern snow wasteland**. **Castorice** lives here. |
| **Aedes Elysiae** | the Deliverer's village | A remote village beyond the **Veil of Evernight**, reached by sea (Voyager's Wharf). **Phainon and Cyrene** live here. |
| **Vortex of Genesis** | sacred nexus | The hidden sanctuary of the primal Coreflames, reached by sea. |
| **Eye of Twilight** | "Sky Castrum" | The **fallen sky castrum**, high above Okhema; a ruin — its sky bridge to Dawncloud is lost. |

---

## The Roads and Commuting Times

Each number is the travel time in **periods** between two directly connected
places (undirected). 0 means *same city*; 5 periods = a full day.

> **The lay of the land** (see the 🗺️ Map tab and `world/geography.md` §3.1 for the
> concrete adjacency matrix): **Okhema** is the hub, its twin **Janusopolis** a short
> road east and the **Grove** a half-day west. **Aidonia** lies in the **northern
> snow wasteland**; the **River of Souls** runs from **Styxia** up into the northern
> snows. The **Eye of Twilight** is a **fallen sky castrum above Okhema** — its sky
> bridge to **Dawncloud** (the council seat in the clouds) is lost, so it has no
> road. The **Vortex of Genesis** is reached one-way by sea; **Aedes Elysiae** lies
> beyond the Veil of Evernight, served by Voyager's Wharf.

### Direct roads (periods)

| Road | Time |
|---|---|
| Okhema ↔ Dawncloud | **0** (same city) |
| Okhema ↔ Janusopolis | **1** |
| Okhema ↔ Grove of Epiphany | **2** |
| Okhema ↔ Castrum Kremnos | **8** |
| Okhema ↔ Styxia | **9** |
| Okhema ↔ Aedes Elysiae | **12** |
| Okhema ↔ Great Tomb | **10** |
| Okhema ↔ Vortex of Genesis | **14** |
| Janusopolis ↔ Aedes Elysiae | **9** |
| Grove of Epiphany ↔ Great Tomb | **2** |
| Grove of Epiphany ↔ Castrum Kremnos | **6** |
| Styxia ↔ Aidonia | **3** |
| Styxia ↔ Vortex of Genesis | **6** |
| Castrum Kremnos ↔ Vortex of Genesis | **8** |
| Aidonia ↔ Vortex of Genesis | **8** |

*The Eye of Twilight has **no road** in the present era — its only link was the
sky bridge to Dawncloud (the council seat), destroyed in "Dawn, Shine at the
World's End."*

### Longest journeys (shortest path, in days)

| From | To | Periods | Days |
|---|---|---|---|
| Okhema | Aedes Elysiae | 10 | **2** |
| Okhema | Castrum Kremnos | 8 | **2** |
| Okhema | Styxia | 9 | **2** |
| Okhema | Aidonia | 12 | **3** |
| Okhema | Vortex of Genesis | 14 | **3** |
| Okhema | Great Tomb | 10 | **2** |
| Janusopolis | Aedes Elysiae | 9 | **2** |
| Aedes Elysiae | Castrum Kremnos | 12 | **3** |

---

## What the commuting means for the Heirs

- **The Okhema circle** (Aglaea, Cerydra, Hysilens, Cipher, Evernight, Dan Heng)
  live in the same city — they cross paths daily, at the council, the market, the
  baths. This is by design: they **work together**.
- **The scholars of the Grove** (Anaxa, Hyacine) live and work together — they
  meet every day.
- **The two souls of Aedes Elysiae** (Phainon, Cyrene) share the same village —
  they are together most days, and Phainon's schedule carries him to Okhema only
  mid-week (a two-day road each way).
- **Tribbie** (Janusopolis), **Mydei** (Castrum Kremnos) and **Castorice**
  (Aidonia) live apart from everyone else. Meeting any of them means **days on
  the road** — so it happens rarely, and only on purpose.

The world engine honours all of this: a Heir who decides to travel sets out on
the road and is *physically absent* for the whole journey — they appear in no
city, they meet no one, until they arrive.

---

## See also

- `world/geography.md` — the researched determination of how Amphoreus's locations
  interconnect (areas, the evidence-based connection matrix, physical geography,
  the Flame-Chase Journey route, and canon-vs-model notes)
- `src/world/map_data.py` — the machine-readable graph (positions, routes, travel times)
- `src/world/schedules.py` — the individual weekly routines of the Heirs
- `world/calendar.md` — the Light Calendar (periods, weeks, months)
- `world/city-states.md` — the lore of the six city-states
