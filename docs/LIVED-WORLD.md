# Lived world — entities and mechanisms

A catalog for visitors and operators. **Entities** are the furniture of Amphoreus (what is *there*). **Mechanisms** are the verbs of a Light Calendar day (what the world *does* when the engine ticks). Neither is famine, plague, war, storm-as-catastrophe, burial, or a grave as today's work. People here live on.

**How you see them**

- **Visit:** one stage paragraph for *this* place and hour, plus two-to-four people actually here. Not this catalog.
- **Gazette:** a handful of tick facts (“This Hour in the World”) and street encounters.
- **Control Panel / Admin Console:** the full ledger (here / near / elsewhere, flags, residents).

Status is derived from the Light Calendar, the Keeper's sky, and where the body stands — never a second random weather. Mechanisms mutate `world.vivid["lived"]` on each `run_day` tick (after Keeper ambient, before night's early return).

Light Calendar periods: **Entry Hour** (0) · **Lucid Hour** (1) · **Action Hour** (2) · **Parting Hour** (3) · **Curtain-Fall** (4). Rest = Curtain-Fall **or** Entry Hour. Lucid and Action are working hours. Parting is not rest (gates, packing stalls, letters).

---

## Entities (31)

Each entity has a *day-job* (its mechanism as furniture) and a *where*. Presence is **here** / **near** / **distant** from the scene you stand in.

### Always on the stage (sky, time, land)

| Entity | What it does on a day | Where it is local | How the hour changes it |
|---|---|---|---|
| **Dawn Device** | Lights and warms the waking world; people and crops keep time by it. | Felt everywhere | Night (Curtain-Fall, and Evernight's long dark): **withdrawn**, even if today's weather was blazing. Entry (ordinary months): **kindles**. Veil / Month of Evernight: burns dim. Month of Everday or a blazing sky: high and hot by day. Parting: light slants west. |
| **Thief Star** | Marks the night road when the Device withdraws. | Night (and Evernight's leak into day) | Out at Curtain-Fall. Hidden under ordinary day. Oronyx's month: a little darkness even while waking. |
| **Today's sky** | The Keeper's weather — what the body feels outdoors. | Everywhere | Echoes the Keeper's city sky. Night does not invent a second weather; it is night *under* that day's sky. |
| **Wind** | Cools labor, dries cloth, fills a sail, can delay a road. | Everywhere | Windy/wild Keeper text: cloth snaps. Still air: banners hang. Month of Strife: a restless cooling wind, not a storm-entity. Otherwise a mild air. |
| **Earth** | Holds the seed; Georios' gift underfoot. | Everywhere | Cultivation (month 4): turned soil. Reaping (month 8): harvest dust. Else quiet ground. |
| **Harvest** | Fills the granaries; the year is planned around it. | Felt everywhere (work is in the fields) | Month 4 **sowing** (not reaping). Months 5–6 crops drink the light. Month 8 **reaping**. Month 9 granaries remember grain. Else the fields rest — no famine. |
| **Dromases** | Beasts of the road; Georios' vigor on the long haul. | Everywhere; strongest on a journey | On the road: they share it. Cultivation: roads full of them. Action/Parting: they move goods. Else yards and quiet streets. |
| **Road** | Connects cities; feet and wheels wear it. | Everywhere | Underfoot when traveling. Parting Hour: wheels find the gates. Else it waits at the gate. |
| **Letter** | A voice across distance; the roads carry it. | Everywhere | Reports whether unread mail waits. The engine's carrying hour (especially Parting) is more likely to actually send a letter. |
| **Light Calendar hours** | Many people keep the same time. | Everywhere | Always names the current period (Entry, Lucid, Action, Parting, Curtain-Fall). |

### Settlements (hearth, house, square)

Local in city-ish places (Okhema, Dawncloud, Janusopolis, Grove of Epiphany, Castrum Kremnos, Styxia, Aidonia, Aedes Elysiae, Eye of Twilight, and the other mapped towns). Distant on a stretch of open road.

| Entity | What it does on a day | How the hour changes it |
|---|---|---|
| **Hearth** | Cooks, warms, and gathers a household. | Night/rest: hearths hold the houses (day's meal and warmth). Waking: lit for work and food. On the road: the hearth is behind you. **Feeding** (below) records that hearths took today's meal, once per date. |
| **House** | Keeps weather and night off the body. | Inside a city: walls and a roof. On the road: the house is the city left or the one ahead. |
| **The city** | Work, rumor, and many hearths in one place. | Awake in working/Parting hours. Quiets toward sleep at rest. A black-tide surge at this edge: talk and trade thinner — not a feast, not a famine. On the road: the city is ahead or behind. |
| **City water** | Baths, wells, and the day's drink. | Okhema / Eternal Holy City: Marmoreal baths and wells. Other towns: cisterns. On the road: what you carry. |
| **Cloth** | Warmth and work; Mnestia's memory in thread. | Month of Weaving: looms and tongues both carry memory. Else cloth on the body. |
| **Market** | Strangers trade without knowing each other. | **Rest (Entry and Curtain-Fall): stalls down.** Lucid: ordinary trade. Action: fullest square (unless a surge thins it). Parting: packing. Grove: *no* market square (trade lives in the cities). Surge: people buy what they need and keep close. Road: the market is in the city, not on this stretch. |
| **Coin** | Stands in for goods so trade can travel. | Sleeps in purses at night and on the road. Month of Balance: accounts weighed. Month of Fortune: faster hands. Else ordinary square coin. |

### Place-bound land and craft

**Here** only in the matching geography. A Grove Visit cannot grow a sea; Kremnos is the forge, not the teaching hall.

| Entity | What it does on a day | Here in | How the hour changes it |
|---|---|---|---|
| **Grove** | Shade, timber, and scholarship among the trees. | Grove of Epiphany, Radiant Scarwood, Great Tomb, Universal Matrix | Lucid Hour: pages, leaves, quiet study. Else leaf and timber. |
| **Sea** | Fish, trade, and the Ocean's breath at the shore. | Styxia, Aedes Elysiae, Vortex of Genesis, Warbling Shores | Month of Joy: fuller nets. Else shore-trade and fish, not a storm. |
| **Harbor** | Ships meet land; goods and news come ashore. | Same as sea | Night: lamps, hulls at quay. Day: goods and news. |
| **Ship** | Carries people and cargo farther than a road. | Same as sea | Night: hulls at rest. Day: a ship can leave. |
| **River of Souls** | Pale river; boats, hush, a long current. | Styxia, Aidonia, Janusopolis, Sanctum of Prophecy, Warbling Shores | Present as geography and hush — not a door out of life, not burial-work. |
| **Kephale's mountain** | The holy city's wall of stone and stillness. | Okhema, Dawncloud, Eternal Holy City, Demigod Council, Eye of Twilight, Fortress of Dome | Stone and stillness above the holy city. |
| **Gates** | Janus's thresholds — a city opens or closes. | Janusopolis, Okhema, Sanctum of Prophecy, Eternal Holy City | Parting: farewells. Entry: first steps, quietly. Else an ordinary door. |
| **Fields** | Sowing and reaping under Georios. | Aedes Elysiae (and of old) | Cultivation: hands in the soil. Reaping: fields toward gold. Else slower coastal work. |
| **Workshop** | Turns material into tools, cloth, pots. | Okhema, Castrum Kremnos, Eternal Holy City, Bloodbathed Battlefront | Day: hammers and benches. Night: banked. |
| **Forge** | Iron from the earth into useful metal. | Castrum Kremnos, Bloodbathed Battlefront | Night: banked, iron waits for Action. Month of Strife: forges ring for walls and tools. Else ordinary ore-to-metal. |
| **Scroll** | Speech that outlives the speaker. | Grove of Epiphany, Okhema, Radiant Scarwood, Eternal Holy City | Lucid Hour: a good hour to open one. Else on the shelf or in someone's hands. |
| **Teaching hall** | Hands a craft or a canon to the next generation. | Grove of Epiphany, Radiant Scarwood | Lucid/Action: at work. Night: dark, resumes with Lucid. |
| **Healer's house** | Tends hurt, fever, and weariness — comfort in a life that goes on. | Grove of Epiphany, Okhema, Dawncloud, Radiant Scarwood | Open for rest and balm. Not a door out of life. |
| **Shrine** | Offerings and thanks in stone. | Okhema, Janusopolis, Dawncloud, Eternal Holy City, Demigod Council | Entry: prayers (thanks, not grave-work). Else offerings already given. |

### Not in the catalog (on purpose)

Famine, plague, war, storm-as-entity, grave, burial, dying as today's work. The black tide remains the existing journey-mode pressure: it **thins** a square; it does not invent hunger. Canon places (Aidonia, the Nether, the River) may exist as geography and remembrance.

---

## Mechanisms (17)

These **run on the world-engine tick**. They write flags and a few chronicle facts so Visit, Gazette, and residents follow the same hour. Feeding and growing mutate **once per Light Calendar date**. The day's civic pulse is persisted from Okhema so a visitor on the road does not shut every stall in Amphoreus.

| # | Mechanism | Verb | When it is doing the work | What the tick actually changes |
|---|---|---|---|---|
| 1 | **Keeping time** | Many people keep the same Light Calendar hour. | Always | Names the period. Everyone (Heirs, residents, Gazette) is on that clock. |
| 2 | **Lighting and withdrawing** | The Dawn Device lights the waking world and withdraws at night. | Always (state changes) | Flag `lighting`: withdrawn / veiled / blazing / kindling / ordinary. `device_withdrawn` at night. Curtain-Fall cannot be “high and hot.” |
| 3 | **Sheltering** | A house keeps weather and night off the body; the road does not. | Always | Flag `sheltering`: `inside` in a city, `road` while traveling. Visit will not claim you are indoors on the miles. |
| 4 | **Feeding** | Hearths take a meal from what harvest and bakers already hold. | Once per **date** | Writes `hearths_fed` for Okhema, Dawncloud, Janusopolis, Grove, Great Tomb, Kremnos, Styxia, Aidonia, Aedes Elysiae, Vortex of Genesis, Eye of Twilight. Chronicle: hearths took today's meal. No famine. |
| 5 | **Growing** | Fields sow or reap by the month — never both at once. | Once per **date** | `harvest_phase`: sowing (4) / growing (5–6) / reaping (8) / granary (9) / fallow. Cultivation cannot “come in.” Reaping can. |
| 6 | **Carrying** | Roads, dromases, ships, and letters move what does not walk itself. | Anyone on the road, or Parting Hour | Flag `carrying`. Raises letter chance at Parting; lowers it at rest. Road vignette adds a sheltering/carrying clause. |
| 7 | **Trading** | The square trades in waking hours; night and rest pack the stalls. | Lucid & Action in market cities | `market_open` only if not rest, not Grove, not on the road. Action = fullest (unless surge → `market_thin`). Parting = `market_packing`. Rest = stalls down. |
| 8 | **Making** | Workshop, forge, and loom work by day and bank at night. | Lucid & Action | `making` in working hours. `forge_ringing` only at Action in Kremnos/Battlefront. Night: banked. |
| 9 | **Gathering** | A city is awake, or it quiets toward sleep. | Lucid, Action, Parting (not rest, not the road) | `gathering` / `npc_abroad`. Street residents are out. Copilot “is about” stroll and small NPC arcs **wait at rest**. |
| 10 | **Crossing** | Gates and harbors take arrivals and farewells, especially at Parting. | Parting Hour | `crossing`. Harbor wording only at the sea. Grove has no harbor crossing. |
| 11 | **Washing and drinking** | Wells, baths, and cisterns hold the day's water. | Waking hours in a city | `washing` in settlements, not at rest, not on the road. Okhema names the Marmoreal baths. |
| 12 | **Cooling and drying** | Wind cools labor and dries cloth — weather, not catastrophe. | Windy/wild sky, or Month of Strife | `cooling`. Dries a sleeve; does not wreck a ship. |
| 13 | **Teaching** | The Grove hands a craft or a canon on, strongest at Lucid Hour. | Lucid & Action (felt in the Grove) | World flag in working hours; the *here* fact is Grove/teaching hall. Rest: hall dark. |
| 14 | **Tending** | A healer's house offers rest and balm. | When you are in a healer city | `tending` in Grove, Okhema, Dawncloud, Scarwood. Comfort; not a door out of life. |
| 15 | **Offering** | Shrines take thanks and prayers. They are not grave-work. | Entry (kindling prayers) and working hours at a shrine | `offering` in Okhema, Janusopolis, Dawncloud, Eternal Holy City, Demigod Council. No burial. |
| 16 | **Remembering without burying** | Scroll, letter, and weaving keep a voice without a burial. | Lucid Hour, Month of Weaving, or a scroll-city | `remembering`. Memory on a shelf, a page, a loom — not a grave. |
| 17 | **Resting** | Curtain-Fall and Entry Hour: the city rests; the Thief Star keeps watch. | Period 0 or 4 | `resting`. Heirs skip decisions (existing rest). Market closed. Forge not ringing. Device withdrawn at Curtain-Fall; may **kindle** at Entry while the city is not yet at work. |

### What cannot be true at once

| If this is true | This cannot also be true |
|---|---|
| Curtain-Fall | Device high and hot; market busiest; forge in full ring |
| On the road | Sheltering inside; “the square is yours” |
| Grove / inland | Sea or harbor *here*; a busy market square |
| Cultivation (month 4) | Harvest “comes in” |
| Veiled sky | Unveiled blazing Device in daylight |
| Tide at this edge | Feast-busy market |
| Entry Hour (rest) | Market open for business |

---

## Residents (how they use the list)

About 110 templated street people (plus Copilot's six named living NPCs: Bartholos, Seliose, Noldus, Researcher Eikura Shuu, Mem, Theodosia) take their hour from these mechanisms: hearths at rest, stalls at Lucid/Action, gates at Parting, Grove students with no harbor-fishers. They can nod to a Heir who is actually in their city. Visit offers two-to-four people *here this hour*, not the census.
