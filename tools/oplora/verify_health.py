"""One-shot health check: adapter files + a short Phainon generation."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HOME", r"D:\hf-cache")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"D:\hf-cache\hub")

ROOT = Path(__file__).resolve().parent / "outputs" / "heirs"
HEIRS = [
    "aglaea",
    "anaxa",
    "castorice",
    "cerydra",
    "cipher",
    "cyrene",
    "dan_heng",
    "evernight",
    "hyacine",
    "hysilens",
    "mydei",
    "phainon",
    "tribbie",
]


def check_adapters() -> bool:
    from safetensors.torch import load_file

    ok = True
    print("=== adapter files ===")
    for h in HEIRS:
        cfgp = ROOT / h / "adapter" / "adapter_config.json"
        w = ROOT / h / "adapter" / "adapter_model.safetensors"
        if not cfgp.is_file() or not w.is_file():
            print("MISSING", h)
            ok = False
            continue
        cfg = json.loads(cfgp.read_text(encoding="utf-8"))
        tensors = load_file(str(w))
        lora_keys = [k for k in tensors if "lora_" in k]
        mean_n = sum(float(tensors[k].float().norm()) for k in lora_keys) / max(
            len(lora_keys), 1
        )
        zero = sum(1 for k in lora_keys if float(tensors[k].abs().max()) == 0)
        print(
            f"{h}: peft={cfg.get('peft_type')} r={cfg.get('r')} "
            f"mb={w.stat().st_size/1e6:.1f} tensors={len(lora_keys)} "
            f"mean_norm={mean_n:.4f} zeros={zero} infer={cfg.get('inference_mode')}"
        )
        if cfg.get("peft_type") != "LORA" or mean_n < 1e-6:
            ok = False
    return ok


def generate_phainon() -> str:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    base = "Qwen/Qwen2.5-7B-Instruct"
    adapter = str(ROOT / "phainon" / "adapter")
    tok = AutoTokenizer.from_pretrained(
        adapter, trust_remote_code=True, local_files_only=True
    )
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        base,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        local_files_only=True,
    )
    model = PeftModel.from_pretrained(model, adapter, local_files_only=True)
    model.eval()
    prompt = (
        "### Instruction:\nYou are Phainon, a Chrysos Heir of Amphoreus. "
        "Answer in character in one spoken reply.\n\n"
        "### Context:\nDan Heng: Look out-!\n\n"
        "### Response:\n"
    )
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=64,
            do_sample=True,
            temperature=0.8,
            top_p=0.9,
            pad_token_id=tok.eos_token_id,
        )
    text = tok.decode(out[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
    return text.strip()


def main() -> int:
    if not check_adapters():
        print("ADAPTERS_BAD")
        return 1
    print("ADAPTERS_OK")
    import torch

    print("CUDA", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")
    print("=== phainon generate ===")
    text = generate_phainon()
    print("GEN:", text[:500])
    print("GEN_OK" if text else "GEN_EMPTY")
    return 0 if text else 1


if __name__ == "__main__":
    raise SystemExit(main())
