# Dialogue-Style Report (the Heir-voice standard)

*Generated: 2026-08-10 · model `qwen2.5:14b-instruct`*

Criteria: **STYLE & INTONATION ≥ 85** (word choice, sentence length, rhythm, emotional register, verbal tics) and **CONTENT ≥ 60** (general gist fits the scene, judged holistically — not sentence by sentence). Pass = both bars met.

**Round 1 baseline (2026-08-10): 13 Heirs × 8 cases, `--best-of 3`, temp 0.3.**
Overall **39 / 104 cases pass (38%)** — avg style 68, avg content 60. Content is
largely met (82% of cases ≥ 60); **style is the binding constraint** (only 38% of
cases reach ≥ 85). Full analysis at the bottom of this file.

| Heir | cases | pass | avg style | avg content | pass rate |
|---|---:|---:|---:|---:|---:|
| Aglaea (aglaea) | 8 | 3 | 65 | 58 | 37% |

**Aglaea** — failed cases (style/content):
- style 20 / content 30 → canon ref *For your first time, I shall personally guide you * → act *"... The threads of fate await your touch."*
- style 70 / content 65 → canon ref *Phainon steers his own fate.* → act *"...Indeed, Phainon is the unblemished thread in our tapestry."*
- style 20 / content 30 → canon ref *He openly dismisses people's faith, and questions * → act *"Onward, then. To other threads we must attend."*
- style 70 / content 65 → canon ref *Whether you wish to break free from death or not, * → act *"...Proceed, Castorice. May your path be guided by the threads of fate*
| Anaxa (anaxa) | 8 | 3 | 76 | 65 | 37% |

**Anaxa** — failed cases (style/content):
- style 70 / content 65 → canon ref *Rule number two: Never interrupt me. Silence is go* → act *Rule number two: Listen closely and ask questions wisely.*
- style 60 / content 70 → canon ref *My story ends here. Now, it's time for you to tell* → act *"Hmm...?"*
- style 70 / content 65 → canon ref *...Just like the Flame-Chase Journey of today. Amp* → act *"I'm certain of this now: Before the Titans that we are well acquainte*
- style 70 / content 65 → canon ref *We should allow the children of humanity who come * → act *"...Let us delve into the depths of this mystery together."*
| Castorice (castorice) | 8 | 5 | 82 | 62 | 62% |

**Castorice** — failed cases (style/content):
- style 70 / content 65 → canon ref *An abrupt ending to an epic that has barely begun * → act *Lord Phainon. Kindly keep five paces distance.*
- style 70 / content 40 → canon ref *...* → act *"...The weight of such a decision..."*
- style 70 / content 65 → canon ref *But I know this runs counter to your wishes. So lo* → act *"...Someone must face 'Death' to ensure peace for Okhema."*
| Cerydra (cerydra) | 8 | 5 | 77 | 64 | 62% |

**Cerydra** — failed cases (style/content):
- style 70 / content 65 → canon ref *Very good, Deliverer, you have courage! To say suc* → act ***Cerydra:** So, you seek to wield "Law" against fate itself? Intrigui*
- style 70 / content 65 → canon ref ***The one who wishes to bear Law must purge this w* → act *"...The game is not about avoiding sacrifice, Hysilens. It's about mak*
- style 40 / content 60 → canon ref *Hah...* → act *"Then let us prepare for our grand finale, Dux Helkolithist."*
| Cipher (cipher) | 8 | 1 | 63 | 64 | 12% |

**Cipher** — failed cases (style/content):
- style 70 / content 65 → canon ref *Give me a reason why you're bowing your noble head* → act *Hmm... Fine, I'll hear you out. But no promises, Seamstress.*
- style 60 / content 70 → canon ref *No need. I already told her. She's fine with it.* → act *"Let's get moving, shall we? Time waits for no thief."*
- style 40 / content 60 → canon ref *I sure love your arrogance, Gray Mystery~* → act *"...You see, it's all about playing with people's minds."*
- style 70 / content 65 → canon ref *...Goodbye, Aglaea.* → act *"...You always know how to make an exit, don't you?"*
| Cyrene (cyrene) | 8 | 2 | 53 | 43 | 25% |

**Cyrene** — failed cases (style/content):
- style 70 / content 40 → canon ref *Huh? She disappeared just like that?* → act *"...Mem?"*
- style 40 / content 30 → canon ref *Chief... you mean Dolimem?* → act *"...Mem?"*
- style 30 / content 20 → canon ref *"Lygus" is the mastermind behind it, the one who's* → act *"...Mem?"*
- style 40 / content 60 → canon ref *But that's actually gonna be our "shortcut," right* → act *"Guess it's time to see what kind of reception awaits us."*
| Dan Heng • Permansor Terrae (dan-heng-permansor-terrae) | 8 | 4 | 74 | 59 | 50% |

**Dan Heng • Permansor Terrae** — failed cases (style/content):
- style 70 / content 65 → canon ref *Plenty of questions are still up in the air, but m* → act *"...Let's focus on what lies ahead."*
- style 40 / content 30 → canon ref *I was organizing logs. I also asked Hyacine for so* → act *"...March 7th is with us again. Good to have you back."*
- style 70 / content 65 → canon ref *I don't understand... Does the Council of Elders p* → act *"...But the path is not so simple."*
- style 70 / content 65 → canon ref *It tells me to commit one final act of treason: En* → act *"... The weight of the earth rests upon us now."*
| Evernight (evernight) | 8 | 1 | 56 | 57 | 12% |

**Evernight** — failed cases (style/content):
- style 40 / content 65 → canon ref *A planet not recorded in the data bank and a world* → act *Indeed. A blank canvas awaits, ripe for discovery. ♭*
- style 30 / content 40 → canon ref *You've seen what's on the other side?* → act *They seek to distort reality itself... ♭*
- style 70 / content 65 → canon ref *You walked every inch of this world in 97 days, bu* → act *"97 days." ♭*
- style 40 / content 65 → canon ref *No.* → act *"...Don't worry, I will guard the path of Trailblaze for you... at any*
| Hyacine (hyacine) | 8 | 5 | 73 | 64 | 62% |

**Hyacine** — failed cases (style/content):
- style 60 / content 70 → canon ref *Hehe, have you forgotten that you're talking to th* → act *"I'll be fine. Let's find those documents and bring some closure to th*
- style 40 / content 60 → canon ref *For the Flame-Chase Journey is nearing its perfect* → act *"...It's an honor to carry on your legacy, Lord Crispus."*
- style 40 / content 60 → canon ref *After staying here, I began to discover that there* → act *"Good work, everyone! Let's keep pushing and defeat the final opponent*
| Hysilens (hysilens) | 8 | 2 | 71 | 64 | 25% |

**Hysilens** — failed cases (style/content):
- style 70 / content 65 → canon ref *You mean Phainon? Such a name could never be your * → act *Khaslana... Your secrets are safe with me, as dark as the deep sea.*
- style 70 / content 65 → canon ref *Alright. There's no rush.* → act *"There is still time. Let's not waste it on idle chatter."*
- style 70 / content 65 → canon ref *Don't worry. I know what you've been waiting for.* → act *"Come over and sit beside me, shall we?"*
- style 70 / content 65 → canon ref *Mother, worry not. We're all children of the sea. * → act *...Our queen, the chalice overflows no more.*
| Mydei (mydei) | 8 | 2 | 62 | 57 | 25% |

**Mydei** — failed cases (style/content):
- style 40 / content 60 → canon ref *Carelessness will be your downfall, "Deliverer"!* → act *"Deliverer, focus on the task at hand."*
- style 70 / content 65 → canon ref *Nikador's soul should be claimed by true warriors.* → act *"...Let us declare no victor and continue on."*
- style 70 / content 65 → canon ref *...?* → act *"...Proceed with caution."*
- style 70 / content 65 → canon ref *Do... whatever... you want...* → act *"...Useless chatter."*
| Phainon (phainon) | 8 | 3 | 64 | 56 | 37% |

**Phainon** — failed cases (style/content):
- style 40 / content 30 → canon ref *Roaming around a place like the Abyss with weapons* → act *"...Dan Heng, stand with me and become a hero."*
- style 70 / content 65 → canon ref *Let's go! We're going to win this competition!* → act *Let's show them what we're made of.*
- style 40 / content 65 → canon ref *A blood-red half-sun hung in the sky, just like on* → act *"...Mydei, let's not dwell on the past. We're stronger together, facin*
- style 30 / content 40 → canon ref *But... now that I'm holding them, they don't seem * → act *For our prophesied tomorrow.*
| Tribbie (tribbie) | 8 | 3 | 69 | 61 | 37% |

**Tribbie** — failed cases (style/content):
- style 40 / content 60 → canon ref *Take care, alright? May Kephale light your path fo* → act *Be careful, Snowy~! Don't let your guard down.*
- style 60 / content 40 → canon ref *Alright, then where will they come from?* → act *...*
- style 60 / content 70 → canon ref *...But Trianne, there's nothing in here.* → act *"...Oronyx, are you there? We need to know what's happening."*
- style 60 / content 70 → canon ref *In the past... When you did smile once in a while,* → act *"...Take a deep breath, Cas. Everything will be fine."*

---

## Analysis — Round 1 baseline (2026-08-10)

**Overall: 39 / 104 cases pass (38%)** under the style standard (style ≥ 85 AND content ≥ 60, judged holistically).

| Metric | Value |
|---|---:|
| Cases | 104 |
| Pass | 39 (38%) |
| Avg style (all Heirs) | 68 |
| Avg content (all Heirs) | 60 |
| Cases with content ≥ 60 | 85 (82%) |
| Cases with style ≥ 85 | 39 (38%) |

**Content is close to the bar; style is the binding constraint.** 82% of replies
already carry the general gist of the scene (content ≥ 60). The gap to the 85%
target lives entirely in **delivery**: only 38% of replies reach the calibrated
"that sounds like them" threshold (the judge scores a true in-voice line 93–100,
an in-voice paraphrase 80–85, and flowery/generic output 10–20).

**The 70/65 plateau.** Most failures are `style 70 / content 65`: the model is
clearly in-character (short, measured, plain) but not a *perfect* register match.
The 70→85 step is the model's core weakness — it takes a strong, distinctive
voice to land there consistently.

**Strongest voices (62% pass):** Castorice (avg style 82), Cerydra (77), Hyacine
(73). These characters have the most distinctive registers in the corpus.

**Weakest (12–25% pass):** Cipher, Evernight (12%); Cyrene (25%, avg style 53,
avg content 43). **Cyrene collapses into echoing its anchors** (`"...Mem?"`
repeated) — the shortest anchor becomes a parrot target, killing both content and
style. Anaxa shows the same micro-collapse (`"Hmm...?"`).

**The three cards with embedded VOICE anchors (Tribbie, Cipher, Anaxa) show no
in-test advantage** — the test injects the same anchors for every Heir, so the
embedded block is not the lever for this gate (it still matters for the deployed
sanctuary: production parity).

**What this implies for the next batch** (per-candidate style ≥ 85 ≈ 15%):

- `--best-of N` alone is not enough — projected pass rates: best-of-5 → ~54%,
  best-of-7 → ~67%, best-of-9 → ~76%. Reaching >85% needs *both* a higher
  best-of **and** a higher per-candidate hit rate.
- Raise per-candidate quality: embed the VOICE block into **all 13 cards**
  (currently only 3), feed **6–8 canon exemplars across moods** (not just the
  first 4), and add an explicit **anti-echo rule** ("never repeat an anchor line
  verbatim") to stop the Cyrene/Anaxa collapse.
- Re-run with `--best-of 5` + those anchors; target >85% pass.