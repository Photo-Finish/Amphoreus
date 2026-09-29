# Q-sit face-graph matte (trial v2)

Independent trial of the ink-graph / paint-face backdrop eraser.

**Not wired** into Eternal Page (`src/world/eternal_q.py` still reads `../cutouts/`).
Live `cutouts/`, `crops/`, and `_preview/` from `tools/cut_q_program.py` are untouched.

- `cutouts/` — RGBA; official RGB, alpha only
- `_preview/` — magenta-on-#FF00FF composites (the Read tool ignores PNG alpha)
- `debug/` — face labels: green Character₀, red environment, yellow undecided, dark ink

Run: `python tools/matte_q_faces.py` (add `--guests` for optional extras)

Close ornaments (Ica, chimera, crown, hat, tail, Tribbie's swing if held) are
meant to stay. Sofa / ice / window / branch the character sits on are meant to go.
Guests in this folder are extras, not circle bodies.

Known trial limits: 360p sits (Hysilens, Phainon, Anaxa) stay muddy; some sofas
(Evernight, Castorice) and Mydei's cup/fruit may still glue or vanish.
