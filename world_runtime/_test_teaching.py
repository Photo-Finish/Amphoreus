"""End-to-end test of the teaching/learning system (mocked LLM, no GPU)."""
import sys, tempfile, json
from pathlib import Path
sys.path.insert(0, r"D:\Workspace\Amphoreus")

from src.core.agent_manager import AgentManager
from src.core import teaching as tp
from src.core.teaching_store import TeachingStore, topic_key, display_topic

tmp = Path(tempfile.mkdtemp(prefix="teaching-test-"))
mgr = AgentManager(
    characters_dir=r"D:\Workspace\Amphoreus\src\characters",
    use_rag=False, memory_root=str(tmp),
)

# --- pure protocol logic ---
assert tp.detect_teaching("I want to teach you about calculus")
assert tp.detect_teaching("Let me teach you something from beyond the stars")
assert not tp.detect_teaching("Good morning, how are you?")
assert tp.asks_verdict("So what do you make of it?")
assert not tp.asks_verdict("Tell me about your day")
assert tp.phase_prompt("foreign", "calculus").startswith("The star-stranger brings")
assert tp.phase_prompt("studied", "calculus").startswith("You have begun")
assert tp.phase_prompt("adopted", "calculus").startswith("You have already formed")
k = topic_key("I want to teach you about calculus — the mathematics of change")
assert k.startswith("calculus"), k
print("protocol logic OK; topic key:", k)

# --- mocked teach flow ---
canned = []

def fake_call(messages, stream=False):
    return canned[0]

mgr._call_llm = fake_call

# Turn 1: first encounter -> studied
canned[:] = ["Calculus? A craft of change... In the Grove we study the fixed and the eternal. Show me how change itself can be measured."]
r1 = mgr.teach("anaxa", "I want to teach you about calculus — the mathematics of change.")
assert canned[0] in r1
st = mgr.teaching.get_topic("anaxa", k)
assert st and st["state"] == "studied", st
assert st["exchanges"] == 1
assert mgr.teaching.to_prompt_block("anaxa") and "calculus" in mgr.teaching.to_prompt_block("anaxa")
print("turn 1 -> studied OK:", r1[:60], "...")

# Turn 2: verdict -> adopted
canned[:] = ["I accept it. Change can be measured — and it holds together like a good proof. I am convinced."]
r2 = mgr.teach("anaxa", "What do you make of it? Was I right?")
st = mgr.teaching.get_topic("anaxa", k)
assert st and st["state"] == "adopted", st
assert st["verdict"] == "adopted" and st["verdict_reason"]
block = mgr.teaching.to_prompt_block("anaxa")
assert "ACCEPTED" in block
print("turn 2 -> adopted OK")
print("--- ledger block ---")
print(block)

# Turn 3: teach a claim -> studied, then verdict -> refuted
k2 = topic_key("Let me teach you that the earth is flat")
canned[:] = ["Nonsense. The stars move as they must, and the world is what the Titans made. I will not hear of disks."]
mgr.teach("anaxa", "Let me teach you that the earth is flat, and all worlds are disks.")
st2 = mgr.teaching.get_topic("anaxa", k2)
assert st2 and st2["state"] == "studied", st2
canned[:] = ["I reject this. It does not hold up against what I know of the world."]
mgr.teach("anaxa", "So what do you make of it now? Was I right?")
st2 = mgr.teaching.get_topic("anaxa", k2)
assert st2 and st2["state"] == "refuted", st2
print("turn 3 -> studied then refuted OK")

# --- memory has teaching entries ---
mems = mgr.memory.get_memories("anaxa", mtype="teaching")
assert len(mems) >= 2, mems
print("memory teaching entries:", len(mems))

# --- chat() auto-routing (routed into teach) ---
canned[:] = ["Hmph. A strange idea from beyond the stars. I will not accept it without proof."]
r = mgr.chat("anaxa", "I want to teach you about quantum mechanics")
k3 = topic_key("I want to teach you about quantum mechanics")
st3 = mgr.teaching.get_topic("anaxa", k3)
assert st3 and st3["state"] == "studied", st3
print("chat auto-route -> studied OK:", r[:60], "...")

# --- ledger persists on disk ---
path = tmp / "SkeMma720-Anaxa" / "teaching.json"
assert path.exists()
data = json.loads(path.read_text(encoding="utf-8"))
assert len(data["topics"]) >= 3
print("ledger persisted on disk:", path.name, "-", len(data["topics"]), "topics")

print("\nALL TEACHING TESTS PASSED")
