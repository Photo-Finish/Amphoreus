# -*- coding: utf-8 -*-
import os
BUILD = os.path.dirname(__file__)
OLD = os.path.join(BUILD, '..', 'missions', 'chapter-01-heroic-saga.md')
OUT = os.path.join(BUILD, '..', 'missions', 'chapter-01-heroic-saga-NEW.md')

with open(OLD, 'r', encoding='utf-8') as f:
    old = f.read()

# Extract the body after "# Complete Dialogue" (line 15 onwards)
marker = '# Complete Dialogue'
idx = old.find(marker)
body = old[idx + len(marker):] if idx != -1 else old

# Rename "## Part N — Title" to "### Title" so they nest under Mission 1
import re
body = re.sub(r'^## Part \d+ — ', '### ', body, flags=re.M)
# Strip the old "## End of Chapter 1" tail
end_marker = '## End of Chapter 1'
eidx = body.find(end_marker)
if eidx != -1:
    body = body[:eidx].rstrip() + '\n'

f = open(OUT, 'a', encoding='utf-8')
f.write("""# Chapter 1 — Heroic Saga of Flame-Chase (v3.0)

> **Version:** 3.0 | **Sub-Missions:** 10 | **Status:** ALL 10/10 MISSIONS WITH FULL DIALOGUE
> **Source:** Honkai: Star Rail Fandom Wiki
> **Characters:** Trailblazer, Pom-Pom, March 7th, Dan Heng, Himeko, Welt, Black Swan, Sunday, Tribbie, Phainon, Aglaea, Mydei, Castorice, Mem, Nikador, Chartonus, Noldus, Virtus, Damionis, Verax Leo, Cerydra, Hyacine, Anaxa, Cipher, Trianne, Trinnon, Oronyx, Thanatos, Zagreus, Aquila, Cerces, Georios, Phagousa, Kephale, Mnestia, Janus, Talanton

---

## Story Recap

A mysterious celestial body entangled by Three Paths appears in the Memokeeper's mirror — Amphoreus, The Eternal Land. The Trailblaze squad's landing is not a smooth one. After surviving the crash, they meet the local Chrysos Heir heroes. They learn the Titans supporting the world are rotting away. In Okhema, the final holy city, the squad gains Aglaea's trust. Facing a threat from beyond the fog, everyone bands together to defeat the Strife Titan Nikador. The Chrysos Heirs resolve to continue their Flame-Chase Journey, while the Trailblazers set out alongside them to face the trials ahead — culminating in the battles to reclaim the Coreflames of Strife, and the final confrontation that sets the stage for the Era Nova.

---

# Complete Dialogue

## Mission 1 — Silver Chariot, Away to that Blackened Land

""")
f.write(body)
f.close()
print("ch1 part 1 done")
