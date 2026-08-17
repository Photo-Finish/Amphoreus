"""
OPLoRA — Orthogonal Projection LoRA (AAAI paper arXiv:2510.13003).

Constrains LoRA updates away from the top-k singular subspace of each
frozen weight so fine-tuning preserves pre-trained knowledge.

ΔW = P_L @ (B @ A) @ P_R
  P_L = I - U_k U_k^T
  P_R = I - V_k V_k^T

This module attaches SVD caches + gradient hooks to a PEFT LoRA model.
It does not replace RAG; Amphoreus treats OPLoRA as optional voice PEFT.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

DEFAULT_TARGET_SUBSTRINGS = (
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
)


@dataclass
class ModuleSVD:
    """Top-k singular factors for one Linear weight (out, in)."""

    name: str
    u_k: torch.Tensor  # (out, k)
    v_k: torch.Tensor  # (in, k)
    s_k: torch.Tensor  # (k,)
    k: int


def _matched(name: str, needles: Iterable[str]) -> bool:
    return any(n in name for n in needles)


@torch.no_grad()
def compute_module_svd(
    weight: torch.Tensor,
    k: int,
    name: str = "",
) -> ModuleSVD:
    w = weight.detach().float()
    if w.ndim != 2:
        w = w.reshape(w.shape[0], -1)
    max_k = min(w.shape[0], w.shape[1])
    k = max(1, min(k, max_k))
    try:
        u, s, vh = torch.linalg.svd(w, full_matrices=False)
        v = vh.transpose(0, 1)
    except RuntimeError:
        logger.warning("Full SVD failed for %s; using svd_lowrank.", name)
        u, s, v = torch.svd_lowrank(w, q=k)
    return ModuleSVD(
        name=name,
        u_k=u[:, :k].contiguous().cpu(),
        v_k=v[:, :k].contiguous().cpu(),
        s_k=s[:k].contiguous().cpu(),
        k=k,
    )


def collect_base_svds(
    model: nn.Module,
    projection_rank: int = 64,
    target_substrings: Iterable[str] = DEFAULT_TARGET_SUBSTRINGS,
) -> Dict[str, ModuleSVD]:
    """
    SVD of frozen base weights for modules that have LoRA adapters.

    Looks for PEFT-style names containing 'lora_' and resolves the sibling
    base Linear (…base_layer or the parent Linear).
    """
    svds: Dict[str, ModuleSVD] = {}
    seen_linears: Dict[int, str] = {}

    for full_name, module in model.named_modules():
        if not _matched(full_name, target_substrings):
            continue
        if not isinstance(module, nn.Linear):
            # PEFT LoraLayer wraps Linear; prefer base_layer when present
            base = getattr(module, "base_layer", None)
            if not isinstance(base, nn.Linear):
                continue
            linear = base
            key = full_name
        else:
            # Skip LoRA A/B matrices themselves
            if "lora_" in full_name:
                continue
            linear = module
            key = full_name

        lid = id(linear)
        if lid in seen_linears:
            continue
        seen_linears[lid] = key
        logger.info("SVD %s shape=%s k=%s", key, tuple(linear.weight.shape), projection_rank)
        svds[key] = compute_module_svd(linear.weight, projection_rank, name=key)

    if not svds:
        # Fallback: every Linear whose name matches targets
        for full_name, module in model.named_modules():
            if isinstance(module, nn.Linear) and _matched(full_name, target_substrings):
                if "lora_" in full_name:
                    continue
                svds[full_name] = compute_module_svd(
                    module.weight, projection_rank, name=full_name
                )
    return svds


def _parent_lora_key(param_name: str) -> Optional[str]:
    """Map '...layers.0.self_attn.q_proj.lora_A.default.weight' → module stem."""
    if ".lora_" not in param_name:
        return None
    return param_name.split(".lora_")[0]


class OPLoRAProjector:
    """
    After backward, project LoRA parameter gradients so the implied ΔW
    stays in the orthogonal complement of the top-k subspace.

    For ΔW ≈ B @ A (PEFT convention: lora_B @ lora_A scaled), we apply:
      grad_B ← P_L @ grad_B
      grad_A ← grad_A @ P_R
    which is the first-order analogue of constraining ΔW = P_L ΔW P_R.
    """

    def __init__(self, svds: Dict[str, ModuleSVD], device: Optional[torch.device] = None):
        self.svds = svds
        self._cache: Dict[str, Tuple[torch.Tensor, torch.Tensor]] = {}
        self.device = device
        self._hooks: List[torch.utils.hooks.RemovableHandle] = []

    def _projections(self, stem: str, device: torch.device, dtype: torch.dtype):
        if stem not in self.svds:
            # Try suffix match (PEFT renames)
            match = None
            for key in self.svds:
                if key.endswith(stem) or stem.endswith(key) or stem in key or key in stem:
                    match = key
                    break
            if match is None:
                return None
            stem = match
        if stem not in self._cache or self._cache[stem][0].device != device:
            svd = self.svds[stem]
            u = svd.u_k.to(device=device, dtype=dtype)
            v = svd.v_k.to(device=device, dtype=dtype)
            self._cache[stem] = (u, v)
        return self._cache[stem]

    @torch.no_grad()
    def project_gradients(self, model: nn.Module) -> int:
        """Call after loss.backward(), before optimizer.step(). Returns #params touched."""
        touched = 0
        for name, param in model.named_parameters():
            if param.grad is None or not param.requires_grad:
                continue
            if "lora_A" not in name and "lora_B" not in name:
                continue
            stem = _parent_lora_key(name)
            if stem is None:
                continue
            proj = self._projections(stem, param.grad.device, param.grad.dtype)
            if proj is None:
                continue
            u_k, v_k = proj
            g = param.grad
            if "lora_B" in name:
                # g: (out, r)  →  (I - U U^T) g
                g.add_(-u_k @ (u_k.transpose(0, 1) @ g))
                touched += 1
            elif "lora_A" in name:
                # g: (r, in)  →  g (I - V V^T)
                g.add_(-(g @ v_k) @ v_k.transpose(0, 1))
                touched += 1
        return touched

    def attach_backward_hooks(self, model: nn.Module) -> None:
        """Optional: auto-project on each LoRA param backward."""

        def make_hook(param_name: str):
            def _hook(grad: torch.Tensor):
                stem = _parent_lora_key(param_name)
                if stem is None:
                    return grad
                proj = self._projections(stem, grad.device, grad.dtype)
                if proj is None:
                    return grad
                u_k, v_k = proj
                g = grad.clone()
                if "lora_B" in param_name:
                    g = g - u_k @ (u_k.transpose(0, 1) @ g)
                elif "lora_A" in param_name:
                    g = g - (g @ v_k) @ v_k.transpose(0, 1)
                return g

            return _hook

        self.remove_hooks()
        for name, param in model.named_parameters():
            if param.requires_grad and ("lora_A" in name or "lora_B" in name):
                self._hooks.append(param.register_hook(make_hook(name)))
        logger.info("Attached %d OPLoRA gradient hooks", len(self._hooks))

    def remove_hooks(self) -> None:
        for h in self._hooks:
            h.remove()
        self._hooks.clear()


def attach_oplora(
    model: nn.Module,
    projection_rank: int = 64,
    target_substrings: Iterable[str] = DEFAULT_TARGET_SUBSTRINGS,
    use_hooks: bool = True,
) -> OPLoRAProjector:
    """Compute SVDs on the (quantized/base) model and optionally install hooks."""
    svds = collect_base_svds(model, projection_rank, target_substrings)
    if not svds:
        raise RuntimeError(
            "No Linear modules matched for OPLoRA SVD. "
            "Check that PEFT LoRA is applied and target names match."
        )
    projector = OPLoRAProjector(svds)
    if use_hooks:
        projector.attach_backward_hooks(model)
    logger.info("OPLoRA ready: %d modules, k=%d", len(svds), projection_rank)
    return projector
