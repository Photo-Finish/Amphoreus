# RAG skills vs non-skills — speech-style A/B

*Model `qwen2.5:14b-instruct` · skilled variant `refined` · cases 9*

**Verdict:** `NO_CLEAR_WIN`

No clear style win for skilled (refined) (Δ style -1.3, B wins 3 / A wins 2 / ties 4).

| side | avg style | avg content | case wins |
|---|---:|---:|---:|
| A non-skilled | 61.1 | 54.4 | 2 |
| B skilled (refined) | 59.8 | 59.4 | 3 |
| ties | | | 4 |

## Cases

### Phainon [~] — A 65/70 vs B 65/70
- A: That's right, Dan Heng. Safety for all.
- B: That's right, Dan Heng. Everyone to be safe.

### Phainon [~] — A 85/65 vs B 85/65
- A: ...The past haunts me, even now.
- B: ...The past haunts me, Castorice.

### Phainon [B+] — A 60/50 vs B 65/60
- A: In the end, there's only one thing I can trust...
- B: So, what's next? We can't just stand here...

### Tribbie [B+] — A 45/55 vs B 75/60
- A: How is this safe!? Hello, friendly strangers! Let's all simmer down and cool our jets.
- B: This is no way to be treating strangers, Snowy! Apologize already!

### Tribbie [B+] — A 10/10 vs B 30/40
- A: Snowy~! Use your imagination, why don't you?
- B: Snowy~! You must help us show Lord Krateros the truth.

### Tribbie [A+] — A 85/60 vs B 30/60
- A: "...Surrender the Coreflame and carve their star into the sky."
- B: ...Surrender the Coreflame and carve their star into the sky.

### Mydei [A+] — A 85/65 vs B 70/65
- A: Hmph, then let's see if you can handle the real fight.
- B: Hmph, then let's see your true strength, Deliverer.

### Mydei [~] — A 85/70 vs B 88/70
- A: Hmph, then let's not waste time.
- B: Hmph, then let's not waste time.

### Mydei [~] — A 30/45 vs B 30/45
- A: Hmph, then come challenge me fair and square, Deliverer.
- B: Hmph, then come challenge me fair and square.

## How to toggle skills in RAG mode

- Control Panel → **Skills aid (optional)**
- Env: `AMP_SKILLS=1` (on) / `AMP_SKILLS=0` (off)
- File: `world_runtime/amp_skills.json` → `{"enabled": true}`
- Default: **OFF**

