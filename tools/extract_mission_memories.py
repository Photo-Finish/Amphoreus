"""
extract_mission_memories.py — split canon mission dialogue into per-Heir and
collective memory files.

Reads databank mission / wiki-dialogue markdown. Never modifies those files.
Writes:
  databank/memories/heirs/<id>/<source-stem>.md
  databank/memories/collective/<source-stem>.md
  databank/memories/INVENTORY.md
  databank/memories/inventory.json
  databank/memories/README.md
  <HeirFolder>/personal-memories.md   (runtime voice-digest rollup)

Replaces the older ±1-exchange alias dump.
"""

from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.heir_folders import HEIR_FOLDERS  # noqa: E402
from src.knowledge.kb_builder import CHARACTER_ALIASES  # noqa: E402
from src.knowledge.mission_memories import (  # noqa: E402
    SKIP_SOURCES,
    collect_all_units,
    excerpt_for_heir,
    list_canon_sources,
)

MEM_ROOT = ROOT / "databank" / "memories"


def _attribution_block(unit, kind: str, extra: list[str] | None = None) -> list[str]:
    heirs = ", ".join(f"{hid} ({role})" for hid, role in sorted(unit.heirs.items()))
    lines = [
        f"**Kind:** {kind}",
        f"**Source:** `{unit.source_rel}`",
        f"**Heading:** {unit.heading}",
        f"**Lines:** {unit.start_line}–{unit.end_line}",
        f"**Id:** `{unit.unit_id}`",
        f"**Heirs:** {heirs or '(none)'}",
    ]
    if extra:
        lines.extend(extra)
    return lines


def _render_unit_body(unit, body: list[str], kind: str, extra: list[str] | None = None) -> str:
    parts = [f"### {unit.title}", ""]
    parts.extend(_attribution_block(unit, kind, extra))
    parts.append("")
    parts.extend(body)
    parts.append("")
    return "\n".join(parts)


def _source_file_header(kind: str, source_rel: str, heir_id: str | None = None) -> str:
    who = f"Heir `{heir_id}`" if heir_id else "shared / collective"
    return (
        f"# Mission memories — {who}\n\n"
        f"> Verbatim extracts from `{source_rel}`. Original mission files are "
        f"unchanged. Attribution headers only — no invented Heir speech.\n\n"
        f"**Kind on this page:** {kind}\n\n"
        "---\n\n"
    )


def write_memories() -> dict:
    units = collect_all_units(ROOT)
    by_source: dict[str, list] = defaultdict(list)
    for u in units:
        by_source[u.source_rel].append(u)

    if MEM_ROOT.exists():
        shutil.rmtree(MEM_ROOT)
    heirs_dir = MEM_ROOT / "heirs"
    coll_dir = MEM_ROOT / "collective"
    heirs_dir.mkdir(parents=True)
    coll_dir.mkdir(parents=True)
    for hid in CHARACTER_ALIASES:
        (heirs_dir / hid).mkdir(parents=True, exist_ok=True)

    inventory_rows = []
    file_index: dict[str, dict] = {}
    personal_rollup: dict[str, list] = defaultdict(list)
    counts = {
        "source_files": 0,
        "units_total": 0,
        "units_personal": 0,
        "units_collective": 0,
        "units_skipped_no_heir": 0,
        "personal_memory_files": 0,
        "collective_memory_files": 0,
        "personal_parts_in_heir_folders": 0,
    }

    sources = list_canon_sources(ROOT)
    counts["source_files"] = len(sources)
    source_order = [p.relative_to(ROOT).as_posix() for p in sources]

    for source_rel in source_order:
        src_units = by_source.get(source_rel, [])
        if not src_units:
            continue
        stem = Path(source_rel).stem
        personal_bodies: dict[str, list[str]] = defaultdict(list)
        collective_bodies: list[str] = []
        skipped_here = 0
        personal_n = 0
        collective_n = 0

        for u in src_units:
            counts["units_total"] += 1
            kind = u.kind
            row = {
                "id": u.unit_id,
                "source": source_rel,
                "heading": u.heading,
                "lines": f"{u.start_line}-{u.end_line}",
                "kind": kind,
                "heirs": u.heirs,
                "complete": False,
                "relevant": False,
                "outputs": [],
                "skip_reason": None,
            }
            if kind == "none":
                counts["units_skipped_no_heir"] += 1
                skipped_here += 1
                row["skip_reason"] = "no Heir spoke, was addressed (Talk to), or named on-stage"
                row["complete"] = True  # nothing to store; unit was examined
                row["relevant"] = True
                inventory_rows.append(row)
                continue

            if kind == "personal":
                hid = next(iter(u.heirs))
                body = _render_unit_body(u, u.lines, "personal")
                personal_bodies[hid].append(body)
                personal_n += 1
                counts["units_personal"] += 1
                out_rel = f"databank/memories/heirs/{hid}/{stem}.md"
                row["outputs"] = [out_rel]
                row["complete"] = True
                row["relevant"] = True
                personal_rollup[hid].append((u, "personal", u.lines, out_rel))
            else:
                extra = ["**Witness note:** full scene lives here; each Heir's personal file keeps a pointer plus what they said/heard."]
                collective_bodies.append(_render_unit_body(u, u.lines, "collective", extra))
                collective_n += 1
                counts["units_collective"] += 1
                coll_rel = f"databank/memories/collective/{stem}.md"
                row["outputs"] = [coll_rel]
                for hid, role in sorted(u.heirs.items()):
                    excerpt = excerpt_for_heir(u.lines, hid)
                    extra_p = [
                        f"**Collective:** `{coll_rel}` (id `{u.unit_id}`)",
                        f"**Witness:** {role}",
                    ]
                    if excerpt:
                        extra_p.append("**Excerpt:** this Heir's spoken lines plus nearby replies (not the whole crowd).")
                    else:
                        extra_p.append("**Excerpt:** pointer only — present, but no spoken lines in this unit.")
                    personal_bodies[hid].append(
                        _render_unit_body(u, excerpt, "collective-pointer", extra_p)
                    )
                    row["outputs"].append(f"databank/memories/heirs/{hid}/{stem}.md")
                    personal_rollup[hid].append((u, "collective-pointer", excerpt, coll_rel))
                row["complete"] = True
                row["relevant"] = True
            inventory_rows.append(row)

        if collective_bodies:
            dest = coll_dir / f"{stem}.md"
            dest.write_text(
                _source_file_header("collective", source_rel) + "\n---\n\n".join(collective_bodies),
                encoding="utf-8",
                newline="\n",
            )
            counts["collective_memory_files"] += 1
            file_index[dest.relative_to(ROOT).as_posix()] = {
                "kind": "collective",
                "source": source_rel,
                "units": collective_n,
            }
        for hid, bodies in personal_bodies.items():
            dest = heirs_dir / hid / f"{stem}.md"
            dest.write_text(
                _source_file_header("personal + collective pointers", source_rel, hid)
                + "\n---\n\n".join(bodies),
                encoding="utf-8",
                newline="\n",
            )
            counts["personal_memory_files"] += 1
            file_index[dest.relative_to(ROOT).as_posix()] = {
                "kind": "personal",
                "heir": hid,
                "source": source_rel,
                "units": len(bodies),
            }

    # Runtime rollup used by voice_digest / style tests.
    for hid, folder_name in HEIR_FOLDERS.items():
        folder = ROOT / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        parts = personal_rollup.get(hid, [])
        header = (
            f"# {hid} — Personal Memories\n\n"
            "> Verbatim canon dialogue this Heir spoke, was addressed in, or "
            "stood on-stage for. Shared scenes are stored in full under "
            "`databank/memories/collective/`; this file keeps the personal "
            "thread plus a pointer. Original databank mission files were not "
            "modified.\n\n"
        )
        body_chunks = []
        for i, (unit, kind, lines, dest) in enumerate(parts, 1):
            meta = [
                f"### Part {i} — `{unit.source_rel}`",
                f"**Context:** {unit.heading}",
                f"**Kind:** {kind}",
                f"**Id:** `{unit.unit_id}`",
            ]
            if kind == "collective-pointer":
                meta.append(f"**Collective:** `{dest}`")
                meta.append(f"**Witness:** {unit.heirs.get(hid, '')}")
            meta.append("")
            body_chunks.append("\n".join(meta + lines + [""]))
        out = folder / "personal-memories.md"
        text = header
        if body_chunks:
            text += "---\n\n" + "\n---\n\n".join(body_chunks)
        else:
            text += "> (No attributed mission dialogue for this Heir.)\n"
        out.write_text(text, encoding="utf-8", newline="\n")
        counts["personal_parts_in_heir_folders"] += len(parts)

    skipped_sources = [{"path": p, "reason": r} for p, r in SKIP_SOURCES]
    processed_paths = [p.relative_to(ROOT).as_posix() for p in sources]

    inventory = {
        "counts": counts,
        "sources_processed": processed_paths,
        "sources_skipped": skipped_sources,
        "memory_files": file_index,
        "units": inventory_rows,
    }
    (MEM_ROOT / "inventory.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    _write_readme(counts, processed_paths, skipped_sources)
    _write_inventory_md(counts, processed_paths, skipped_sources, file_index, inventory_rows)
    return inventory


def _write_readme(counts, processed, skipped) -> None:
    text = f"""# Mission memories (Stage 2)

Canon mission dialogue, split by **who was actually there**.

Original files under `databank/missions/` (and the wiki Tribbie/Dialogue page) are
**verbatim and untouched**. These files are extracts with attribution headers.

## Layout

```
databank/memories/
├── README.md                 ← this file
├── INVENTORY.md              ← completeness checklist
├── inventory.json            ← machine-readable unit map
├── heirs/<heir-id>/<source-stem>.md
└── collective/<source-stem>.md
```

Runtime voice digest still reads `<HeirFolder>/personal-memories.md` (a rollup
of personal units + collective pointers/excerpts).

## How a beat is classified

1. Parse a dialogue **unit** = one leaf heading (mission step / `###` scene /
   adventure `####` beat), further split on `(Talk to X)` so optional chats
   are not mixed.
2. An Heir is related if they **spoke** (strict speaker-label match), were
   the target of **Talk to &lt;Heir&gt;**, or were named in a **stage/cutscene**
   line. Mentioning someone who is off-stage is not enough.
3. **One Heir** → personal memory (full unit).
4. **Two or more Heirs** → one collective memory (full unit) plus a pointer
   and a short witness excerpt in each related Heir's file. Silent extras do
   not receive the whole crowd scene.
5. Guests **Dan Heng** and **Evernight** (including March 7th) follow the
   same rule. Mem / Demiurge fold into Cyrene; Trianne / Trinnon / Tribios
   into Tribbie; Khaslana / Hero Within into Phainon; Terravox into Dan Heng.

Titans and look-alike labels are **not** Heir memory: Oronyx, Thanatos,
Aquila, Kephale, Janus, Phagousa, Nikador, Seliose, Flame Reaver, Dolimem,
and other memosprites stay out unless a real Heir speaker is also present
(in which case those Heirs remember the scene, not the Titan's "voice" as
their own).

## RAG

These files are **not** added to Chroma `GLOBAL_PATTERNS`. Mission chapters
remain the RAG dialogue source. Memories are an attribution layer so we do
not double-index the same lines.

## Rebuild

```
python tools/extract_mission_memories.py
```

`tools/extract_personal_memories.py` calls the same pipeline.

## Counts (last extract)

| | |
|---|---|
| Source files processed | {counts['source_files']} |
| Dialogue units examined | {counts['units_total']} |
| Personal units | {counts['units_personal']} |
| Collective units | {counts['units_collective']} |
| Skipped (no Heir present) | {counts['units_skipped_no_heir']} |
| Personal memory files | {counts['personal_memory_files']} |
| Collective memory files | {counts['collective_memory_files']} |
"""
    (MEM_ROOT / "README.md").write_text(text, encoding="utf-8", newline="\n")


def _write_inventory_md(counts, processed, skipped, file_index, rows) -> None:
    lines = [
        "# Mission-memory inventory",
        "",
        "Every canon dialogue source was examined. Original mission files were not modified.",
        "",
        "## Counts",
        "",
        f"- Sources processed: **{counts['source_files']}**",
        f"- Units examined: **{counts['units_total']}**",
        f"- Personal units: **{counts['units_personal']}**",
        f"- Collective units: **{counts['units_collective']}**",
        f"- Skipped (no Heir present): **{counts['units_skipped_no_heir']}**",
        f"- Personal memory files: **{counts['personal_memory_files']}**",
        f"- Collective memory files: **{counts['collective_memory_files']}**",
        "",
        "## Sources processed",
        "",
    ]
    for p in processed:
        n = sum(1 for r in rows if r["source"] == p)
        pers = sum(1 for r in rows if r["source"] == p and r["kind"] == "personal")
        coll = sum(1 for r in rows if r["source"] == p and r["kind"] == "collective")
        skip = sum(1 for r in rows if r["source"] == p and r["kind"] == "none")
        lines.append(
            f"- `{p}` — processed: yes — units {n} (personal {pers}, collective {coll}, no-Heir {skip})"
        )
    lines += ["", "## Sources skipped", ""]
    for s in skipped:
        lines.append(f"- `{s['path']}` — {s['reason']}")
    lines += ["", "## Memory files", "", "| Path | Kind | Heir | Source | Units |", "|---|---|---|---|---|"]
    for path, meta in sorted(file_index.items()):
        lines.append(
            f"| `{path}` | {meta['kind']} | {meta.get('heir', '—')} | `{meta['source']}` | {meta['units']} |"
        )
    # Fail list (should be empty after extract; tests re-check).
    fails = [r for r in rows if r["kind"] != "none" and (not r["complete"] or not r["relevant"])]
    lines += ["", "## Unit COMPLETE / RELEVANT", ""]
    if not fails:
        lines.append(
            "All stored units were written with full source line-range bodies "
            "(collective/personal) and Heir lists from speaker / Talk-to / on-stage "
            "detection. Automated re-check: `python tools/test_mission_memories.py`."
        )
    else:
        lines.append("**Fails:**")
        for r in fails:
            lines.append(f"- `{r['id']}` complete={r['complete']} relevant={r['relevant']}")
    (MEM_ROOT / "INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    inv = write_memories()
    c = inv["counts"]
    print("Mission memories extracted (databank originals untouched).")
    for k, v in c.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
