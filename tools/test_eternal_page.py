# -*- coding: utf-8 -*-
"""An Eternal Page — circle, shared memory, buddy HTML (no LLM).

    python tools/test_eternal_page.py
"""
from __future__ import annotations

import os
import struct
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.core.heir_folders import HEIR_FOLDERS
from src.core.memory_store import MemoryStore
from src.world import eternal_page as ep
from src.ui_eternal_page import STAGE_H, build_stage_html

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        extra = f"  {detail}" if detail else ""
        print(f"FAIL  {name}{extra}")


class FakeManager:
    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.calls: list[tuple[str, str]] = []

    def chat(self, character_id: str, user_message: str, **_kw) -> str:
        self.calls.append((character_id, user_message))
        self.memory.record_visit(character_id)
        self.memory.add_history(character_id, "user", user_message)
        reply = f"{character_id} answers: {user_message}"
        self.memory.add_history(character_id, "assistant", reply)
        return reply

    def get_character_info(self, character_id: str) -> dict:
        return {"name": ep.short_name(character_id)}


def png_ihdr(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 24:
        return None
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def png_unique_colors(path: Path, cap: int = 64) -> int:
    try:
        from PIL import Image
    except Exception:
        return -1
    im = Image.open(path).convert("RGBA")
    im.thumbnail((96, 96))
    seen = set()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a > 20:
                seen.add((r, g, b))
            if len(seen) > cap:
                return cap + 1
    return len(seen)


def test_roster() -> None:
    print("== roster ==")
    ids = ep.all_ids()
    check("thirteen Heirs", len(ids) == 13, str(ids))
    check("matches character cards", set(ids) == set(HEIR_FOLDERS))
    check("layout for every Heir", all(c in ep.LAYOUT for c in ids))
    check("Cyrene is on the page", "cyrene" in ids)


def test_selection() -> None:
    print("== selection ==")
    check("empty normalizes", ep.normalize_selected([]) == [])
    check("unknown dropped", ep.normalize_selected(["nope", "phainon"]) == ["phainon"])
    one = ep.toggle_member([], "aglaea")
    check("toggle on", one == ["aglaea"])
    check("toggle off", ep.toggle_member(one, "aglaea") == [])
    check("solo", ep.solo_member("mydei") == ["mydei"])
    check("solo rejects junk", ep.solo_member("nope") == [])
    all_ids = ep.all_ids()
    check("all thirteen", len(all_ids) == 13)


def test_speakers() -> None:
    print("== speakers ==")
    ids = ep.all_ids()
    s, listen = ep.pick_speakers(["phainon"], "hello")
    check("solo speaks", s == ["phainon"] and listen == [])
    trio = ["phainon", "mydei", "aglaea"]
    s, listen = ep.pick_speakers(trio, "hello")
    check("small circle all speak", set(s) == set(trio) and listen == [])
    s, listen = ep.pick_speakers(ids, "hello", everyone=True)
    check("everyone answers", set(s) == set(ids) and listen == [])
    s, listen = ep.pick_speakers(ids, "hello", everyone=False, cap=4)
    check("cap speakers", len(s) == 4, str(s))
    check("rest listen", len(listen) == 9, str(len(listen)))
    s, listen = ep.pick_speakers(ids, "Phainon, can you hear me?", cap=4)
    check("named speaker kept", "phainon" in s, str(s))
    a, _ = ep.pick_speakers(ids, "hello", rotate=0, cap=4)
    b, _ = ep.pick_speakers(ids, "hello", rotate=4, cap=4)
    check("rotate changes the set", set(a) != set(b), f"{a} vs {b}")


def test_memory_shared_with_visit() -> None:
    print("== shared memory ==")
    tmp = Path(tempfile.mkdtemp(prefix="amp-eternal-"))
    memory = MemoryStore(tmp)
    manager = FakeManager(memory)
    line = "The wheat by the dromas road was gold today."
    # Visit-style turn first.
    visit_reply = manager.chat("phainon", line)
    check("visit wrote user+assistant", memory.history_count("phainon") == 2)
    # Eternal Page uses the same chat() for speakers.
    out = ep.eternal_talk(
        manager,
        ["phainon", "cyrene", "aglaea", "mydei", "castorice"],
        "Do you remember the wheat?",
        everyone=False,
    )
    check("talk ok", bool(out.get("ok")))
    check("phainon used manager.chat", any(c == "phainon" for c, _ in manager.calls[1:]))
    # Speakers have assistant lines; listeners have the user line only.
    speakers = set(out["speakers"])
    for cid in out["members"]:
        hist = memory.get_recent_history(cid, n=20)
        users = [h for h in hist if h.get("role") == "user"]
        asst = [h for h in hist if h.get("role") == "assistant"]
        check(
            f"{cid} heard the whisper",
            any("wheat" in str(h.get("content")) for h in users),
            str(users[-1] if users else None),
        )
        if cid in speakers:
            check(f"{cid} answered into history", len(asst) >= 1)
        elif cid != "phainon":
            check(f"{cid} listener has no extra answer", len(asst) == 0)
    # Same files Visit would read.
    folder = tmp / HEIR_FOLDERS["phainon"]
    check("history.jsonl is Visit's file", (folder / "history.jsonl").is_file())
    check("bond.json is Visit's file", (folder / "bond.json").is_file())
    # Journey vs Aftermath does not fork storage.
    src = Path(ep.__file__).read_text(encoding="utf-8")
    check("no mode fork in eternal_page", "SANCTUARY_MODE" not in src)
    check("no play_mode fork in eternal_page", "play_mode" not in src)
    check("visit reply stored", "wheat" in visit_reply)


def test_no_land_systems() -> None:
    print("== no land systems ==")
    world = Path(ep.__file__).read_text(encoding="utf-8")
    ui = Path(ROOT / "src" / "ui_eternal_page.py").read_text(encoding="utf-8")
    blob = world + "\n" + ui
    check("no weather module", "ui_weather" not in blob and "from src.world.ambient" not in blob)
    check("no ecosystem module", "from src.world.ecosystem" not in blob)
    check("no chimera/dromas sprites", "life_sprites" not in blob)


def test_art() -> None:
    print("== cute art ==")
    missing = ep.art_missing()
    check("every Heir has a sticker PNG", missing == [], ",".join(missing))
    parchment = ep.parchment_path()
    check("parchment backdrop exists", parchment is not None)
    for cid in ep.all_ids():
        path = ep.cute_art(cid)
        if not path:
            continue
        size = png_ihdr(path)
        check(f"{cid} is a real PNG", size is not None, str(path))
        if size:
            w, h = size
            check(f"{cid} is not tiny", w >= 96 and h >= 96, f"{w}x{h}")
        ncolors = png_unique_colors(path)
        if ncolors < 0:
            check(f"{cid} file is substantial", path.stat().st_size > 12000, str(path.stat().st_size))
        else:
            check(f"{cid} is painted art", ncolors >= 24, f"colors={ncolors}")


def test_html_stage() -> None:
    print("== buddy stage html ==")
    art = {cid: f"data:image/png;base64,QQ==" for cid in ep.all_ids()}
    doc = build_stage_html(
        selected=["cyrene", "phainon"],
        bubbles=[{"id": "cyrene", "text": "The page remembers you."}],
        art=art,
        parchment_uri="data:image/jpeg;base64,QQ==",
        names={"cyrene": "Cyrene", "phainon": "Phainon"},
        emotions={"cyrene": "joy", "phainon": "weary"},
    )
    check("contained height", STAGE_H == 560 and STAGE_H < 900)
    check("no full-viewport stage", "100vh" not in doc and "position:fixed" not in doc)
    wheel_js = "\n".join(
        line for line in doc.splitlines()
        if "wheel" in line.lower() or "scrollBy" in line or "passive" in line
    )
    check("no wheel preventDefault", "preventDefault" not in wheel_js)
    check("passive wheel passthrough", "parent.scrollBy" in doc and "{passive: true}" in doc)
    check("no canvas placeholders", "<canvas" not in doc.lower())
    check("sprites are images", doc.count("<img ") == 13)
    check("speech bubble present", "data-amp-bubble" in doc and "The page remembers you." in doc)
    check("emotion attribute on buddy", 'data-amp-emotion="joy"' in doc)
    check("weary pose marked", 'data-amp-emotion="weary"' in doc)
    check("selected ring class", 'data-heir="cyrene"' in doc and "buddy on" in doc)
    check("click + double-click", "ep_click" in doc and "ep_solo" in doc)
    check("stage marker", 'data-amp-eternal-stage="1"' in doc)
    check("bubble above buddies", "z-index: 8" in doc)
    # Geometric drawing would use svg circles / rects as characters.
    check("no svg geometry characters", "<svg" not in doc.lower() and "<circle" not in doc.lower())
    ui = (ROOT / "src" / "ui_eternal_page.py").read_text(encoding="utf-8")
    check("whisper is a form not chat_input", "st.chat_input" not in ui and "whisper_form" in ui)
    check("distinct from Visit", "Visit an Heir" in ui)
    app = (ROOT / "src" / "ui_app.py").read_text(encoding="utf-8")
    check("tab exists", '"An Eternal Page"' in app)
    page = ROOT / "src" / "pages" / "3_An_Eternal_Page.py"
    check("multipage exists", page.is_file())
    look = (ROOT / "src" / "ui_look.py").read_text(encoding="utf-8")
    check("look watcher knows Eternal", "An Eternal Page" in look and "amp-mode-eternal" in look)
    from src.world import group_chat as gc
    check("leaving Visit for Eternal ends gathering", gc.should_end_for_tab("An Eternal Page"))


def test_interaction_api() -> None:
    print("== interaction ==")
    tmp = Path(tempfile.mkdtemp(prefix="amp-eternal-i-"))
    manager = FakeManager(MemoryStore(tmp))
    empty = ep.eternal_talk(manager, ["phainon"], "   ")
    check("empty whisper refused", empty.get("reason") == "empty")
    none = ep.eternal_talk(manager, [], "Hello")
    check("no one near refused", none.get("reason") == "none_near")
    out = ep.eternal_talk(manager, ["hyacine"], "Are you well?")
    check("single reply", out.get("ok") and len(out.get("speakers") or []) == 1)
    check("intuitive one-to-one", manager.calls[-1][0] == "hyacine")


def test_emotion_poses() -> None:
    print("== emotion poses ==")
    from src.world import eternal_emotion as ee
    from src.world import living_world as lw

    check("joy from glad talk", ee.classify_text("Ehe! I am so glad you came.") == "joy")
    check("weary from tired talk", ee.classify_text("I am so tired I can barely stand.") == "weary")
    check("fear from the tide", ee.classify_text("The black tide presses at the walls.") == "fear")
    check("sad from apology", ee.classify_text("I am sorry. It still hurts.") == "sad")
    check("empty is calm", ee.classify_text("   ") == "calm")

    world = SimpleNamespace(
        mood={"aglaea": {"valence": 3, "reason": "a warm visit", "ts": ""}},
        surge={"active": True, "remaining": 2, "cities": ["Okhema"]},
        black_tide_enabled=True,
        _travel={},
    )
    world.location_name = lambda cid: "Okhema"
    world.travel_info = lambda cid: None

    check(
        "radiant mood is joy",
        ee.detect_emotion("aglaea", world=world) == "joy",
        ee.detect_emotion("aglaea", world=world),
    )
    check(
        "tide at the city wears them",
        ee.detect_emotion("phainon", world=world) in {"weary", "fear"},
        ee.detect_emotion("phainon", world=world),
    )

    tmp = Path(tempfile.mkdtemp(prefix="amp-eternal-emo-"))
    memory = MemoryStore(tmp)
    memory.add_history("cyrene", "user", "hello")
    memory.add_history("cyrene", "assistant", "I am sorry. I have been lonely.")
    felt = ee.detect_emotion(
        "cyrene",
        memory=memory,
        world=SimpleNamespace(
            mood={"cyrene": {"valence": 0, "reason": "", "ts": ""}},
            surge={"active": False, "remaining": 0, "cities": []},
            black_tide_enabled=False,
            location_name=lambda cid: "Aedes Elysiae",
            travel_info=lambda cid: None,
        ),
        last_reply="I am sorry. I have been lonely.",
    )
    check("conversation outweighs calm mood", felt == "sad", felt)

    check("aglaea anger uses a different sticker", ee.variant_for("aglaea", "anger") == "02")
    check("aglaea joy uses bath sticker", ee.variant_for("aglaea", "joy") == "01")
    joy_art = ep.cute_art("aglaea", "joy")
    anger_art = ep.cute_art("aglaea", "anger")
    check(
        "aglaea avatar changes with emotion",
        joy_art is not None and anger_art is not None and joy_art != anger_art,
        f"{joy_art} vs {anger_art}",
    )
    phainon_sad = ep.cute_art("phainon", "sad")
    check("phainon still has a sticker when poses are few", phainon_sad is not None)
    missing_pose = []
    for cid in ep.all_ids():
        if ep.cute_art(cid, "calm") is None:
            missing_pose.append(cid)
    check("every Heir has a calm pose", missing_pose == [], ",".join(missing_pose))
    multi = [
        cid for cid in ep.all_ids()
        if (ep.ART_DIR / cid).is_dir()
        and len(list((ep.ART_DIR / cid).glob("*.png"))) >= 2
    ]
    check("most Heirs have several PPG poses", len(multi) >= 11, str(len(multi)))
    check("unknown emotion falls back", ee.variant_for("hyacine", "nope") == ee.variant_for("hyacine", "calm"))
    check("normalize wounded", ee.normalize_emotion("wounded") == "sad")
    lw.set_mood  # living_world is importable for ongoings
    check("living world mood names exist", "calm" in lw.MOOD_NAMES.values())


def main() -> int:
    test_roster()
    test_selection()
    test_speakers()
    test_memory_shared_with_visit()
    test_no_land_systems()
    test_art()
    test_html_stage()
    test_interaction_api()
    test_emotion_poses()
    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    for name in FAILED:
        print(f"  - {name}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
