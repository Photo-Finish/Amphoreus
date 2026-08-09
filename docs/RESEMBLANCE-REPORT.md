# Dialogue-Resemblance Report (the Heir-model standard)

*Generated: 2026-08-10 · model `qwen2.5:14b-instruct` · pass bar ≥ 85/100 (LLM judge)*

> **Status:** this is the initial **pilot** (2 Heirs × 3 cases) that validated the
> workflow with the real sanctuary model (`qwen2.5:14b-instruct`). The **full
> 13-Heir baseline** is pending: the 14B was unavailable later the same day
> (CUDA pinned-memory pool exhaustion — see `TECHNICAL-BARRIERS.md` §9; a reboot
> resets it). Run it afterwards with:
> `python tools/test_dialogue_resemblance.py` (defaults: all 13 Heirs, 8 cases
> each, pass ≥ 85).

Method: real canon contexts from `personal-memories.md` → the Heir model replies
in character → a strict LLM judge scores meaning/emotion/voice (0-100 each);
embedding cosine (all-MiniLM) reported as a secondary signal. Base
`prompts.system_prompt` only (no voice-digest leakage).

| Heir | cases | pass | avg judge | avg cosine | pass rate |
|---|---:|---:|---:|---:|---:|
| Phainon (phainon) | 3 | 0 | 48 | 0.21 | 0% |

**Phainon** — failed cases (judge < 85):
- 50/100: ctx *(scene: Complete Dialogue > Mission 1 — Silver Chariot, Away to that Blackened L* → expected *You've got something... interesting.* → model ***(Phainon quickly turns his head towards the voice, readying himself for action*
- 30/100: ctx *(scene: Mission 5: Memories, Veiled in Blazing Mist > Try to Understand What Hap* → expected *The culprit... is... Mydeimos...* → model *(sighs deeply) Tribbie, what happened here? Why do the memories always bring us *
- 63/100: ctx *(scene: Complete Dialogue > Mission 3 — (Side) Hero, Return to That Peace of Hom* → expected *Yes, a flimsy little card. That is my choice. Just know that it's called the "De* → model ***(Phainon sighs)** "It's not just any card, Mydei. It's an important part of ou*
| Hysilens (hysilens) | 3 | 0 | 39 | 0.16 | 0% |

**Hysilens** — failed cases (judge < 85):
- 52/100: ctx *(scene: Complete Dialogue > Mission 5 — (Side) Hero, Ignite That Primal Sun > Ta* → expected *You mean Phainon? Such a name could never be your true one...* → model ***Hysilens:** Khaslana, your presence calls forth a melody I did not know was wi*
- 30/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Sun, Repel Stars and Pale Moon > Some* → expected *Thank you for your bravery, guests. It's time for me to dispel the fantasia. Thi* → model ***Hysilens:** (in a low voice) Shadows dance when light is dimmed. The winds of *
- 35/100: ctx *(scene: Complete Dialogue > Sub-Mission 7: Captives, Behold the Expanse Beyond L* → expected *Your ambitions have already made so many people give up their lives for the "Law* → model ***Hysilens:** The sea teaches us that every wave付出必有代价，海洋教会我们每一波浪都有其代价。但我们也能从深渊中*