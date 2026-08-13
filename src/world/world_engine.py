"""
World Engine — the daemon of the little Amphoreus.

It is a pure host: it advances the Light Calendar, wakes the Heirs according
to the rhythms of the day, and lets each Heir decide — spontaneously, in their
own voice — what they do. Encounters between Heirs who choose to be together
unfold as free dialogue. The engine never authors an action or an outcome.

Usage:
    python -m src.world.world_engine --interval 900     # run continuously
    python -m src.world.world_engine --once             # run a single day
    python -m src.world.world_engine --stop             # stop the daemon
    python -m src.world.world_engine --status           # show state
"""

import argparse
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# The Chronicle and status lines use emoji / non-ASCII text; make sure they
# print correctly regardless of the Windows console codepage.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.character_loader import CharacterLoader
from src.core.llm_client import LLMClient
from src.core.memory_store import MemoryStore
from src.world.world_state import WorldState, PERIODS_PER_DAY
from src.world import world_events as wev
from src.world.agent import HeirAgent
from src.world.ambient import AmbientDirector
from src.world.chronicle import Chronicle


class WorldEngine:
    """Hosts the little Amphoreus."""

    def __init__(
        self,
        characters_dir: str = "src/characters",
        llm_model: str = "qwen2.5:14b-instruct",
        llm_base_url: str | None = None,
        llm_api_key: str | None = None,
        ambient_model: str | None = None,
        memory_root: str = ".",
        state_path: str = "world_runtime/world_state.json",
        chronicle_path: str = "world_runtime/chronicle",
        stop_path: str = "world_runtime/stop.flag",
        seed: int | None = None,
    ):
        self.loader = CharacterLoader(characters_dir)
        self.llm = LLMClient(
            model=llm_model,
            base_url=llm_base_url,
            api_key=llm_api_key,
            temperature=0.9,
            max_tokens=160,
        )
        # The Keeper of Amphoreus — a separate role on a SEPARATE model (by
        # default the local DeepSeek-R1-Distill-32B, registered from the LM
        # Studio files; override with --ambient-model). It sets weather,
        # errands, and news each day. If the model cannot load (RAM), the
        # director falls back to deterministic seasonal weather automatically.
        self.director = AmbientDirector(
            model=ambient_model or "deepseek-r1-distill:32b",
            base_url=llm_base_url,
            api_key=llm_api_key,
        )
        self.memory = MemoryStore(memory_root)
        self.world = WorldState(state_path)
        self.chronicle = Chronicle(chronicle_path)
        self.stop_path = stop_path
        self.agents: Dict[str, HeirAgent] = {
            cid: HeirAgent(cid, self.loader, self.llm, self.memory, self.world)
            for cid in self.loader.list_characters()
        }
        if seed is not None:
            random.seed(seed)

    # ------------------------------------------------------------------ #
    def _name_of(self, character_id: str) -> str:
        try:
            return self.agents[character_id].name
        except Exception:
            try:
                return self.loader.load(character_id)["meta"]["name"]
            except Exception:
                return character_id

    def _title_of(self, character_id: str) -> str:
        """A short role/title for the Ambient Director's errand grounding."""
        try:
            card = self.loader.load(character_id)
            titles = (card.get("identity") or {}).get("titles") or []
            if titles:
                return titles[0]
            return (card.get("meta") or {}).get("name", character_id)
        except Exception:
            return character_id

    # ------------------------------------------------------------------ #
    # Life of one day
    # ------------------------------------------------------------------ #
    def run_day(self) -> List[str]:
        """Advance one day and let the Heirs live it. Returns chronicle lines."""
        # Advance a full day + one period, so the hour of the day cycles.
        self.world.clock.advance(PERIODS_PER_DAY + 1)
        clock = self.world.clock
        time_str = clock.format_short()
        lines: List[str] = []

        # Travellers advance one day on the road; arrivals are logged.
        for cid, dest in self.world.advance_travel():
            name = self._name_of(cid)
            arrived = f"{time_str} — {name} arrives in {dest} after days on the road."
            lines.append(arrived)
            self.chronicle.append({"time": time_str, "text": arrived})
            self.world.add_event(arrived)
            self.agents[cid].remember(
                f"{time_str} — I arrived in {dest} after a long journey.", importance=2
            )

        # The Keeper sets the day's stage — weather, errands, news (cached by
        # date, so this is one LLM call per in-game day at most).
        heirs_info = {
            cid: {
                "name": self._name_of(cid),
                "home": self.world.location_name(cid),
                "title": self._title_of(cid),
            }
            for cid in self.agents
        }
        ambient = self.director.daily(self.world.clock, heirs_info)
        self.world.set_ambient(ambient)
        news = (ambient or {}).get("news", "")
        if news:
            board = f"{time_str} — The Keeper sets the day: {news}"
            lines.append(board)
            self.chronicle.append({"time": time_str, "text": board, "kind": "ambient"})
            self.world.add_event(board)

        # The living texture: a black-tide surge may stir (journey mode), the
        # cities' named residents go about their days, and a letter may travel
        # between distant Heirs.
        lines.extend(self._world_texture(time_str))

        # The Heirs go about their usual routines — the map reflects where they
        # actually are right now, not just where they live. Travellers stay on
        # the road (their location is only updated on arrival).
        for cid in self.agents:
            if self.world.is_traveling(cid):
                continue
            try:
                self.world.agent_location[cid] = self.world.scheduled_place(cid)
            except Exception:
                pass

        if clock.is_rest_time():
            night = (
                f"{time_str} — The city rests. Only the Thief Star wanders the sky. "
                "The Heirs sleep, and their days wait for the dawn."
            )
            self.chronicle.append({"time": time_str, "text": night})
            self.world.add_event(night)
            self.world.save()
            return [night]

        # Active hour — every Heir decides freely (unless they are on the road).
        order = list(self.agents.keys())
        random.shuffle(order)
        for cid in order:
            agent = self.agents[cid]
            try:
                if self.world.is_traveling(cid):
                    info = self.world.travel_info(cid)
                    companion = ""
                    if self.world.is_accompanied(cid):
                        companion = " The star-stranger walks beside them."
                    line = (
                        f"{time_str} — {agent.name} is on the road to {info['to']}, "
                        f"{info['remaining_days']} day(s) of travel remain."
                        f"{companion}"
                    )
                    lines.append(line)
                    self.chronicle.append({"time": time_str, "text": line})
                    continue
                decision = agent.decide()
                agent.act(decision)
                if self.world.is_traveling(cid):
                    info = self.world.travel_info(cid)
                    companion = ""
                    if self.world.is_accompanied(cid):
                        companion = " The star-stranger travels with them."
                    line = (
                        f"{time_str} — {agent.name} sets out for {info['to']} "
                        f"({info['remaining_days']} day(s) on the road): {decision['action']}"
                        f"{companion}"
                    )
                    agent.remember(
                        f"{time_str} — I set out for {info['to']}. {decision['action']}",
                        importance=2,
                    )
                else:
                    loc = self.world.location_name(cid)
                    line = f"{time_str} — {agent.name} at {loc}: {decision['action']}"
                    agent.remember(
                        f"{time_str} — I was at {loc}. {decision['action']}", importance=1
                    )
                lines.append(line)
                self.chronicle.append({"time": time_str, "text": line})
            except Exception as e:
                lines.append(f"{time_str} — {agent.name} (the world paused for a moment: {e})")

        # Encounters: Heirs who chose to be together may speak — freely.
        lines.extend(self._run_encounters(time_str))

        # Long-term work: the Heirs' life projects advance, milestones logged.
        for milestone in wev.advance_projects(self.world):
            mline = f"{time_str} — {milestone}"
            lines.append(mline)
            self.chronicle.append({"time": time_str, "text": mline, "kind": "project"})
            self.world.add_event(milestone)

        self.world.save()
        return lines

    def _world_texture(self, time_str: str) -> List[str]:
        """Surges, city residents, and letters — the daily texture of the world."""
        lines: List[str] = []
        # 1) The black tide may stir along the edge cities (journey mode only).
        surge = wev.maybe_surge(self.world)
        if surge:
            sline = f"{time_str} — ⚠️ {wev.surge_text(self.world)}"
            lines.append(sline)
            self.chronicle.append({"time": time_str, "text": sline, "kind": "surge"})
            self.world.add_event(sline)
            # the surge darkens the Keeper's weather
            weather = self.world.ambient.setdefault("weather", {})
            for city in surge.get("cities", []):
                weather[city] = (weather.get(city) or "clear") + ", and the black tide darkens the sky"
        wev.advance_surge(self.world)
        # 2) A named resident is seen in one of the cities (alive NPCs only).
        if self.world.ambient.get("news", "") and random.random() < 0.5:
            npc = random.choice(wev.NPCS)
            fline = (f"{time_str} — In {npc['city']}, {npc['name']} is about — "
                     f"{npc['flavor']}")
            lines.append(fline)
            self.chronicle.append({"time": time_str, "text": fline, "kind": "flavor"})
        # 3) Sometimes a letter travels between distant Heirs.
        if random.random() < 0.3:
            letter = self._compose_letter(time_str)
            if letter:
                lline = (f"{time_str} — A letter travels from {letter['from_name']} "
                         f"to {letter['to_name']}: \"{letter['text'][:120]}\"")
                lines.append(lline)
                self.chronicle.append({"time": time_str, "text": lline, "kind": "letter"})
                self.world.add_event(lline)
        return lines

    def _compose_letter(self, time_str: str) -> Optional[dict]:
        """A letter between two Heirs who are apart (canon-relation or bonded)."""
        import random as _r
        ids = list(self.agents)
        _r.shuffle(ids)
        for a in ids:
            for b in ids:
                if a == b:
                    continue
                if self.world.location_name(a) == self.world.location_name(b):
                    continue  # they can just talk
                if wev.relationship_delta_of(self.world, a, b) == 0:
                    continue  # no established bond worth a letter yet
                text = (f"I think of you often. When the road is long, "
                        f"your words are company. — {self._name_of(a)}")
                entry = wev.compose_letter(self.world, a, b, text)
                # both remember it
                self.agents[a].remember(
                    f"{time_str} — I wrote to {self._name_of(b)}.", importance=2)
                self.agents[b].remember(
                    f"{time_str} — A letter arrived from {self._name_of(a)}.", importance=2)
                wev.adjust_relationship(self.world, a, b, 1)
                return entry
        return None

    def _run_encounters(self, time_str: str) -> List[str]:
        lines: List[str] = []
        locations = set(self.world.agent_location.values())
        for loc in locations:
            present = self.world.agents_at(loc)
            if len(present) < 2:
                continue
            group = [self.agents[cid] for cid in present]
            # A free exchange: each speaks in turn, spontaneously, a few rounds.
            transcript: List[str] = []
            rounds = 2
            for _ in range(rounds):
                random.shuffle(group)
                for agent in group:
                    if len(transcript) >= 6:
                        break
                    try:
                        reply = agent.react(transcript[-3:])
                        name = agent.name
                        transcript.append(f"{name}: {reply}")
                    except Exception:
                        continue
            if len(transcript) >= 2:
                header = f"{time_str} — At {loc}, words passed between the Heirs:"
                lines.append(header)
                self.chronicle.append({"time": time_str, "text": header, "kind": "encounter"})
                for turn in transcript[:6]:
                    lines.append(f"    {turn}")
                    self.chronicle.append({"time": time_str, "text": turn, "kind": "encounter"})
                # They remember the exchange
                for agent in group:
                    others = " · ".join(
                        t for t in transcript if not t.startswith(agent.name + ":")
                    )
                    if others:
                        agent.remember_encounter("the other Heirs", others[:240])
                # The living web: what they shared becomes rumour between them,
                # their bonds shift a little, and each keeps a cross-memory of
                # the others' words.
                for agent in group:
                    for other in group:
                        if other is agent:
                            continue
                        wev.spread_rumors(self.world, agent.character_id, other.character_id)
                        wev.adjust_relationship(self.world, agent.character_id, other.character_id, 1)
                    cross = [t for t in transcript if not t.startswith(agent.name + ":")]
                    if cross:
                        who = ", ".join(t.split(":")[0] for t in cross[:3])
                        agent.remember(
                            f"{time_str} — In my meeting with the others, {who} spoke "
                            f"with me. We exchanged what we know.", importance=2)
        return lines

    # ------------------------------------------------------------------ #
    # Daemon loop
    # ------------------------------------------------------------------ #
    def run_loop(self, interval_seconds: int = 900, once: bool = False):
        """Run the world continuously (or a single day with once=True)."""
        if not self.llm.configured:
            print(
                "World engine: no LLM backend configured. "
                "Start Ollama or set OPENAI_BASE_URL / OPENAI_API_KEY."
            )
            return

        self._clear_stop()
        print(f"🌍 The little Amphoreus awakens — {self.world.clock.format()}")

        failed_days = 0
        while True:
            if self._stop_requested():
                print("🌙 The little Amphoreus rests. (stop requested)")
                break
            if self.world.visitor_present():
                # The visitor is here — yield the hearth to them.
                time.sleep(min(interval_seconds, 60))
                continue
            try:
                lines = self.run_day()
                if lines:
                    print(lines[0])
                failed_days = 0
            except Exception as e:
                # FAILSAFE: one bad day must never kill the world. Record the
                # pause in the chronicle, persist state, and keep going. If a
                # whole run of days keeps failing, back off so we do not spin.
                failed_days += 1
                print(f"[failsafe] a day failed ({e}) — the world holds its breath and continues.")
                try:
                    self.chronicle.append({
                        "time": self.world.clock.format_short(),
                        "text": "The world held its breath for a moment, then went on.",
                    })
                    self.world.save()
                except Exception:
                    pass
                if failed_days > 5:
                    print("[failsafe] several days failed in a row — resting a while.")
                    time.sleep(60)
                    failed_days = 0
            if once:
                break
            time.sleep(interval_seconds)

    # ------------------------------------------------------------------ #
    # Stop / status
    # ------------------------------------------------------------------ #
    def _stop_requested(self) -> bool:
        return os.path.exists(self.stop_path)

    def _clear_stop(self):
        try:
            if os.path.exists(self.stop_path):
                os.remove(self.stop_path)
        except Exception:
            pass

    def stop(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.stop_path)), exist_ok=True)
        with open(self.stop_path, "w") as f:
            f.write("stop")

    def status(self) -> dict:
        return {
            "clock": self.world.clock.format(),
            "llm_configured": self.llm.configured,
            "model": self.llm.model,
            "agents": len(self.agents),
            "chronicle_entries": self.chronicle.count(),
            "visitor_present": self.world.visitor_present(),
        }


def main():
    parser = argparse.ArgumentParser(description="Run the little Amphoreus.")
    parser.add_argument("--interval", type=int, default=900,
                        help="real seconds between in-game days (default 900)")
    parser.add_argument("--once", action="store_true", help="run a single day then exit")
    parser.add_argument("--stop", action="store_true", help="request the engine to stop")
    parser.add_argument("--status", action="store_true", help="show world status")
    parser.add_argument("--model", default="qwen2.5:14b-instruct")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--ambient-model", default=None,
                        help="separate model for the Ambient World Director "
                             "(weather, errands, news); defaults to --model")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    engine = WorldEngine(
        llm_model=args.model,
        llm_base_url=args.base_url,
        ambient_model=args.ambient_model,
        seed=args.seed,
    )

    if args.stop:
        engine.stop()
        print("Stop requested — the little Amphoreus will rest.")
        return
    if args.status:
        for k, v in engine.status().items():
            print(f"  {k}: {v}")
        return

    engine.run_loop(interval_seconds=args.interval, once=args.once)


if __name__ == "__main__":
    main()
