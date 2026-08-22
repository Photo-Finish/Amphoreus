# OPLoRA refine notes

Working adapters under `outputs/heirs/<heir>/adapter/` were verified
2026-08-18 (non-zero LoRA tensors; Phainon generate OK via Visit/OPLoRA path).

## First pass (1 epoch from random LoRA)

| Heir | rows | last loss | mean loss |
|------|------|-----------|-----------|
| Phainon | 1930 | 1.672 | 1.822 |
| Dan Heng | 1108 | 1.666 | 1.960 |
| Aglaea | 802 | 1.702 | 2.061 |
| Castorice | 1307 | 1.707 | 1.864 |
| Cyrene | 1114 | 1.726 | 2.028 |
| Tribbie | 997 | 1.778 | 1.996 |
| Anaxa | 681 | 1.821 | 2.092 |
| Mydei | 613 | 1.850 | 2.130 |
| Hyacine | 608 | 1.988 | 2.244 |
| Hysilens | 324 | 2.038 | 2.394 |
| Evernight | 232 | 2.083 | 2.634 |
| Cerydra | 338 | 2.090 | 2.489 |
| Cipher | 414 | 2.103 | 2.399 |

## Refine run (2026-08-18)

Continue SFT **from** `adapter_v1/` (snapshot of the verified first pass)
into `adapter_v2/`. Does not train from scratch.

- LR `8e-5` (was `1e-4`)
- 2 extra epochs: Evernight, Cerydra, Cipher, Hysilens, Hyacine
- 1 extra epoch: the other eight
- `save_strategy: no` so 8GB disk is not eaten by optimizer checkpoints
- Live `adapter/` is swapped to v2 only when last loss is strictly lower

```
.\.venv-oplora\Scripts\python.exe tools\oplora\train_refine.py
```

Do **not** edit `databank/` or cards — reshape via `shape_training_data.py`
into `work_copies/` only.

## Ensemble / Stage-2 note (2026-08-22)

Adapters remain **voice-stability only** — they stabilize spoken register under
Visit / group load; they do not replace canon. Scripture and lore still come
from the **RAG path**, not from LoRA weights.

Next refine targets **thin sets** (Hysilens, Evernight, Cerydra, Cipher, and
peers with higher residual loss) under **group-chat load**, where ensemble
pressure exposes register drift sooner than 1:1 Visit.

Do **not** overwrite live `adapter/` until last loss on the refine run is
strictly lower than the current verified adapter (same gate as the 2026-08-18
refine protocol).
