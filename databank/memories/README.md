# Mission memories (Stage 2)

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
| Source files processed | 17 |
| Dialogue units examined | 1370 |
| Personal units | 402 |
| Collective units | 445 |
| Skipped (no Heir present) | 523 |
| Personal memory files | 128 |
| Collective memory files | 14 |
