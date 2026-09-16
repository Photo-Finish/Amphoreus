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
    check(
        "star-swirl vortex backdrop",
        parchment is not None and parchment.name == "bg-vortex-of-genesis.jpg",
        str(parchment),
    )
    check(
        "not the Exotale garden plaza",
        parchment is not None and "beyond-time" not in parchment.name.lower(),
        str(parchment),
    )
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
    check("pet and drag protocol", "ep_pet" in doc and "ep_drag" in doc)
    placed = build_stage_html(
        selected=["cyrene"],
        art=art,
        names={"cyrene": "Cyrene"},
        layout={"cyrene": [12.0, 44.0]},
    )
    check("drag layout is used", "left:12.0%;bottom:44.0%" in placed)
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
    check("parent hit-test uses elementFromPoint", "elementFromPoint" in ui)
    check("stage iframe is click-through", "pointer-events: none" in ui)
    check("parent command bus", "st-key-amp_eternal_cmd" in ui and "createElement('a')" in ui)
    check("name chips backup", "amp_eternal_names" in ui)
    check("hidden Streamlit hit buttons", "amp_eternal_hit_" in ui)
    check("vfx overlay classes", "mk-flush" in doc and "mk-vein" in doc and "data-amp-vfx=" in doc)
    check("keyboard legend on stage", "data-amp-legend" in doc and "Shift+click" in doc)
    check("hover keys documented", "P pat" in doc and "H hug" in doc)
    check("parent keydown ignores typing", "typingFocus" in ui and "contenteditable" in ui)
    check("ep_act query bridge", "ep_act" in ui and "ep_id" in ui)
    check("companions stay sticker images", doc.count("<img ") == 13 and "<svg" not in doc.lower())
    check("companions do not hover-bob", "amp-bob" not in doc and "amp-bob" not in ui)
    check("emotion marks still float", "@keyframes amp-float" in doc and "mk-heart::after" in doc)
    gal = (ROOT / "src" / "ui_galgame.py").read_text(encoding="utf-8")
    galg = (ROOT / "src" / "ui_galgame_group.py").read_text(encoding="utf-8")
    check("galgame portraits do not hover-bob", "galfloat" not in gal)
    check("group galgame portraits do not hover-bob", "galfloat" not in galg)


def test_desktop_pet() -> None:
    print("== desktop pet ==")
    check("place default", ep.place_of("cyrene") == ep.LAYOUT["cyrene"])
    moved = ep.move_companion({}, "cyrene", 12.5, 40.0)
    check("move writes overlay", moved.get("cyrene") == [12.5, 40.0], str(moved))
    check("clamp high", ep.clamp_place(200, 200) == (96.0, 88.0))
    check("clamp low", ep.clamp_place(-4, 0) == (4.0, 8.0))
    check("unknown stay put", "nope" not in ep.move_companion({}, "nope", 1, 1))
    world = SimpleNamespace(mood={})
    ok = ep.pet_companion("phainon", world=world)
    check("pet is allowed", ok is True)
    check(
        "pet warms mood without speech",
        int((world.mood.get("phainon") or {}).get("valence") or 0) >= 1,
        str(world.mood),
    )
    check("pet does not chat", ep.pet_companion.__doc__ and "never authors" in ep.pet_companion.__doc__)
    check("junk pet refused", ep.pet_companion("nope", world=world) is False)
    check("parse click", ep.parse_command("click:cyrene") == ("click", "cyrene"))
    check("parse solo", ep.parse_command("solo:mydei") == ("solo", "mydei"))
    check("parse pet", ep.parse_command("pet:hyacine") == ("pet", "hyacine"))
    check(
        "parse drag",
        ep.parse_command("drag:aglaea:10:20") == ("drag", "aglaea", 10.0, 20.0),
    )
    check("parse junk", ep.parse_command("explode:cyrene") is None)
    check("parse pat", ep.parse_command("pat:cyrene") == ("pat", "cyrene"))
    check("parse poke", ep.parse_command("poke:mydei") == ("poke", "mydei"))
    check("parse ask", ep.parse_command("ask:hyacine") == ("ask", "hyacine"))
    src = Path(ep.__file__).read_text(encoding="utf-8")
    pet_fn = src.split("def pet_companion", 1)[-1].split("\ndef ", 1)[0]
    check("pet never calls chat", "eternal_talk" not in pet_fn and ".chat(" not in pet_fn)


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


def test_gestures_and_vfx() -> None:
    print("== gestures and vfx ==")
    import time

    from src.ui_eternal_page import _apply_command, _consume_clicks, build_stage_html
    from src.world import eternal_emotion as ee
    from src.world import eternal_gesture as eg

    art = {cid: "data:image/png;base64,QQ==" for cid in ep.all_ids()}
    pat = eg.reaction_for("hyacine", "pat")
    check("hyacine pat is joy", bool(pat) and pat["emotion"] == "joy", str(pat))
    poke = eg.reaction_for("mydei", "poke")
    check("mydei poke is anger", bool(poke) and poke["emotion"] == "anger", str(poke))
    check("mydei poke shows a vein", bool(poke) and "vein" in poke["vfx"], str(poke))
    fear = eg.reaction_for("castorice", "poke")
    check("castorice poke is fear", bool(fear) and fear["emotion"] == "fear", str(fear))
    hands = eg.reaction_for("cyrene", "hands")
    check("hold hands is social", bool(hands) and hands["social"] and hands["join_near"])
    check("anger default vfx", "vein" in ee.vfx_for("anger") and "steam" in ee.vfx_for("anger"))
    check("joy default vfx", "sparkle" in ee.vfx_for("joy") and "heart" in ee.vfx_for("joy"))
    check("weary default vfx", ee.vfx_for("weary") == ("zzz",))
    check("unknown gesture", eg.reaction_for("cyrene", "explode") is None)

    world = SimpleNamespace(mood={})
    touched = eg.apply_gesture("phainon", "pat", world=world, overlay={}, near=["cyrene"])
    check("pat applies", bool(touched.get("ok")))
    check(
        "pat warms mood",
        int((world.mood.get("phainon") or {}).get("valence") or 0) >= 1,
        str(world.mood),
    )
    reason = str((world.mood.get("phainon") or {}).get("reason") or "")
    check("pat reason is factual", reason == "a pat on the head on the Eternal Page", reason)
    hug = eg.apply_gesture(
        "cyrene", "hug", world=world, overlay={}, near=["phainon", "cyrene"]
    )
    check("hug overlay on target", (hug.get("overlay") or {}).get("cyrene", {}).get("gesture") == "hug")
    wit = (hug.get("overlay") or {}).get("phainon") or {}
    check("hug marks nearby Heirs", bool(wit.get("witness")) and wit.get("gesture") == "hug")

    now = time.time()
    faces = ee.circle_emotions(
        gestures={"aglaea": {"emotion": "anger", "vfx": ["vein"], "ts": now}}
    )
    check("gesture overlay sets the face", faces.get("aglaea") == "anger", str(faces.get("aglaea")))
    stale = ee.circle_emotions(
        gestures={"aglaea": {"emotion": "anger", "vfx": ["vein"], "ts": now - 10_000}}
    )
    check("stale overlay does not stick", stale.get("aglaea") == "calm", str(stale.get("aglaea")))
    pruned = eg.prune_overlay(
        {"aglaea": {"emotion": "anger", "ts": now - 10_000}}, now=now
    )
    check("prune drops stale overlay", pruned == {})

    cmds = eg.commands_from_query({"ep_act": "pat", "ep_id": "cyrene"})
    check("consume ep_act", cmds == ["pat:cyrene"], str(cmds))
    check(
        "consume legacy pet",
        eg.commands_from_query({"ep_pet": "hyacine"}) == ["pet:hyacine"],
    )
    check(
        "consume drag query",
        eg.commands_from_query({"ep_drag": "aglaea,10,20"}) == ["drag:aglaea:10:20"],
    )
    check(
        "consume click query",
        eg.commands_from_query({"ep_click": "phainon"}) == ["click:phainon"],
    )
    parsed = ep.parse_command(cmds[0])
    check("act query parses", parsed == ("pat", "cyrene"), str(parsed))

    class FakeQuery(dict):
        pass

    class FakeST:
        def __init__(self):
            self.query_params = FakeQuery({"ep_click": "phainon"})
            self.session_state = {
                ep.STATE_SELECTED: [],
                ep.STATE_LAYOUT: {},
                ep.STATE_GESTURES: {},
                ep.STATE_CMD: "",
            }

    fake = FakeST()
    changed = _consume_clicks(fake)
    check("consume click changes selection", changed is True)
    check(
        "click query stands near",
        fake.session_state.get(ep.STATE_SELECTED) == ["phainon"],
        str(fake.session_state.get(ep.STATE_SELECTED)),
    )
    fake2 = FakeST()
    fake2.query_params = FakeQuery({})
    fake2.session_state[ep.STATE_SELECTED] = ["cyrene"]
    ok_cmd = _apply_command(fake2, "hands:cyrene", world=SimpleNamespace(mood={}))
    check("apply hands command", ok_cmd is True)
    row = (fake2.session_state.get(ep.STATE_GESTURES) or {}).get("cyrene") or {}
    check("hands writes overlay", row.get("gesture") == "hands", str(row))

    gest_html = build_stage_html(
        selected=["cyrene"],
        art=art,
        names={"cyrene": "Cyrene"},
        emotions={"cyrene": "anger"},
        gestures={"cyrene": {"gesture": "poke", "emotion": "anger", "vfx": ["vein", "steam"], "ts": now}},
    )
    check("anger vfx class in html", "mk-vein" in gest_html and 'data-amp-emotion="anger"' in gest_html)
    check("gesture flash marked", 'data-amp-gesture="poke"' in gest_html)
    for cls in eg.vfx_class_names():
        check(f"vfx mark {cls}", cls in gest_html)
    check("legend lists ctrl poke", "Ctrl+click" in gest_html and "poke" in gest_html.lower())

    src = Path(eg.__file__).read_text(encoding="utf-8")
    ui = Path(ROOT / "src" / "ui_eternal_page.py").read_text(encoding="utf-8")
    check("gesture module never chats", "eternal_talk" not in src and ".chat(" not in src)
    check("gesture module never authors I-lines", 'reason": "I ' not in src)
    bad_bits = ("Nya~", "Nya", "don't poke me", "Don't poke me", "how dare you poke")
    blob = src + "\n" + ui
    check(
        "no canned Heir speech in gestures",
        not any(b.lower() in blob.lower() for b in bad_bits if b != "Nya"),
    )
    # Nya is too short; look for the cute canned form only.
    check("no Nya canned line", "Nya~" not in blob and "nya~" not in blob.lower())
    for gid, spec in eg.GESTURES.items():
        reason = str(spec.get("reason") or "")
        check(
            f"{gid} reason is factual",
            reason.startswith("a ") and "Eternal Page" in reason and " I " not in f" {reason} ",
            reason,
        )
        check(f"{gid} has a vfx", bool(spec.get("vfx")))
    check("ask line is the visitor's", eg.ASK_USER_LINE == "How did that feel?")
    check("ask is not a gesture id", "ask" not in eg.GESTURE_IDS)


def main() -> int:
    test_roster()
    test_selection()
    test_speakers()
    test_memory_shared_with_visit()
    test_no_land_systems()
    test_art()
    test_html_stage()
    test_desktop_pet()
    test_interaction_api()
    test_emotion_poses()
    test_gestures_and_vfx()
    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    for name in FAILED:
        print(f"  - {name}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
