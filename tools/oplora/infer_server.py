"""OPLoRA voice infer server (runs under .venv-oplora, not the Streamlit venv).

Listens on localhost:8765. Loads Qwen2.5-7B-Instruct in 4-bit once, then
swaps Heir LoRA adapters on demand. Keep Ollama's large models unloaded
while this process holds VRAM.

Endpoints:
  GET  /health
  POST /generate  JSON {heir|character_id, messages|prompt, max_new_tokens?}
  POST /unload   free GPU (optional; process stays up)
"""

from __future__ import annotations

import json
import os
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional

os.environ.setdefault("HF_HOME", r"D:\hf-cache")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"D:\hf-cache\hub")

ROOT = Path(__file__).resolve().parents[2]
OPLORA = Path(__file__).resolve().parent
ADAPTERS = OPLORA / "outputs" / "heirs"
BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
HOST = "127.0.0.1"
PORT = int(os.environ.get("AMPHOREUS_OPLORA_PORT", "8765"))

CARD_TO_ADAPTER = {
    "aglaea": "aglaea",
    "anaxa": "anaxa",
    "castorice": "castorice",
    "cerydra": "cerydra",
    "cipher": "cipher",
    "cyrene": "cyrene",
    "dan-heng-permansor-terrae": "dan_heng",
    "dan_heng": "dan_heng",
    "evernight": "evernight",
    "hyacine": "hyacine",
    "hysilens": "hysilens",
    "mydei": "mydei",
    "phainon": "phainon",
    "tribbie": "tribbie",
}

_lock = threading.Lock()
_tok = None
_model = None
_loaded_adapter: Optional[str] = None
_loaded_adapters: set[str] = set()


def _resolve_adapter(heir: str) -> Path:
    key = (heir or "").strip().lower().replace(" ", "_")
    aid = CARD_TO_ADAPTER.get(key, key)
    path = ADAPTERS / aid / "adapter"
    if not (path / "adapter_config.json").is_file():
        raise FileNotFoundError(f"No adapter for '{heir}' at {path}")
    return path


def _ensure_base():
    global _tok, _model
    if _model is not None:
        return
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    print(f"[oplora-infer] loading base {BASE_MODEL} (4-bit)…", flush=True)
    _tok = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if _tok.pad_token is None:
        _tok.pad_token = _tok.eos_token
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    _model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    _model.eval()
    print("[oplora-infer] base ready", flush=True)


def _ensure_adapter(aid: str, path: Path) -> None:
    global _model, _loaded_adapter, _loaded_adapters
    from peft import PeftModel

    _ensure_base()
    if not isinstance(_model, PeftModel):
        print(f"[oplora-infer] attaching first adapter {aid}", flush=True)
        _model = PeftModel.from_pretrained(_model, str(path), adapter_name=aid)
        _loaded_adapters.add(aid)
        _loaded_adapter = aid
        return
    if aid not in _loaded_adapters:
        print(f"[oplora-infer] loading adapter {aid}", flush=True)
        _model.load_adapter(str(path), adapter_name=aid)
        _loaded_adapters.add(aid)
    if _loaded_adapter != aid:
        _model.set_adapter(aid)
        _loaded_adapter = aid


def _messages_to_prompt(messages: list[dict]) -> str:
    """Prefer Qwen chat template; fall back to training-style Instruction block."""
    assert _tok is not None
    try:
        return _tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    except Exception:
        system = ""
        user_bits = []
        for m in messages:
            role = m.get("role", "")
            content = str(m.get("content", ""))
            if role == "system":
                system = content
            elif role in ("user", "assistant"):
                user_bits.append(f"{role}: {content}")
        ctx = "\n".join(user_bits[-6:])
        return (
            f"### Instruction:\n{system or 'You are a Chrysos Heir of Amphoreus.'}\n\n"
            f"### Context:\n{ctx}\n\n"
            f"### Response:\n"
        )


def generate(
    heir: str,
    messages: Optional[list] = None,
    prompt: Optional[str] = None,
    max_new_tokens: int = 256,
) -> dict[str, Any]:
    import torch

    path = _resolve_adapter(heir)
    aid = path.parent.name
    with _lock:
        _ensure_adapter(aid, path)
        assert _tok is not None and _model is not None
        if messages:
            text = _messages_to_prompt(messages)
        else:
            text = prompt or ""
        inputs = _tok(text, return_tensors="pt")
        inputs = {k: v.to(_model.device) for k, v in inputs.items()}
        with torch.no_grad():
            out = _model.generate(
                **inputs,
                max_new_tokens=int(max_new_tokens),
                do_sample=True,
                temperature=0.8,
                top_p=0.9,
                pad_token_id=_tok.eos_token_id,
            )
        prompt_len = inputs["input_ids"].shape[1]
        reply = _tok.decode(out[0][prompt_len:], skip_special_tokens=True).strip()
        return {
            "ok": True,
            "heir": aid,
            "text": reply,
            "adapter": str(path),
            "base": BASE_MODEL,
        }


def unload() -> dict:
    global _tok, _model, _loaded_adapter, _loaded_adapters
    with _lock:
        _tok = None
        _model = None
        _loaded_adapter = None
        _loaded_adapters = set()
        try:
            import torch
            import gc

            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
    return {"ok": True, "unloaded": True}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[oplora-infer] " + (fmt % args) + "\n")

    def _json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return {}

    def do_GET(self):
        if self.path.split("?")[0] in ("/health", "/"):
            self._json(
                200,
                {
                    "ok": True,
                    "service": "amphoreus-oplora-infer",
                    "base_loaded": _model is not None,
                    "adapter": _loaded_adapter,
                    "adapters_loaded": sorted(_loaded_adapters),
                    "port": PORT,
                },
            )
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            if path == "/generate":
                data = self._read_json()
                heir = data.get("heir") or data.get("character_id") or ""
                messages = data.get("messages")
                prompt = data.get("prompt")
                max_new = int(data.get("max_new_tokens") or 256)
                if not heir:
                    self._json(400, {"ok": False, "error": "heir required"})
                    return
                result = generate(heir, messages=messages, prompt=prompt, max_new_tokens=max_new)
                self._json(200, result)
                return
            if path == "/unload":
                self._json(200, unload())
                return
            self._json(404, {"ok": False, "error": "not found"})
        except Exception as e:
            traceback.print_exc()
            self._json(500, {"ok": False, "error": str(e)})


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[oplora-infer] listening on http://{HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[oplora-infer] stop", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
