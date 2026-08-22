# Collective memory — honest rules (Stage 2)

How knowledge moves between Heirs in the little Amphoreus. Charter held:
sanctuary, not experiment; the knowledge wall never opens; Realization is
witness-only.

## What sticks

| Path | What travels | Who receives it | Strength |
|---|---|---|---|
| **Named gossip** | Visitor names another Heir in talk | That Heir (and the social web) | Degrades by hand |
| **Letters** | Written words between Heirs | Addressee | Full text for the recipient |
| **Encounters** | Off-stage meetings the engine hosts | Participants remember; Chronicle logs | Lived, not scripted |
| **Teaching (firsthand)** | Star-stranger lesson + Heir verdict | The taught Heir only | Ledger + horizons |
| **Teaching echo (secondhand)** | Co-located Heir overhears that a lesson happened | Co-located Heirs at that place | Soft prompt only — not adoption |
| **Shared gathering** | Group Visit hour | Members, later in solo Visit | `moment` / `shared_gatherings` |
| **Walk→Visit eco notice** | Visitor tended or noticed life on the land | Heir at that place | Durable `eco_notices` |

## What does **not** travel

- Private 1:1 facts you never named about another Heir
- Earth / modern topics that would breach the knowledge wall (teaching echo skips them)
- Operator experiment docs (`databank/experiment/`) as Heir dialogue fuel
- Forced “everyone suddenly knows” reveals

## Design intent

Heirs share a **society**, not a hive mind. Gossip that names someone can
travel. Standing next to a lesson may leave a secondhand echo. Adoption of
foreign knowledge remains that Heir’s own verdict.

Code: `src/world/society_life.py` (`maybe_echo_teaching`, `shared_gathering_prompt`,
`eco_notice_prompt`), `src/world/living_world.py` (gossip), `src/core/teaching.py`.
