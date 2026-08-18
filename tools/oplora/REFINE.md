# OPLoRA refine notes (do not overwrite working adapters yet)

Working adapters under `outputs/heirs/<heir>/adapter/` were verified
2026-08-18 (non-zero LoRA tensors; Phainon generate OK via Visit/OPLoRA path).

## Observed

| Heir | rows (approx) | train wall | note |
|------|---------------|------------|------|
| Phainon | 1930 | ~45 min | richest set |
| Evernight | 232 | ~18 min | smallest; highest avg loss in first pass |
| Hysilens | 324 | ~20 min | thin |
| Cipher | 414 | ~21 min | thin |

## Safe next refine (when disk ≥ ~25 GiB free)

1. Copy each current `adapter/` → `adapter_v1/` (keep the verified weights).
2. Retrain weak heirs into `outputs/heirs/<heir>/adapter_v2/` with
   `config_refine_small.yaml` (2 epochs, same r=16, max_seq 512).
3. Health-check + short generate on v2; only then swap `adapter/` → v2.

Do **not** edit `databank/` or cards — reshape via `shape_training_data.py`
into `work_copies/` only.

## Done this round without retrain

- Infer server `local_files_only=True` against `D:\hf-cache` (avoids HF-mirror TLS).
- UI voice-path switch + live RAG and OPLoRA message tests.
