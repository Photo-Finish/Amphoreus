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
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
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
        "--init-adapter",
        type=Path,
        default=None,
        help="Continue SFT from an existing LoRA adapter (does not overwrite it).",
    )
    ap.add_argument(
        "--adapter-subdir",
        type=str,
        default="adapter",
        help="Subfolder under output-dir to save the trained adapter.",
    )
    ap.add_argument("--epochs", type=float, default=None, help="Override num_train_epochs")
    ap.add_argument("--lr", type=float, default=None, help="Override learning_rate")
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
    if args.epochs is not None:
        cfg["num_train_epochs"] = float(args.epochs)
    if args.lr is not None:
        cfg["learning_rate"] = float(args.lr)
    if args.init_adapter is not None:
        cfg["init_adapter"] = str(args.init_adapter)
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    adapter_subdir = (args.adapter_subdir or "adapter").strip() or "adapter"
    save_dir = out_dir / adapter_subdir
    if args.heir:
        log.info("=== Heir: %s ===", args.heir)

    tokenizer = AutoTokenizer.from_pretrained(
        cfg["model_name_or_path"],
        trust_remote_code=True,
        local_files_only=True,
    )
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
        local_files_only=True,
    )
    model = prepare_model_for_kbit_training(model)
    if cfg.get("gradient_checkpointing", True):
        model.gradient_checkpointing_enable()

    init_adapter = cfg.get("init_adapter")
    if init_adapter:
        init_path = Path(init_adapter)
        if not (init_path / "adapter_config.json").is_file():
            raise SystemExit(f"init-adapter missing adapter_config.json: {init_path}")
        log.info("Continuing LoRA from %s", init_path)
        model = PeftModel.from_pretrained(model, str(init_path), is_trainable=True)
    else:
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

    save_strategy = str(cfg.get("save_strategy", "steps"))
    sft_kwargs = dict(
        output_dir=str(out_dir),
        num_train_epochs=float(cfg.get("num_train_epochs", 1)),
        per_device_train_batch_size=int(cfg.get("per_device_train_batch_size", 1)),
        gradient_accumulation_steps=int(cfg.get("gradient_accumulation_steps", 8)),
        learning_rate=float(cfg.get("learning_rate", 1e-4)),
        logging_steps=int(cfg.get("logging_steps", 5)),
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
        save_strategy=save_strategy,
    )
    if save_strategy != "no":
        sft_kwargs["save_steps"] = int(cfg.get("save_steps", 50))
        sft_kwargs["save_total_limit"] = int(cfg.get("save_total_limit", 1))
    train_args = SFTConfig(**sft_kwargs)

    trainer = SFTTrainer(
        model=model,
        args=train_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )
    trainer.train()
    save_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(save_dir))
    tokenizer.save_pretrained(str(save_dir))
    losses = [x["loss"] for x in trainer.state.log_history if "loss" in x]
    metrics = {
        "heir": args.heir,
        "init_adapter": cfg.get("init_adapter"),
        "save_dir": str(save_dir),
        "epochs": float(cfg.get("num_train_epochs", 1)),
        "learning_rate": float(cfg.get("learning_rate", 1e-4)),
        "last_loss": losses[-1] if losses else None,
        "mean_loss": (sum(losses) / len(losses)) if losses else None,
        "n_logs": len(losses),
        "global_step": int(getattr(trainer.state, "global_step", 0) or 0),
        "log_history": [
            {"step": x.get("step"), "epoch": x.get("epoch"), "loss": x.get("loss")}
            for x in trainer.state.log_history
            if "loss" in x
        ],
    }
    (save_dir / "refine_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    log.info(
        "Saved adapter → %s last_loss=%s mean_loss=%s",
        save_dir,
        metrics["last_loss"],
        metrics["mean_loss"],
    )
    if projector:
        projector.remove_hooks()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
