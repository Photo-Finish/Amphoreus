"""test_mission_memories.py — COMPLETE / RELEVANT gate for split mission memories.

Does not modify databank mission files. Run after (or it will invoke)
`tools/extract_mission_memories.py`.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.knowledge.kb_builder import CHARACTER_ALIASES  # noqa: E402
from src.knowledge.mission_memories import (  # noqa: E402
    SKIP_SOURCES,
    _talk_to_heading,
    collect_all_units,
    excerpt_for_heir,
    heirs_speaking_in_line,
    list_canon_sources,
    speaker_heirs,
    speaker_of,
)
from tools.extract_mission_memories import MEM_ROOT, write_memories  # noqa: E402

SPEAKER_RE = re.compile(r"^\s*>?\s*\*\*(.+?):\*\*\s*(.*)$")


def _assert(cond, msg, fails):
    if not cond:
        fails.append(msg)


def test_speaker_heirs(fails):
    cases = [
        ("Phainon", ["phainon"]),
        ("??? (Phainon)", ["phainon"]),
        ("Young Phainon", ["phainon"]),
        ("Khaslana", ["phainon"]),
        ("The Hero Within", ["phainon"]),
        ('"Evernight"', ["evernight"]),
        ("March 7th", ["evernight"]),
        ("Veil of Evernight, March 7th", ["evernight"]),
        ("Mem", ["cyrene"]),
        ("??? (Mem)", ["cyrene"]),
        ("Cyrene", ["cyrene"]),
        ("Aglaea & Phainon", ["aglaea", "phainon"]),
        ("Dan Heng, Cyrene, March 7th and (Trailblazer)", [
            "dan-heng-permansor-terrae", "cyrene", "evernight",
        ]),
        ("Castorice, Hand of Shadow", ["castorice"]),
        ("Cipher Etched in Memory", ["cipher"]),
        ("Hysilens's Memory", ["hysilens"]),
        ("Terravox", ["dan-heng-permansor-terrae"]),
        ("Aglaea (through Tribbie)", ["aglaea", "tribbie"]),
        ("Tribbie & Trinnon", ["tribbie"]),
        ("(Trailblazer)", []),
        ("Thanatos", []),
        ("Oronyx", []),
        ("Aquila", []),
        ("Kephale?", []),
        ("Janus", []),
        ("Phagousa", []),
        ("Seliose", []),
        ("Flame Reaver", []),
        ("Dolimem", []),
        ("Relimem", []),
        ("Memory's Chorus", []),
        ("Memosnatcher", []),
        ("Team Phainon Fairy", []),
        ("Gorgo, Mydei's Mother", []),
        ("Phainon's Look-Alike", []),
        ("Lygus", []),
        ("Nikador's Corpse", []),
    ]
    for label, expect in cases:
        got = speaker_heirs(label)
        _assert(
            got == expect,
            f"speaker_heirs({label!r}) -> {got} expected {expect}",
            fails,
        )
    _assert(
        _talk_to_heading("**(Talk to Himeko):**") == "Himeko",
        "Talk-to regex missed bold-wrapped companion chat",
        fails,
    )
    _assert(
        _talk_to_heading("*(Talk to Castorice, optional)*") == "Castorice, optional",
        "Talk-to regex missed italic optional Talk-to",
        fails,
    )


def test_sources_cover_all_dialogue_files(fails):
    processed = {p.relative_to(ROOT).as_posix() for p in list_canon_sources(ROOT)}
    expected = {
        "databank/missions/chapter-01-heroic-saga.md",
        "databank/missions/chapter-02-light-slips.md",
        "databank/missions/chapter-03-through-petals.md",
        "databank/missions/chapter-04-fall-at-dawn.md",
        "databank/missions/chapter-05-sun-set-to-die.md",
        "databank/missions/chapter-06-before-their-deaths.md",
        "databank/missions/chapter-07-back-to-earth.md",
        "databank/missions/chapter-08-as-tomorrow.md",
        "databank/missions/adventure/v30.md",
        "databank/missions/adventure/v31.md",
        "databank/missions/adventure/v32.md",
        "databank/missions/adventure/v33.md",
        "databank/missions/adventure/v34.md",
        "databank/missions/adventure/v35-37.md",
        "databank/missions/adventure/v36.md",
        "databank/missions/adventure/v38.md",
        "databank/wiki/lore/tribbie-dialogue.md",
    }
    _assert(expected <= processed, f"missing sources: {sorted(expected - processed)}", fails)
    extra = processed - expected
    _assert(not extra, f"unexpected sources: {sorted(extra)}", fails)


def test_spot_scenes(fails, units):
    def find(title_substr, source_substr):
        hits = [
            u for u in units
            if source_substr in u.source_rel and title_substr.lower() in u.title.lower()
        ]
        return hits

    meet = find("Meeting Phainon and Tribbie", "chapter-01")
    _assert(meet, "missing unit Meeting Phainon and Tribbie", fails)
    if meet:
        u = meet[0]
        _assert(u.kind == "collective", f"meeting should be collective, got {u.kind} {u.heirs}", fails)
        _assert("phainon" in u.heirs, "Phainon missing from first meeting", fails)
        _assert("tribbie" in u.heirs, "Tribbie missing from first meeting", fails)
        _assert("dan-heng-permansor-terrae" in u.heirs, "Dan Heng missing from first meeting", fails)
        _assert("aglaea" not in u.heirs, "Aglaea should not be in first meeting", fails)
        body = "\n".join(u.lines)
        _assert("I bear no harm" in body, "first meeting truncated (Phainon safety line missing)", fails)
        _assert("Janusopolis" in body, "first meeting truncated (Tribbie intro missing)", fails)

    nav = find("Navigation Meeting", "chapter-01")
    _assert(nav, "missing Navigation Meeting", fails)
    if nav:
        u = nav[0]
        _assert("phainon" not in u.heirs, "Phainon must not own Express navigation", fails)
        _assert("evernight" in u.heirs, "March 7th → Evernight should witness navigation", fails)
        _assert("dan-heng-permansor-terrae" in u.heirs, "Dan Heng should witness navigation", fails)

    talks = [
        u for u in units
        if "chapter-01" in u.source_rel and "Talk to Himeko" in u.heading
    ]
    _assert(talks, "Talk-to split failed for **(Talk to Himeko):**", fails)
    if talks:
        _assert(
            "evernight" not in talks[0].heirs and "dan-heng-permansor-terrae" not in talks[0].heirs,
            f"Himeko optional chat dumped onto Heirs: {talks[0].heirs}",
            fails,
        )

    wiki = [
        u for u in units
        if "tribbie-dialogue" in u.source_rel and u.kind != "none"
    ]
    _assert(wiki, "wiki Tribbie/Dialogue produced no Heir units", fails)
    wiki_text = "\n".join("\n".join(u.lines) for u in wiki)
    _assert(
        "Little Gray" in wiki_text and "Century Gate" in wiki_text,
        "wiki Tribbie dialogue missing converted lines",
        fails,
    )

    gold = find("Aglaea — The Goldweaver", "chapter-01")
    _assert(gold, "missing Aglaea Goldweaver scene", fails)
    if gold:
        u = gold[0]
        _assert("aglaea" in u.heirs, "Aglaea missing from Goldweaver", fails)
        body = "\n".join(u.lines)
        _assert("golden threads" in body or "Goldweaver" in u.title, "Goldweaver body empty/truncated", fails)

    await_p = find("Await Phainon at the Vortex of Genesis", "chapter-02")
    _assert(await_p, "missing ch2 Await Phainon", fails)
    if await_p:
        u = await_p[0]
        _assert(u.kind == "collective", f"Await Phainon should be collective, got {u.kind} {u.heirs}", fails)
        _assert("phainon" not in u.heirs, "waiting-room scene is not Phainon's witness", fails)
        _assert("aglaea" in u.heirs and "mydei" in u.heirs, "Aglaea/Mydei should wait at the Vortex", fails)
        body = "\n".join(u.lines)
        _assert("Plan B" in body, "Await Phainon truncated", fails)

    # Oronyx as speaker must not become Evernight.
    leaked = [
        u for u in units
        if "evernight" in u.heirs
        and any((speaker_of(ln) or "").strip('"') == "Oronyx" for ln in u.lines)
        and not any(
            hid == "evernight"
            for ln in u.lines
            for hid in heirs_speaking_in_line(ln)
        )
        and u.heirs.get("evernight") == "spoke"
    ]
    _assert(not leaked, f"Evernight marked as speaking Oronyx lines: {[u.unit_id for u in leaked[:5]]}", fails)

    dolimem = [
        u for u in units
        if any((speaker_of(ln) or "") == "Dolimem" for ln in u.lines)
        and "cyrene" in u.heirs
        and u.heirs.get("cyrene") == "spoke"
        and not any("cyrene" in heirs_speaking_in_line(ln) for ln in u.lines)
    ]
    _assert(not dolimem, f"Cyrene credited for Dolimem speech: {[u.unit_id for u in dolimem[:5]]}", fails)


def test_unit_outputs_complete_relevant(fails, units, inventory):
    by_id = {r["id"]: r for r in inventory["units"]}
    memory_files = inventory["memory_files"]
    loaded = {}

    def load(rel):
        if rel not in loaded:
            p = ROOT / rel
            _assert(p.exists(), f"missing memory file {rel}", fails)
            loaded[rel] = p.read_text(encoding="utf-8") if p.exists() else ""
        return loaded.get(rel, "")

    titan_speakers = {
        "Thanatos", "Oronyx", "Aquila", "Kephale?", "Kephale", "Janus",
        "Phagousa", "Seliose", "Flame Reaver", "Dolimem",
    }

    for u in units:
        row = by_id.get(u.unit_id)
        _assert(row is not None, f"unit {u.unit_id} missing from inventory", fails)
        if row is None:
            continue
        if u.kind == "none":
            continue
        sp_lines = [ln for ln in u.lines if speaker_of(ln)]
        if u.kind == "personal":
            hid = next(iter(u.heirs))
            rel = f"databank/memories/heirs/{hid}/{Path(u.source_rel).stem}.md"
            text = load(rel)
            _assert(u.unit_id in text, f"{rel} missing id {u.unit_id}", fails)
            for ln in sp_lines:
                _assert(
                    ln.strip() in text,
                    f"COMPLETE fail {u.unit_id}: missing speaker line in {rel}: {ln[:80]}",
                    fails,
                )
            # Relevance: file is this Heir's folder.
            _assert(hid in u.heirs, f"RELEVANT fail {u.unit_id}: {hid} not in heirs", fails)
        else:
            rel = f"databank/memories/collective/{Path(u.source_rel).stem}.md"
            text = load(rel)
            _assert(u.unit_id in text, f"{rel} missing id {u.unit_id}", fails)
            for ln in sp_lines:
                _assert(
                    ln.strip() in text,
                    f"COMPLETE fail {u.unit_id}: missing speaker line in collective {rel}: {ln[:80]}",
                    fails,
                )
            for hid in u.heirs:
                prel = f"databank/memories/heirs/{hid}/{Path(u.source_rel).stem}.md"
                ptext = load(prel)
                _assert(u.unit_id in ptext, f"pointer missing for {hid} {u.unit_id}", fails)
                excerpt = excerpt_for_heir(u.lines, hid)
                own = [ln for ln in u.lines if hid in heirs_speaking_in_line(ln)]
                for ln in own:
                    _assert(
                        ln.strip() in ptext,
                        f"COMPLETE fail {hid} excerpt {u.unit_id}: missing own line {ln[:80]}",
                        fails,
                    )
                # Silent extra must not receive the full crowd if excerpt is small.
                if u.heirs[hid] != "spoke" and len(sp_lines) >= 12 and excerpt:
                    _assert(
                        len(excerpt) <= max(8, len(own) + 4),
                        f"RELEVANT fail {hid} dumped crowd scene {u.unit_id}",
                        fails,
                    )

        # Titan speech is not this Heir "speaking".
        for ln in u.lines:
            sp = speaker_of(ln)
            if not sp:
                continue
            if sp.strip('"') in titan_speakers:
                _assert(
                    speaker_heirs(sp) == [],
                    f"Titan {sp} mapped to {speaker_heirs(sp)} in {u.unit_id}",
                    fails,
                )

    for rel, meta in memory_files.items():
        text = load(rel)
        _assert("**Kind:**" in text, f"frontmatter Kind missing in {rel}", fails)
        _assert("**Source:**" in text, f"frontmatter Source missing in {rel}", fails)
        if meta["kind"] == "personal":
            hid = meta["heir"]
            _assert(hid in CHARACTER_ALIASES, f"unknown heir {hid} in {rel}", fails)


def test_personal_memories_exist(fails):
    from src.core.heir_folders import HEIR_FOLDERS
    from src.core.personal_memory import own_speaker_lines

    for hid in CHARACTER_ALIASES:
        folder = ROOT / HEIR_FOLDERS[hid]
        path = folder / "personal-memories.md"
        _assert(path.exists(), f"missing rollup {path}", fails)
        if hid in {"phainon", "aglaea", "tribbie", "cyrene"}:
            own = own_speaker_lines(hid, ROOT)
            _assert(len(own) > 10, f"{hid} voice digest empty ({len(own)} lines)", fails)
        if hid == "castorice":
            own = own_speaker_lines(hid, ROOT)
            _assert(
                not any("**Thanatos:**" in ln for ln, _ in own),
                "Castorice voice digest ingested Thanatos titan lines",
                fails,
            )
        if hid == "cyrene":
            own = own_speaker_lines(hid, ROOT)
            _assert(
                not any("**Dolimem:**" in ln for ln, _ in own),
                "Cyrene voice digest ingested Dolimem lines",
                fails,
            )
        if hid == "evernight":
            own = own_speaker_lines(hid, ROOT)
            _assert(
                not any(ln.startswith("**Oronyx:**") for ln, _ in own),
                "Evernight voice digest ingested Oronyx titan lines",
                fails,
            )


def test_no_invented_lines(fails, units):
    """Every **Speaker:** line in a memory file must exist in its source unit."""
    if not MEM_ROOT.exists():
        fails.append("databank/memories missing")
        return
    unit_line_sets = {}
    for u in units:
        unit_line_sets[u.unit_id] = set(ln.strip() for ln in u.lines if ln.strip())
    id_re = re.compile(r"\*\*Id:\*\*\s+`([^`]+)`")
    for path in list((MEM_ROOT / "heirs").rglob("*.md")) + list((MEM_ROOT / "collective").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        chunks = re.split(r"\n### ", text)
        for chunk in chunks[1:]:
            m = id_re.search(chunk)
            if not m:
                fails.append(f"section without Id in {path}")
                continue
            uid = m.group(1)
            allowed = unit_line_sets.get(uid)
            if allowed is None:
                # skip file header
                continue
            for ln in chunk.splitlines():
                if speaker_of(ln) and ln.strip() not in allowed:
                    # attribution keys are not speakers of canon
                    if speaker_of(ln) in {
                        "Kind", "Source", "Heading", "Lines", "Id", "Heirs",
                        "Witness", "Witness note", "Collective", "Excerpt",
                    }:
                        continue
                    fails.append(
                        f"invented or truncated-mismatch in {path.name} {uid}: {ln[:100]}"
                    )


def main():
    fails: list[str] = []
    test_speaker_heirs(fails)
    test_sources_cover_all_dialogue_files(fails)
    print("Parsing source units…")
    units = collect_all_units(ROOT)
    print(f"  {len(units)} units")
    test_spot_scenes(fails, units)
    if not (MEM_ROOT / "inventory.json").exists() or "--refresh" in sys.argv:
        print("Writing memory files…")
        write_memories()
    inventory = json.loads((MEM_ROOT / "inventory.json").read_text(encoding="utf-8"))
    print("Checking COMPLETE / RELEVANT…")
    test_unit_outputs_complete_relevant(fails, units, inventory)
    test_personal_memories_exist(fails)
    test_no_invented_lines(fails, units)
    if fails:
        print(f"\nFAILED ({len(fails)}):")
        for f in fails[:80]:
            print(" -", f)
        if len(fails) > 80:
            print(f" … {len(fails) - 80} more")
        sys.exit(1)
    c = inventory["counts"]
    print("\nOK — all memory files COMPLETE and RELEVANT.")
    print(
        f"sources={c['source_files']} units={c['units_total']} "
        f"personal={c['units_personal']} collective={c['units_collective']} "
        f"skipped_no_heir={c['units_skipped_no_heir']}"
    )


if __name__ == "__main__":
    main()
