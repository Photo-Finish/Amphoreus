# The Keeper of Amphoreus — the Ambient World Director

The little Amphoreus has a quiet stage-manager: a **second intelligence**, the
*Keeper of Amphoreus*, that sets the atmosphere the Heirs live in — but never
what they say or do. The Heirs keep their free will; the Keeper only arranges
the weather, the errands laid at their doors, and the distant news.

## What the Keeper provides (once per in-game day)

- **Weather** — the day's sky over each city. Amphoreus has no rain as we know
  it; its weather is Titan-flavored: light that opens like doorways (Janus),
  veils and grey curtains (Oronyx), golden harvest light (Mnestia), ash and
  long shadows (Nikador, Thanatos).
- **Errands** — for each Heir, one short request the city lays at their door:
  a plea, a duty, a message, an invitation. The Heir may accept, decline, or
  ignore it — that choice is theirs alone.
- **News** — one short line of distant news that reaches every city.

## Design

- The Director is a **separate role** (its own system prompt) on a **separate
  model**: by default the locally-deployed **DeepSeek-R1-Distill-32B**
  (`deepseek-r1-distill:32b`, registered from the LM Studio GGUF files without
  duplicating them — see `tools/register_lmstudio_gguf.py`). Override with
  `python -m src.world.world_engine --ambient-model ...`.
- **Canon-grounded**: the Keeper's prompt embeds `KEEPER_KNOWLEDGE` — the
  city/patron table, the 12-month Light Calendar with its festival seeds, the
  black tide, the Thief Star, and the creatures — so weather, errands, and news
  feel authentically Amphorean. The deterministic fallback uses `MONTH_LORE`
  (month-aware weather) and `CITY_ERRAND` (city-specific duties). Full grounding:
  `databank/world/keeper-knowledge.md`.
- **One LLM call per in-game day** — results are cached by date
  (`world_runtime/ambient_cache.json`), so the world never pays the cost more
  than once per day no matter how often the engine ticks.
- **Deterministic fallback** — if the LLM is unreachable or cannot load (low
  RAM), seasonal weather and routine-flavored errands keep the world moving;
  the engine never stalls.
- The day's stage is stored in the world state and shown to each Heir in their
  perception (weather in their senses, their errand, and the news), and
  rendered in the 🗺️ Map tab of the sanctuary UI.

## Files

- `src/world/ambient.py` — the `AmbientDirector` (Keeper role + fallback).
- `src/world/world_state.py` — ambient storage (`set_ambient`, `ambient_weather`,
  `ambient_errand`, `ambient_news`) and weather in `sensory_text`.
- `src/world/agent.py` — Heirs perceive the day's errand and news.
- `src/world/world_engine.py` — calls the Director once per day and logs the
  Keeper's board to the Chronicle.
- `src/ui_app.py` — the 🗺️ Map tab shows today's sky, news, and errands.
