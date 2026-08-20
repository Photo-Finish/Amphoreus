# RAG skills vs non-skills — speech-style A/B

*Model `qwen2.5:14b-instruct` · 3 Heirs × 3 cases · Chroma RAG on*

## Verdict

**Skilled is not significantly better on speech-style similarity.** Treat skills as an **optional** RAG aid (default **OFF**).

| Condition | avg style | avg content | case wins | notes |
|---|---:|---:|---:|---|
| A non-skilled | 59.8 / 61.1 | 53.9 / 54.4 | — | baseline / refined runs |
| B skilled **baseline** (thin skill rules) | 65.6 | 56.1 | B2 / A1 / ties6 | Δstyle +5.8 but **mostly ties**; wins were thin (ellipsis / one Tribbie rescue) |
| B skilled **refined** (voice-first + mission bias) | 59.8 | 59.4 | B3 / A2 / ties4 | Δstyle **−1.3** — no clear win; content slightly up |

Honest read: replies often match between A and B. Skills help **retrieval discipline / anti-lore-bot** more reliably than they lift **delivery** scores. Classic RAG + measured card voice remains the default path.

Full case dumps: `docs/RAG-SKILLS-STYLE-AB.json` (baseline), `docs/RAG-SKILLS-STYLE-AB-REFINED.json`.

## When to turn skills ON

- You want mission chunks preferred in the Knowledge block and a short anti-encyclopedia reminder.
- Agent work already following `.cursor/skills/amphoreus-databank-rag` (Cursor skill load ≠ this runtime switch).

Leave **OFF** for everyday sanctuary chat when voice fidelity is the priority.

## How to enable / disable

1. **Control Panel** → Voice path section → **Skills aid (optional)** → ON / OFF  
2. Env: `AMP_SKILLS=1` (on) / `AMP_SKILLS=0` (off) — overrides the file  
3. File: `world_runtime/amp_skills.json` → `{"enabled": true}`  
4. Sidebar (operator) shows current skills label next to RAG status  

Default: **OFF**. Applies on the **RAG** voice path only (not OPLoRA).

## Re-run eval

```bash
# from repo root, with OPENAI_BASE_URL=http://127.0.0.1:11434/v1
python tools/eval_rag_skills_style.py --variant baseline
python tools/eval_rag_skills_style.py --variant refined --report docs/RAG-SKILLS-STYLE-AB-REFINED.md
python tools/test_amp_skills.py
```
