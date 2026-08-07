# Where the models come from (verified mirrors)

This machine's direct downloads from `github.com` / `ollama.com` / `huggingface.co`
are throttled to ~10 KB/s. Every model in this project was downloaded through a
**Chinese mirror at ~8–9 MB/s** and is stored locally inside `models/`.

> All of these are open-source model files (Apache-2.0 / MIT); they are stored
> in this repository so the project is self-contained and offline.

## Fast mirrors used

| Mirror | Speed (tested) | Notes |
|---|---|---|
| **ModelScope** (`modelscope.cn`) | ~8.3 MB/s | Chinese model hub; hosts the GGUF files and whisper |
| **gh-proxy.com** (`https://gh-proxy.com/<full-github-url>`) | ~9.1 MB/s | Proxies GitHub release assets (e.g. `OllamaSetup.exe`) |

## Model files & their sources

| Local path (inside `Amphoreus/models/`) | Source | File / size |
|---|---|---|
| `gguf/qwen2.5-14b-instruct-q4_k_m.gguf` | `modelscope.cn/models/Qwen/Qwen2.5-14B-Instruct-GGUF` | `qwen2.5-14b-instruct-q4_k_m.gguf` — 8,988,110,272 B |
| `gguf/Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf` | `modelscope.cn/models/lmstudio-community/Qwen2.5-VL-7B-Instruct-GGUF` | `Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf` — 4,683,072,032 B |
| `gguf/mmproj-model-f16.gguf` | same repo | `mmproj-model-f16.gguf` — 1,354,162,912 B (vision projector) |
| `gguf/Qwen2.5-Omni-7B-Q4_K_M.gguf` | `modelscope.cn/models/ggml-org/Qwen2.5-Omni-7B-GGUF` | `Qwen2.5-Omni-7B-Q4_K_M.gguf` — 4,683,072,384 B |
| `gguf/mmproj-Qwen2.5-Omni-7B-Q8_0.gguf` | same repo | `mmproj-Qwen2.5-Omni-7B-Q8_0.gguf` — 1,548,488,480 B (audio projector) |
| `faster-whisper-base/*` | `modelscope.cn/models/Systran/faster-whisper-base` | `model.bin` (145,217,532 B), `config.json`, `tokenizer.json`, `vocabulary.txt` |
| Ollama installer (installed at `%LOCALAPPDATA%\Programs\Ollama`) | `gh-proxy.com/https://github.com/ollama/ollama/releases/download/v0.32.6/OllamaSetup.exe` | 1,563,278,432 B — SHA256 `526e47db7c295d017e9514df5bb20c6f32b3d1170f2c8bb9c59b53185f5bd6ff` (verified) |

## How to re-download (e.g. on another machine)

```powershell
# ModelScope file listing / download pattern
#   list:  https://modelscope.cn/api/v1/models/<org>/<repo>/repo/files?Recursive=true&PageSize=50&PageNumber=1
#   get:   https://modelscope.cn/models/<org>/<repo>/resolve/master/<file>   (resume with curl -C -)

curl.exe -L -C - -o qwen2.5-14b-instruct-q4_k_m.gguf `
  "https://modelscope.cn/models/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/master/qwen2.5-14b-instruct-q4_k_m.gguf"

# GitHub release asset through the proxy (SHA256-verified)
curl.exe -L -C - -o OllamaSetup.exe `
  "https://gh-proxy.com/https://github.com/ollama/ollama/releases/download/v0.32.6/OllamaSetup.exe"
Get-FileHash OllamaSetup.exe -Algorithm SHA256   # expect 526e47db7c…bd6ff
```

## Re-creating the Ollama models

```powershell
$env:OLLAMA_MODELS = "D:\Workspace\Amphoreus\models\ollama"
ollama create qwen2.5:14b-instruct -f models/Modelfiles/qwen25-14b
ollama create qwen2.5vl:7b        -f models/Modelfiles/qwen25vl-7b
ollama create qwen2.5-omni        -f models/Modelfiles/qwen25-omni
```
