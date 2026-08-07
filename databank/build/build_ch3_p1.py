# -*- coding: utf-8 -*-
import os

BUILD = os.path.dirname(__file__)
MISSIONS = os.path.join(BUILD, '..', 'missions')
OUT = os.path.join(MISSIONS, 'chapter-03-through-petals-NEW.md')
OLD = os.path.join(MISSIONS, 'chapter-03-through-petals.md')

f = open(OUT, 'w', encoding='utf-8')
f.write("""# Chapter 3 — Through the Petals in the Land of Repose (v3.2)

> **Version:** 3.2 | **Sub-Missions:** 13 | **Status:** FULL VERBATIM DIALOGUE ✅
> **Source:** Honkai: Star Rail Fandom Wiki — all 13 sub-mission pages
> **Overview:** "Through the Petals in the Land of Repose" chronicles the Chrysos Heirs' trials in the wake of the Sky Titan's fall — Anaxa's fusion with the Reason Coreflame, the trial of Oronyx, the truth of the Flame-Chase prophecy, and the heroes' journey across the River of Souls toward the final confrontation with fate.

---

## Story Recap

While everyone is awaiting the demigod of Strife to emerge from the trial, something unexpected happens. The Trailblaze squad immediately follows Mydei into the trial and rescues Phainon. Just as everyone breathes a sigh of relief, Mydei had to shoulder the burden of Strife, but the Kremnoans would never willingly give up the Coreflame. Meanwhile, Trianne and Castorice are dispatched to the Grove of Epiphany as diplomatic envoys. They encounter the Flame Reaver and rescue Anaxa. Unexpectedly, they encounter the mysterious swordmaster yet again — Trianne sacrifices herself. In order to take back the Coreflame, everyone sets up a plan. Mydei returns as the demigod of Strife and helps reclaim the Coreflame. The group continues the Flame-Chase Journey...

---

# Complete Dialogue

## Sub-Mission 1: Spindle, Laboring to Weave the Tapestry of Time

""")

# Copy the existing Spindle content (everything from "# Complete Dialogue" up to "## End of Chapter 3")
with open(OLD, 'r', encoding='utf-8') as old:
    content = old.read()

start = content.index('# Complete Dialogue')
body = content[start:]
end_marker = '## End of Chapter 3'
if end_marker in body:
    body = body[:body.index(end_marker)]
body = body.rstrip()
# remove a trailing "---" separator if present
if body.endswith('---'):
    body = body[:-3].rstrip()
f.write(body)
f.write('\n\n---\n\n')
f.close()
print("ch3 part 1 done")
