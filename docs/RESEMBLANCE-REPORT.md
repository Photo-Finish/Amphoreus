# Dialogue-Resemblance Report (the Heir-model standard)

*Generated: 2026-08-10 · model `qwen2.5:14b-instruct` · pass bar ≥ 85/100 (LLM judge)*

Method: real canon contexts from `personal-memories.md` → the Heir model replies
in character → a strict LLM judge scores meaning/emotion/voice (0-100 each);
embedding cosine (all-MiniLM) reported as a secondary signal. Base
`prompts.system_prompt` only (no voice-digest leakage).

| Heir | cases | pass | avg judge | avg cosine | pass rate |
|---|---:|---:|---:|---:|---:|
| Tribbie (tribbie) | 8 | 0 | 43 | 0.25 | 0% |

**Tribbie** — failed cases (judge < 85):
- 35/100: ctx *(scene: Complete Dialogue > Mission 1 — Silver Chariot, Away to that Blackened L* → expected *Phai—non—! Look what you did again! Agh, you even ruined his weapon! This is no * → model *Snowy~! Don't be so suspicious, we just want to help find Trianne and stop whate*
- 58/100: ctx *(scene: Complete Dialogue > Mission 6 — Kremnos, Cleanse Thy Rusted Blood (I) > * → expected *No need for formalities at a time like this. I trust that you have found a solut* → model *Snowy~, you're too kind! We did what we could. Let's find those memory fragments*
- 58/100: ctx *(scene: Mission 3: Grove, Wherefore Are the Wise Silent > Leave the Library of P* → expected *Yup! The spindle that Agy gave us is so powerful that Trianne seems to have foun* → model *Snowy~! Trianne's got a knack for finding things, doesn't she?*
- 25/100: ctx *(scene: Mission 6: Passages, Knocking Echoes in Dreams > Find Missing Memories)
* → expected *(All the words are blurred out... Could it be that my memory is fading?)* → model *We summon thee, Oronyx, to lift the curtain of memory... Snowy~! Maybe your memo*
- 50/100: ctx *(scene: Mission 6: Passages, Knocking Echoes in Dreams > Have an Audience with O* → expected *Come on... This isn't the right time to be playing games.* → model *Snowy~, maybe they're waiting for just the right moment... to show us something *
| Cipher (cipher) | 8 | 0 | 39 | 0.18 | 0% |

**Cipher** — failed cases (judge < 85):
- 20/100: ctx *(scene: Complete Dialogue > Sub-Mission 6: Pathstrider, Set Sail Upon the River * → expected *Grumph...* → model *Pfft... Who’s looking for who here?*
- 30/100: ctx *(scene: Complete Dialogue > Sub-Mission 6: Pathstrider, Set Sail Upon the River * → expected *She can always turn back before the end, you know? Maybe she'll remember Trianne* → model *Pfft..., who says I have a mind to make up? Castorice is just better at hiding h*
- 50/100: ctx *(scene: Complete Dialogue > Sub-Mission 6: Pathstrider, Set Sail Upon the River * → expected *Alright! Pass me the coin — it's time to get the god's powers going! A fleet-foo* → model *Pfft..., like a few coins are gonna change the cosmos. Hahaha! Just take it and *
- 58/100: ctx *(scene: Complete Dialogue > Mission 3 — Chest, Bear the Bygone Dust > Flashback:* → expected *Ha, I won them fair and square in a bet. What, do you doubt me?* → model *Pfft... Just a girl who loves treasure and the twists of fate, Ags. Always have,*
- 35/100: ctx *(scene: Complete Dialogue > Mission 4 — Golden Thread, Relay the Savior's Fate >* → expected *What confidence. You talk as if you have everything in the palm of your hand... * → model *Hahaha! You're too kind, Phainon. But seriously, this is a big responsibility.*
| Anaxa (anaxa) | 8 | 0 | 43 | 0.20 | 0% |

**Anaxa** — failed cases (judge < 85):
- 35/100: ctx *(scene: Mission 3: Grove, Wherefore Are the Wise Silent > Anaxa's Alchemical Mes* → expected *My name is Anaxagoras, one of the Seven Sages of the Grove of Epiphany and the f* → model *Echoes are but whispers of what once was. What do you remember?*
- 50/100: ctx *(scene: Mission 9: Passage, Reveal the Past Once More > Epilogue: Anaxa and Cerc* → expected *...What do you mean?* → model *Death is merely the end of a reaction. What matters is the impact one leaves. ко*
- 50/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Olive, Cast to the Conference Chair >* → expected *Oh? Are you saying that the renowned Reason Titan is now admitting a lack of wis* → model *Nothing is impossible. What secrets lie within your history, Cerces?*
- 20/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Olive, Cast to the Conference Chair >* → expected *(No, she can't be. I would know her name if she really were one of the Seven Sag* → model *That does not surprise me.*
- 25/100: ctx *(scene: Complete Dialogue > Sub-Mission 5: Broken Dream, Enlighten From the Beyo* → expected ***Think about the story of the dragon. This stone will lead you to your real hom* → model *Conversion begets understanding; through fire, truth is revealed.*