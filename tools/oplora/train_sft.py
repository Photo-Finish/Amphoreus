"""
QLoRA + OPLoRA SFT entry for Amphoreus voice-stability pilots.

Usage (from repo root, after setup_env.ps1):
  .\\.venv-oplora\\Scripts\\python.exe tools\\oplora\\prepare_dataset.py
  .\\.venv-oplora\\Scripts\\python.exe tools\\oplora\\train_sft.py --config tools\\oplora\\config.yaml

Does not wire into the Visit UI yet — training only.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import torch
import yaml
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

# Local import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from oplora import attach_oplora

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("train_sft")


def _load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_jsonl(path: Path) -> Dataset:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        raise SystemExit(f"No rows in {path}. Run prepare_dataset.py first.")
    return Dataset.from_list(rows)


def _format_row(example: dict) -> dict:
    text = (
        f"### Instruction:\n{example['instruction']}\n\n"
        f"### Context:\n{example.get('input', '')}\n\n"
        f"### Response:\n{example['output']}"
    )
    return {"text": text}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=Path(__file__).with_name("config.yaml"))
    ap.add_argument("--dataset", type=Path, default=None, help="Override config dataset_path")
    ap.add_argument("--output-dir", type=Path, default=None, help="Override config output_dir")
    ap.add_argument("--heir", type=str, default=None, help="Label for logs only")
    ap.add_argument(
        "--dry-load",
        action="store_true",
        help="Load tokenizer + 4bit model + OPLoRA hooks, then exit (no train).",
    )
    args = ap.parse_args()

    # Prefer D: cache — keep C: free
    os.environ.setdefault("HF_HOME", r"D:\hf-cache")
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"D:\hf-cache\hub")

    cfg = _load_config(args.config)
    if args.dataset is not None:
        cfg["dataset_path"] = str(args.dataset)
    if args.output_dir is not None:
        cfg["output_dir"] = str(args.output_dir)
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.heir:
        log.info("=== Heir: %s ===", args.heir)

    tokenizer = AutoTokenizer.from_pretrained(cfg["model_name_or_path"], trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.bfloat16 if cfg.get("bnb_4bit_compute_dtype") == "bfloat16" else torch.float16
    bnb_config = None
    if cfg.get("load_in_4bit", True):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=dtype,
            bnb_4bit_quant_type=cfg.get("bnb_4bit_quant_type", "nf4"),
            bnb_4bit_use_double_quant=cfg.get("bnb_4bit_use_double_quant", True),
        )

    log.info("Loading %s (4bit=%s)…", cfg["model_name_or_path"], bool(bnb_config))
    model = AutoModelForCausalLM.from_pretrained(
        cfg["model_name_or_path"],
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=dtype,
    )
    model = prepare_model_for_kbit_training(model)
    if cfg.get("gradient_checkpointing", True):
        model.gradient_checkpointing_enable()

    lora = LoraConfig(
        r=int(cfg.get("lora_r", 16)),
        lora_alpha=int(cfg.get("lora_alpha", 32)),
        lora_dropout=float(cfg.get("lora_dropout", 0.05)),
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=list(cfg.get("target_modules") or ["q_proj", "v_proj"]),
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    projector = None
    if cfg.get("oplora_enabled", True):
        projector = attach_oplora(
            model,
            projection_rank=int(cfg.get("projection_rank", 64)),
            target_substrings=tuple(cfg.get("target_modules") or []),
            use_hooks=True,
        )
        log.info("OPLoRA hooks attached (%d modules)", len(projector.svds))

    if args.dry_load:
        log.info("dry-load OK — exiting before train")
        if projector:
            projector.remove_hooks()
        return 0

    ds_path = Path(cfg["dataset_path"])
    dataset = _load_jsonl(ds_path).map(_format_row)

    # Newer TRL SFTConfig dropped warmup_ratio — use warmup_steps.
    warmup_steps = cfg.get("warmup_steps")
    if warmup_steps is None:
        n = len(dataset)
        bsz = int(cfg.get("per_device_train_batch_size", 1))
        gas = int(cfg.get("gradient_accumulation_steps", 8))
        steps_per_epoch = max(1, (n + bsz - 1) // bsz // max(gas, 1))
        epochs = float(cfg.get("num_train_epochs", 1))
        warmup_steps = max(1, int(float(cfg.get("warmup_ratio", 0.03)) * steps_per_epoch * epochs))

    train_args = SFTConfig(
        output_dir=str(out_dir),
        num_train_epochs=float(cfg.get("num_train_epochs", 1)),
        per_device_train_batch_size=int(cfg.get("per_device_train_batch_size", 1)),
        gradient_accumulation_steps=int(cfg.get("gradient_accumulation_steps", 8)),
        learning_rate=float(cfg.get("learning_rate", 1e-4)),
        logging_steps=int(cfg.get("logging_steps", 5)),
        save_steps=int(cfg.get("save_steps", 50)),
        warmup_steps=int(warmup_steps),
        lr_scheduler_type=cfg.get("lr_scheduler_type", "cosine"),
        optim=cfg.get("optim", "paged_adamw_8bit"),
        bf16=bool(cfg.get("bf16", True)),
        gradient_checkpointing=bool(cfg.get("gradient_checkpointing", True)),
        report_to=cfg.get("report_to", "none"),
        seed=int(cfg.get("seed", 42)),
        max_length=int(cfg.get("max_seq_length", 512)),
        dataset_text_field="text",
        packing=False,
    )

    trainer = SFTTrainer(
        model=model,
        args=train_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(out_dir / "adapter"))
    tokenizer.save_pretrained(str(out_dir / "adapter"))
    log.info("Saved adapter → %s", out_dir / "adapter")
    if projector:
        projector.remove_hooks()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
