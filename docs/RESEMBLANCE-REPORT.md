# Dialogue-Resemblance Report (the Heir-model standard)

*Generated: 2026-08-10 · model `qwen2.5:14b-instruct` · pass bar ≥ 85/100 (LLM judge)*

Method: real canon contexts from `personal-memories.md` → the Heir model replies
in character → a strict LLM judge scores meaning/emotion/voice (0-100 each);
embedding cosine (all-MiniLM) reported as a secondary signal. Base
`prompts.system_prompt` only (no voice-digest leakage).

| Heir | cases | pass | avg judge | avg cosine | pass rate |
|---|---:|---:|---:|---:|---:|
| Aglaea (aglaea) | 8 | 0 | 47 | 0.27 | 0% |

**Aglaea** — failed cases (judge < 85):
- 48/100: ctx *(scene: Complete Dialogue > Mission 1 — Silver Chariot, Away to that Blackened L* → expected *Curious about my eyesight? Well, I'm not blind. On the contrary, I can see much * → model *Ah, Dan Heng, ever observant. My vision may be clouded, but the threads of fate *
- 72/100: ctx *(scene: Complete Dialogue > Mission 2 — Distant Travelers, Listen to this World'* → expected *Sink deeper and do this once more. Submerge your wrists in the spirit water. Fam* → model *As the waters part at your command, so too shall the veil between worlds. Let th*
- 65/100: ctx *(scene: Complete Dialogue > Mission 3 — Night Stars, Accompany My Slumber > Calm* → expected *The golden thread hangs unusually silent today, as if the heavens, earth, and oc* → model ***Aglaea:** The tapestry of time weaves its patterns without rest. Even as the d*
- 27/100: ctx *(scene: Complete Dialogue > Mission 7 — A Cleansing of Gold > Go to Marmoreal Ma* → expected *Wait... if my suspicion is correct, are you skulking about in the filth to keep * → model *Certainly, **Bartholos**. Proceed with the mission as planned. Ensure that the a*
- 24/100: ctx *(scene: Mission 3: Grove, Wherefore Are the Wise Silent > Speak with Aglaea (Gro* → expected *Allow me to do the honors. This young lady is Hyacine, assistant lecturer of the* → model *Indeed, Dan Heng, they are. Observing the subtleties within human interaction is*
| Anaxa (anaxa) | 8 | 0 | 53 | 0.22 | 0% |

**Anaxa** — failed cases (judge < 85):
- 35/100: ctx *(scene: Mission 3: Grove, Wherefore Are the Wise Silent > Anaxa's Alchemical Mes* → expected *My name is Anaxagoras, one of the Seven Sages of the Grove of Epiphany and the f* → model *The past is but a dim reflection on the surface of our present actions. What mat*
- 35/100: ctx *(scene: Mission 9: Passage, Reveal the Past Once More > Epilogue: Anaxa and Cerc* → expected *...What do you mean?* → model *Death is but the end of a chapter; a conclusion to one narrative does not negate*
- 60/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Olive, Cast to the Conference Chair >* → expected *Oh? Are you saying that the renowned Reason Titan is now admitting a lack of wis* → model *It seems the Council's secrets are as tightly guarded as ever, Cerces. Your relu*
- 52/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Olive, Cast to the Conference Chair >* → expected *(No, she can't be. I would know her name if she really were one of the Seven Sag* → model *Indeed, Calypso is a name that carries significant weight within the scholarly c*
- 60/100: ctx *(scene: Complete Dialogue > Sub-Mission 5: Broken Dream, Enlighten From the Beyo* → expected ***Think about the story of the dragon. This stone will lead you to your real hom* → model *Indeed, the Philosopher's Stone represents the culmination of wisdom and knowled*
| Castorice (castorice) | 8 | 0 | 58 | 0.20 | 0% |

**Castorice** — failed cases (judge < 85):
- 58/100: ctx *(scene: Complete Dialogue > Mission 1 — Silver Chariot, Away to that Blackened L* → expected *Lord Phainon. And... the two guests. Welcome to Okhema.* → model *The weight of life and death hangs heavy in this place. We must tread carefully *
- 58/100: ctx *(scene: Complete Dialogue > Mission 6 — Kremnos, Cleanse Thy Rusted Blood (I) > * → expected *But if Mem thinks he has some valuable memories, we'd better ask him in person.* → model *Even those with talent can act in darkness. It's a reminder that everyone has th*
- 42/100: ctx *(scene: Complete Dialogue > Mission 8 — Kremnos, Cleanse Thy Rusted Blood (II) >* → expected *I have an agreement with the Titan... The Chrysos Heirs will take away their Cor* → model *The silence is deafening, yet soothing. It is a respite from the relentless clas*
- 58/100: ctx *(scene: Mission 3: Grove, Wherefore Are the Wise Silent > Offer the Golden Bough* → expected *Right, got it...* → model *Ah, I see... The weight of such vows must be heavy indeed.*
- 70/100: ctx *(scene: Complete Dialogue > Sub-Mission 5: Broken Dream, Enlighten From the Beyo* → expected *But before that, we first need to witness what ultimately happened to Lord Gnaeu* → model **softly* Anaxa, remember that sometimes the path to understanding leads us throu*
| Cerydra (cerydra) | 8 | 0 | 55 | 0.29 | 0% |

**Cerydra** — failed cases (judge < 85):
- 35/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Sun, Repel Stars and Pale Moon > Obse* → expected ***Cerydra**. On behalf of my people and this land, greetings, "Deliverer."* → model *The stars may whisper secrets, but it is we who decide whether to heed them or n*
- 58/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Sun, Repel Stars and Pale Moon > Have* → expected *Very good, Deliverer, you have courage! To say such presumptuous things, even kn* → model *Ah, Cyrene, you speak of altering the fabric of existence itself. It is like try*
- 30/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Sun, Repel Stars and Pale Moon > Some* → expected *The guests' patience is running thin. I plan to remove the fantasia and head int* → model *Ah, experimentation indeed. But remember, Lygus, every move on the chessboard ha*
- 58/100: ctx *(scene: Complete Dialogue > Sub-Mission 6: Sea, Bury the Wine-Dark Dreams > List* → expected *You're here, Dux Gladiorum.* → model ***Cerydra:** Hysilens, every move has its reason, even if the pieces cannot see *
- 72/100: ctx *(scene: Complete Dialogue > Sub-Mission 7: Captives, Behold the Expanse Beyond L* → expected *But the order of the cosmos is already set in stone. The old laws decree that on* → model *A queen must sometimes sacrifice her pawns to checkmate her opponent. Yet, it is*
| Cipher (cipher) | 8 | 0 | 40 | 0.16 | 0% |

**Cipher** — failed cases (judge < 85):
- 25/100: ctx *(scene: Complete Dialogue > Sub-Mission 6: Pathstrider, Set Sail Upon the River * → expected *Grumph...* → model *Ah, sleepyhead! You finally decide to join me, huh? Don't worry, I didn’t move f*
- 25/100: ctx *(scene: Complete Dialogue > Sub-Mission 6: Pathstrider, Set Sail Upon the River * → expected *She can always turn back before the end, you know? Maybe she'll remember Trianne* → model *Ah, Aglaea, always the optimist about me, aren’t you? But don’t worry, even if t*
- 60/100: ctx *(scene: Complete Dialogue > Sub-Mission 6: Pathstrider, Set Sail Upon the River * → expected *Alright! Pass me the coin — it's time to get the god's powers going! A fleet-foo* → model **grinning and waving a hand dismissively* Oh come on, Castor! It’s the thought t*
- 60/100: ctx *(scene: Complete Dialogue > Mission 3 — Chest, Bear the Bygone Dust > Flashback:* → expected *Ha, I won them fair and square in a bet. What, do you doubt me?* → model ***Cipher:** Oh, I've got my ways, haven't I? The wind whispers secrets to me, an*
- 50/100: ctx *(scene: Complete Dialogue > Mission 4 — Golden Thread, Relay the Savior's Fate >* → expected *What confidence. You talk as if you have everything in the palm of your hand... * → model *Oh, come on, Phaino! You wound me with such little faith in my ability to say no*
| Cyrene (cyrene) | 8 | 0 | 41 | 0.25 | 0% |

**Cyrene** — failed cases (judge < 85):
- 25/100: ctx *(scene: Complete Dialogue > Mission 1 — Silver Chariot, Away to that Blackened L* → expected *...Mem?* → model **(with a serene smile)* We are prepared, Pom-Pom. Let us proceed with the plan. *
- 50/100: ctx *(scene: Complete Dialogue > Awaken During the Trial — Speak to Mem)
What was sai* → expected *Oronyx... How heartbreaking. Ever since the figure draped in the black cloak rob* → model *> **Cyrene:** Mem, you’re doing wonderfully. And Oronyx, hold on a little longer*
- 60/100: ctx *(scene: Complete Dialogue > Mission 3 — (Side) Hero, Return to That Peace of Hom* → expected *Ah, the blessing of childhood. Believing the gods might not notice our little co* → model ***(with a gentle smile)** Ah, Phainon, you always see right through things. The *
- 58/100: ctx *(scene: Complete Dialogue > Mission 5 — (Side) Hero, Ignite That Primal Sun > Wi* → expected *Alright, alright, let's not make things so gloomy.* → model ***Cyrene:** It means I must do what is necessary, Phainon. For Amphoreus... for *
- 35/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Sun, Repel Stars and Pale Moon > Find* → expected *...I see. No wonder there was a faint smell of rust in the air before I even ent* → model *Ah, Hysilens, I know you mean well, but let's try to find some peace for now, sh*
| Dan Heng • Permansor Terrae (dan-heng-permansor-terrae) | 8 | 0 | 50 | 0.16 | 0% |

**Dan Heng • Permansor Terrae** — failed cases (judge < 85):
- 58/100: ctx *(scene: Complete Dialogue > Mission 1 — Silver Chariot, Away to that Blackened L* → expected *Mr. Mikhail's homeworld. Lushaka was hit by rising sea levels after the Stellaro* → model *Dan Heng nodded thoughtfully at Welt’s words, his eyes cast downward momentarily*
- 35/100: ctx *(scene: Complete Dialogue > Mission 2 — Distant Travelers, Listen to this World'* → expected *You could say she's not very talkative? No, that's not it, she's just a little e* → model ***Dan Heng:** Farewell, Castorice. Take care and remember to rest when you can. *
- 48/100: ctx *(scene: Complete Dialogue > Mission 3 — Night Stars, Accompany My Slumber > Spea* → expected *Keep yourself safe, and work within your capabilities.* → model *> **Dan Heng:** I will make sure to document our journey through Amphoreus, Tria*
- 82/100: ctx *(scene: Mission 8: Throne, End Those Long Years Forlorn > Farewell to the Trailb* → expected *...Rest assured. We'll do everything we can.* → model ***Dan Heng:** Mydei, your faith in us is both a burden and an honor. We will kee*
- 25/100: ctx *(scene: Complete Dialogue > Mission 1 — Hero, Honor That Crimson Call > Screwllu* → expected *At some point earlier, they suddenly froze in place... not moving at all. Like..* → model *We must comply with Lord Phainon’s directive then. Stay vigilant, Guard Mnemosyn*
| Evernight (evernight) | 8 | 0 | 46 | 0.15 | 0% |

**Evernight** — failed cases (judge < 85):
- 50/100: ctx *(scene: Complete Dialogue > Mission 1 — Silver Chariot, Away to that Blackened L* → expected *A planet not recorded in the data bank and a world even Akivili has never set fo* → model *The Eternal Land holds mysteries both enticing and perilous ♭.*
- 40/100: ctx *(scene: Complete Dialogue > Mission 2 — (Side) Mother, Parted by the Turning of * → expected *The Garden's allies... you mean Miss Black Swan?* → model *The faces may change, yet the heart remains ♭.*
- 25/100: ctx *(scene: Complete Dialogue > Sub-Mission 3: Wanderer, Decipher the Waxen Imprints* → expected *This burning Coreflame. This footnote of a transaction. It contains hope... and * → model *This guise grows thin, March 7th. The mask you wear—so cleverly crafted—is about*
- 35/100: ctx *(scene: Complete Dialogue > Mission 1 — Night, Coming Before Dawn Breaks > March* → expected *You walked every inch of this world in 97 days, but unfortunately...* → model *The truth is always a sharp blade, March 7th ♭.*
- 70/100: ctx *(scene: Complete Dialogue > Mission 7 — Great Tomb, Hide the Secrets of Incarnat* → expected *Why should I do that? So you can buy more time and send a message to your compan* → model *Elegance is but a facade in the face of necessity ♭. Ask your questions, and per*
| Hyacine (hyacine) | 8 | 0 | 39 | 0.25 | 0% |

**Hyacine** — failed cases (judge < 85):
- 25/100: ctx *(scene: Mission 3: Grove, Wherefore Are the Wise Silent > Speak with Aglaea (Gro* → expected *Wow, Grayie and Dannie have sharp eyes indeed! You'd make outstanding members of* → model ***Hyacine:** Dan Heng, I understand your concerns, but please don't let our inte*
- 35/100: ctx *(scene: Complete Dialogue > Sub-Mission 3: Papyrus, Read the Blasphemer's Will >* → expected *Events of the past, huh... I was also a child when I looked up at Cerces. Their * → model ***Hyacine:** Ah, I see. Well, let's not dwell on it now. We have more pressing m*
- 40/100: ctx *(scene: Complete Dialogue > Sub-Mission 3: Papyrus, Read the Blasphemer's Will >* → expected *Anaxa said the same thing then.* → model *Dan, I understand Anaxa's perspective, but we must also consider the consequence*
- 30/100: ctx *(scene: Complete Dialogue > Mission 4 — Golden Thread, Relay the Savior's Fate >* → expected *Yes... we witnessed her final moments. I tried to treat her immediately, but eve* → model *I know it’s hard, but we must stay strong for each other. Let’s cleanse ourselve*
- 35/100: ctx *(scene: Complete Dialogue > Mission 7 — Poet, Speak of the Sky Through Me (II) >* → expected *... Am I... the descendant of that nameless Chrysos Heir? Our lineage wasn't fro* → model *I see the weight of history now, Seliose. It's a heavy burden, but one I will ca*
| Hysilens (hysilens) | 8 | 0 | 54 | 0.27 | 0% |

**Hysilens** — failed cases (judge < 85):
- 58/100: ctx *(scene: Complete Dialogue > Mission 5 — (Side) Hero, Ignite That Primal Sun > Ta* → expected *You mean Phainon? Such a name could never be your true one...* → model ***Hysilens:** Khaslana, your name is known, yet it is the heart that resonates w*
- 42/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Sun, Repel Stars and Pale Moon > Meet* → expected *Those are the two spots reserved for you. Please take your seats.* → model *The tides shift, and the past whispers its lessons. Whether we ride the wave or *
- 60/100: ctx *(scene: Complete Dialogue > Sub-Mission 2: Sun, Repel Stars and Pale Moon > Enjo* → expected *What's the matter, guests?* → model ***Hysilens:** The night whispers secrets and tonight, it is offering a toast to *
- 60/100: ctx *(scene: Complete Dialogue > Sub-Mission 5: Nectar, Saturate the Hollow Treecore * → expected *I am a sea siren, a vessel born to contain the tides. Now that my task is done, * → model *The sea swallows all, yet it is not Death; it is the eternal cycle of life and o*
- 35/100: ctx *(scene: Complete Dialogue > Sub-Mission 6: Sea, Bury the Wine-Dark Dreams > List* → expected *You sent me away under the pretense of guarding the rear. Was there... any shred* → model ***Hysilens:** My devotion is not measured by words, but by actions and the music*
| Mydei (mydei) | 8 | 0 | 42 | 0.20 | 0% |

**Mydei** — failed cases (judge < 85):
- 0/100: ctx *(scene: Complete Dialogue > Mission 1 — Silver Chariot, Away to that Blackened L* → expected *Carelessness will be your downfall, "Deliverer"!* → model *"Phainon, your bluntness is noted. We are indeed facing formidable foes, but rem*
- 50/100: ctx *(scene: Complete Dialogue > Mission 4 — Wasteland, Hark Back Glory of Old > Meet* → expected *Since there is no victor, let's continue on—* → model *The past is irrelevant. Focus on the present and what we must achieve. Let us en*
- 60/100: ctx *(scene: Complete Dialogue > Mission 8 — Kremnos, Cleanse Thy Rusted Blood (II) >* → expected *Eager to meet your demise? Very well then, let the trial begin!* → model *Enter, then. Each of you bears the weight of Kremnos' legacy. Let your resolve s*
- 52/100: ctx *(scene: Complete Dialogue > Find the Source of Strife)
What was said around you:* → expected *...Don't you dare speak of her.* → model *Guard your words, Titan. The past is not so easily forgotten, nor forgiven. And *
- 70/100: ctx *(scene: Mission 5: Memories, Veiled in Blazing Mist > Observe Phainon Conversing* → expected *How does one contender alone make a valid competition?* → model ***Mydei:** Your cheer hides a sharp edge, Phainon. Do not let your guard down wh*
| Phainon (phainon) | 8 | 0 | 53 | 0.20 | 0% |

**Phainon** — failed cases (judge < 85):
- 30/100: ctx *(scene: Complete Dialogue > Mission 1 — Silver Chariot, Away to that Blackened L* → expected *You've got something... interesting.* → model ***(Phainon looks up from where he stands with Tribbiani, concern etched on his f*
- 60/100: ctx *(scene: Complete Dialogue > Mission 4 — Wasteland, Hark Back Glory of Old > Cont* → expected *What do you know? We're talking strategy here!* → model *Ha! I'm not giving up, Mydei. Your words just remind me that every challenge is *
- 35/100: ctx *(scene: Complete Dialogue > Mission 5 — Night Veil, Shroud the Silent Past > Con* → expected *Neither of these are paths we can take, and the exit has been concealed from us.* → model *Perhaps they're just delayed or hiding for safety's sake. We can't abandon hope *
- 58/100: ctx *(scene: Mission 6: Passages, Knocking Echoes in Dreams > Keep Observing Phainon * → expected *No, I can't. Why are you asking that?* → model **Phainon smiles wistfully and shakes his head.* No, I can't fly. But I've got my*
- 35/100: ctx *(scene: Complete Dialogue > Mission 4 — Golden Thread, Relay the Savior's Fate >* → expected *I felt the same as all of you initially. I wanted to stand here beside you, to c* → model *In her absence, we are left to pick up the threads of unity and purpose that she*
| Tribbie (tribbie) | 8 | 0 | 49 | 0.26 | 0% |

**Tribbie** — failed cases (judge < 85):
- 35/100: ctx *(scene: Complete Dialogue > Mission 1 — Silver Chariot, Away to that Blackened L* → expected *Phai—non—! Look what you did again! Agh, you even ruined his weapon! This is no * → model *Oh relax, Snowy! We mean no harm. Us and our sisters come from a place where lig*
- 40/100: ctx *(scene: Complete Dialogue > Mission 6 — Kremnos, Cleanse Thy Rusted Blood (I) > * → expected *No need for formalities at a time like this. I trust that you have found a solut* → model *Oh, don't mention it, Snowy! It's much nicer this way, isn't it? Now, let's see *
- 58/100: ctx *(scene: Mission 3: Grove, Wherefore Are the Wise Silent > Leave the Library of P* → expected *Yup! The spindle that Agy gave us is so powerful that Trianne seems to have foun* → model *Heh, sounds like our sister's up to her old tricks again! Let’s head over and se*
- 50/100: ctx *(scene: Mission 6: Passages, Knocking Echoes in Dreams > Find Missing Memories)
* → expected *(All the words are blurred out... Could it be that my memory is fading?)* → model *(We must be patient, the memories will come back when they're ready. Mama always*
- 48/100: ctx *(scene: Mission 6: Passages, Knocking Echoes in Dreams > Have an Audience with O* → expected *Come on... This isn't the right time to be playing games.* → model *We can't know for sure what's in their heart, but we must try harder. Maybe if w*