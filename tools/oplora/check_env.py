"""Smoke-check the Amphoreus OPLoRA training environment."""
from __future__ import annotations

import platform
import sys
from pathlib import Path


def main() -> int:
    print("Python:", sys.version)
    print("Platform:", platform.platform())

    import torch

    print("torch:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if not torch.cuda.is_available():
        print("FAIL: CUDA not available")
        return 1

    print("CUDA device:", torch.cuda.get_device_name(0))
    print("Capability:", torch.cuda.get_device_capability(0))
    free, total = torch.cuda.mem_get_info()
    print(f"VRAM free/total: {free/1024**3:.2f} / {total/1024**3:.2f} GiB")

    x = torch.randn(1024, 1024, device="cuda", dtype=torch.float16)
    y = x @ x.T
    torch.cuda.synchronize()
    print("matmul ok, mean=", float(y.mean()))

    import transformers
    import peft
    import bitsandbytes as bnb
    import trl
    import accelerate
    import datasets

    print("transformers:", transformers.__version__)
    print("peft:", peft.__version__)
    print("bitsandbytes:", bnb.__version__)
    print("trl:", trl.__version__)
    print("accelerate:", accelerate.__version__)
    print("datasets:", datasets.__version__)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from oplora import ModuleSVD, OPLoRAProjector

    w = torch.randn(64, 32, device="cuda")
    u, s, vh = torch.linalg.svd(w.float(), full_matrices=False)
    svd = ModuleSVD(
        name="blk.q_proj",
        u_k=u[:, :4].cpu(),
        v_k=vh.T[:, :4].cpu(),
        s_k=s[:4].cpu(),
        k=4,
    )

    class LoRAPair(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.lora_A = torch.nn.Parameter(torch.randn(8, 32, device="cuda"))
            self.lora_B = torch.nn.Parameter(torch.randn(64, 8, device="cuda"))

    class Block(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.q_proj = LoRAPair()

    class Root(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.blk = Block()

    model = Root()
    for p in model.parameters():
        p.grad = torch.randn_like(p)

    proj = OPLoRAProjector({"blk.q_proj": svd})
    n = proj.project_gradients(model)
    print(f"OPLoRA projector touched {n} grads")
    if n < 2:
        print("FAIL: expected to touch lora_A and lora_B grads")
        return 1
    print("ENV_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
