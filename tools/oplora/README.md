# Optional OPLoRA voice-PEFT stack (not used by Stage-1 RAG runtime).
#
# Disk note (this machine, 2026-08-18): D: ~37 GiB free before install.
# Torch cu128 nightly alone is ~2.8 GiB; leave headroom for one Qwen2.5-7B
# download (~15 GiB safetensors) under D:\hf-cache.
#
# Setup:
#   .\tools\oplora\setup_env.ps1
#   .\.venv-oplora\Scripts\python.exe tools\oplora\check_env.py
#
# Shape SFT data (copies databank → work_copies/, never edits originals):
#   .\.venv-oplora\Scripts\python.exe tools\oplora\shape_training_data.py --clean
#   # outputs → tools/oplora/datasets/*.jsonl + manifest.json
#
# Train:
#   .\.venv-oplora\Scripts\python.exe tools\oplora\train_sft.py --dry-load
#
# Charter: adapters are voice-stability only; RAG remains the scripture path.
