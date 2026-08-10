"""
register_lmstudio_gguf.py — register LM Studio GGUF files into the local Ollama
store WITHOUT duplicating them on disk (a hard link is used for the model blob,
so the file keeps its single copy in D:\\AI Large Language Model Files).

Mirrors the manual registration the project used for qwen2.5:14b
(tools/register_gguf_model.ps1): a config blob + a manifest referencing the
model blob by sha256 digest. This makes the model appear in `ollama list` and
usable through the OpenAI-compatible API.

USAGE
-----
    python tools/register_lmstudio_gguf.py ^
        --gguf "D:\\AI Large Language Model Files\\lmstudio-community\\DeepSeek-R1-Distill-Qwen-32B-GGUF\\DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf" ^
        --name deepseek-r1-distill:32b --family qwen2 --type 32.0B --file-type Q4_K_M

Note: registering writes only manifests (KB). The model itself is loaded into
RAM only when actually used (e.g. by the Ambient Director or a chat call).
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

OLLAMA_MODELS = Path(os.environ.get("OLLAMA_MODELS", r"D:\Workspace\Amphoreus\models\ollama"))


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_no_bom(path: Path, text: str):
    path.write_bytes(text.encode("utf-8"))  # no BOM


def register(gguf: Path, name: str, family: str, model_type: str, file_type: str,
             copy_if_no_hardlink: bool = True) -> bool:
    if not gguf.exists():
        print(f"  ! {gguf} not found")
        return False
    digest = sha256_of(gguf)
    size = gguf.stat().st_size
    print(f"  digest sha256:{digest[:16]}… size {size/1e9:.2f} GB")

    blobs = OLLAMA_MODELS / "blobs"
    blob_path = blobs / f"sha256-{digest}"
    if not blob_path.exists():
        # Hard link first (free — same volume, NTFS), copy as fallback.
        try:
            os.link(gguf, blob_path)
            print(f"  ✓ blob hard-linked (no disk duplication)")
        except OSError:
            if copy_if_no_hardlink:
                print(f"  ~ hard link failed — copying (uses {size/1e9:.2f} GB)")
                import shutil
                shutil.copy2(gguf, blob_path)
            else:
                print("  ! hard link failed and copying disabled")
                return False
    else:
        print(f"  = blob already present")

    config = {
        "model_format": "gguf",
        "model_family": family,
        "model_families": [family],
        "model_type": model_type,
        "file_type": file_type,
        "architecture": "amd64",
        "os": "linux",
        "rootfs": {"type": "layers", "diff_ids": [f"sha256:{digest}"]},
    }
    config_json = json.dumps(config, separators=(",", ":"))
    config_digest = hashlib.sha256(config_json.encode("utf-8")).hexdigest()
    config_blob = blobs / f"sha256-{config_digest}"
    if not config_blob.exists():
        write_no_bom(config_blob, config_json)

    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "digest": f"sha256:{config_digest}",
            "size": len(config_json),
        },
        "layers": [{
            "mediaType": "application/vnd.ollama.image.model",
            "digest": f"sha256:{digest}",
            "size": size,
        }],
    }
    manifest_json = json.dumps(manifest, separators=(",", ":"))
    # name is "namespace:tag" or "name:tag" → registry path is library/<name>
    if ":" in name:
        n, tag = name.split(":", 1)
    else:
        n, tag = name, "latest"
    manifest_path = OLLAMA_MODELS / "manifests" / "registry.ollama.ai" / "library" / n / tag
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_no_bom(manifest_path, manifest_json)
    print(f"  ✓ manifest: {manifest_path}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--name", required=True, help="e.g. deepseek-r1-distill:32b")
    ap.add_argument("--family", default="qwen2")
    ap.add_argument("--type", default="32.0B")
    ap.add_argument("--file-type", default="Q4_K_M")
    ap.add_argument("--no-copy", action="store_true")
    args = ap.parse_args()

    ok = register(
        Path(args.gguf), args.name, args.family, args.type, args.file_type,
        copy_if_no_hardlink=not args.no_copy,
    )
    print("OK" if ok else "FAILED")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
