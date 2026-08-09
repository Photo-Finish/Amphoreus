# Amphoreus — Technical Barriers & How They Were Solved

A running log of the major technical obstacles hit while building the Sanctuary,
what caused them, and exactly how each was solved. Also tracks the task currently
in progress.

> Philosophy: every barrier here was solved **for real** on this machine
> (Windows 11, RTX 5070 Laptop 8 GiB, ~31 GB RAM, disk nearly full). Where a
> workaround is network-specific it is marked as such.

---

## Live status — current task

### 🔄 LLM refinement of Heir personality traits (in progress, 2026-08-10)

**Goal:** let the LLM read each Heir's canon dialogue (`personal-memories.md`) and
refine their personality traits to a deeper, evidence-grounded level — for all 13 Heirs.

**Tool:** `tools/refine_personal_traits.py`

**Progress:** (updated 2026-08-10 ~01:10 — **COMPLETE ✅**)

| # | Heir | status |
|---|------|--------|
| 1–13 | all Heirs | ✅ refined (13/13) |

- All 13 cards refined via `tools/refine_personal_traits.py` (qwen2.5:14b-instruct,
  num_ctx 32768, ~30k chars of canon dialogue per Heir), backups in `.cache/refine-backups/`.
- **Evidence fidelity: 73/73 quotes verbatim** — checked with `--verify` (handles
  blockquote/quote-style and speaker-label differences; two cerydra quotes corrected by
  hand to exact canon after the LLM merged/paraphrased them).
- Live progress display while running: `tools/watch_refine.ps1`
  (`pwsh -NoProfile -File tools\watch_refine.ps1`).
- Preferences merged into each Heir's `preferences.json` (runtime, gitignored)

**Remaining:** commit the refined cards + tools + docs, then push to GitHub (ask user).

**Remaining after the batch finishes:** inspect the diffs of all 13 cards, confirm
evidence quotes are verbatim canon, commit the refined cards + the tool + this doc, push to GitHub.

---

## 1. Network: international sites throttled or blocked

### 1.1 GitHub / HuggingFace / Ollama direct downloads throttled to ~10 KB/s
- **Symptom:** downloads from `github.com`, `huggingface.co`, `ollama.com` crawl at
  ~10 KB/s (a 200 MB file = hours).
- **Root cause:** per-IP throttling / an unstable route to those hosts; even parallel
  connections get 0 bytes.
- **Solution:** verified fast Chinese mirrors:
  - **gh-proxy.com** (`https://gh-proxy.com/<full-github-url>`) — ~9.1 MB/s, supports
    `-r` range requests. Used for the Ollama installer (`OllamaSetup.exe`, SHA256 verified).
  - **modelscope.cn** — ~8.3 MB/s. Used for all GGUF models and faster-whisper.
    - File listing API: `.../api/v1/models/<org>/<repo>/repo/files?Recursive=true&PageSize=50`
    - Download: `.../models/<org>/<repo>/resolve/master/<file>` (resume with `-C -`).
  - **registry.ollama.ai** — fast for model blobs (`ollama pull` works), slow manifests.
- **Dead ends tried:** GitCode (403), Gitee (no releases), Huawei/Tencent/Aliyun mirrors
  (SPA/404), ghproxy.net (~15 KB/s).

### 1.2 `hsr.fandom.com` (Fandom wiki) completely unreachable
- **Symptom:** TCP blackhole — `curl` returns HTTP 000 (never connects), for IPv4 *and*
  IPv6, HTTP and HTTPS, and via several public relays (allorigins 500/522, corsproxy 403,
  r.jina.ai blocked) and the Wayback Machine. Even small API calls fail most of the time
  (occasional tiny successes, large transfers always killed with `SSL: UNEXPECTED_EOF`).
  DNS also resolves to different (poisoned-looking) IPs per resolver.
- **Root cause:** the network blocks the `fandom.com` domains at the TCP level; a
  middlebox randomly kills connections (small requests sometimes slip through).
- **Solution:** the verification tool (`tools/verify_dialogues_against_fandom.py`)
  is built to **auto-discover a working endpoint** (Fandom → `MIRROR_APIS` → public
  relays), caches results offline, and falls back to offline mode with a clear message
  when nothing is reachable. On a network with Fandom access it works out of the box;
  a mirror can be supplied via `--api`.

## 2. Ollama / model deployment

### 2.1 `mmproj` (vision/audio projector) NOT auto-bundled by `ollama create`
- **Symptom:** VL/Omni models created from GGUF had no vision/audio support — the
  projector layer was missing.
- **Root cause:** `ollama create` from a plain GGUF does not attach the `mmproj`
  projector file automatically.
- **Solution:** manual attachment in `tools/attach_mmproj.ps1` — copy the projector
  into the blobs dir and add an `application/vnd.ollama.image.projector` layer to the
  manifest. **Gotcha:** the manifest must be written **without a UTF-8 BOM**, or the
  server dies with `invalid character '´'` (JSON parse error).

### 2.2 14B `ollama create` needs ~18 GB peak (quantize temp)
- **Symptom:** `ollama create` for qwen2.5:14b failed mid-way — the quantize pass needs
  ~18 GB temporary space on an already-full drive.
- **Solution:** skip the quantize pass entirely — `tools/register_gguf_model.ps1`
  manually registers the model (config blob + manifest referencing the existing model
  blob). The pre-quantized GGUF is used as-is.

### 2.3 Ollama server dies with the terminal / tray serves a stale models dir
- **Symptom:** "model not found" 404s, or the server is simply not running — the tray
  app or a prior terminal was serving a different (stale) `OLLAMA_MODELS`.
- **Solution:** `tools/start_ollama.ps1` — kills stale `ollama` processes, starts a
  **detached** `ollama serve` with `OLLAMA_MODELS=models\ollama`, and verifies all three
  models. This is the only reliable way to bring the server up; it does not auto-run
  across boots (documented in README quickstart).

### 2.4 Ollama `/v1` endpoint ignores `num_ctx` (context stays 4096)
- **Symptom:** sending a >4096-token prompt to `qwen2.5:14b-instruct` fails with
  `request (N tokens) exceeds the available context size (4096 tokens)` even when
  `options.num_ctx` is sent to the OpenAI-compatible endpoint.
- **Root cause:** Ollama 0.32.6's `/v1/chat/completions` compatibility layer ignores
  the `options` body field for context sizing.
- **Solution:** use the **native `/api/chat`** endpoint with
  `"options": {"num_ctx": 32768, "num_predict": N}` (stdlib `urllib` in
  `tools/refine_personal_traits.py`). Verified: the native endpoint honors `num_ctx`
  and accepts large prompts. (An earlier attempt to add `extra_body` `num_ctx` to
  `src/core/llm_client.py` was reverted — dead code for Ollama.)

## 3. Disk space

### 3.1 D: drive ran to 0 bytes
- **Symptom:** writes failed; `ollama create` temp failed; system unstable.
- **Root cause:** ~20 GB of models + the user's own ~215 GB+ of files filled the drive.
- **Solution:** deleted the leftover `D:\OllamaSetup.exe` installer (1.45 GB, no longer
  needed — Ollama already installed). ⚠️ No further deletions — the user's files are
  theirs; the ~20 GB of models are required and stay. User should free space themselves
  if more is needed.

## 4. Console / encoding

### 4.1 Emoji / CJK crash on cp1252 console (world engine)
- **Symptom:** `UnicodeEncodeError` when the world engine printed emoji to a
  cp1252 terminal.
- **Solution:** `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` at the top
  of the entry scripts (and the same guard in every new tool).

### 4.2 Inline multi-line `python -c` breaks in PowerShell
- **Symptom:** multi-line `python -c "..."` snippets misbehave under PowerShell quoting.
- **Solution:** write temp `.py` files (or standalone tools) instead of inline snippets.

## 5. RAG / embeddings

### 5.1 ChromaDB ONNX embedding OOM on long builds
- **Symptom:** the local embedding function (all-MiniLM-L6-v2 ONNX) accumulated memory
  across a full 13-collection build → out-of-memory crash mid-build.
- **Solution:** per-character fresh-process builds (`build_kb.py --embedding local
  --character X` in a loop) + `gc.collect()` in the build functions. Rebuilt all 13
  collections = 11,332 docs.

### 5.2 Custom embedding function protocol changed in newer chromadb
- **Symptom:** `AttributeError` with custom embedding functions.
- **Solution:** the custom function must implement `name()`, `__call__`,
  `embed_query(str|list)`, and `embed_documents`; and the collection must be queried
  with the **same** embedding function used at build time.

## 6. GitHub

### 6.1 Push blocked by 20 GB models in history
- **Symptom:** `git push` rejected — files >100 MB (GitHub hard limit); 20 GB also far
  exceeds the free LFS quota (1 GB) and the ~5 GB repo soft limit.
- **Solution:** rebuilt the history as **one clean commit** excluding `models/`
  (gitignored), force-pushed over the scaffold. Models stay local and are re-downloadable
  via `docs/DOWNLOADS.md`. Repo = 164 files / 9.3 MB. Auth via the stored Windows Git
  Credential Manager entry.

## 7. Character / runtime behaviour

### 7.1 Heir drifted to the wrong language (Castorice → Chinese in chronicle)
- **Symptom:** a world-agent reply switched language unexpectedly.
- **Solution:** language guardrails — chat replies in the visitor's language; world
  agents are instructed "Always reply in English."

### 7.2 LLM fabricated subtle details (risk in trait refinement)
- **Symptom/risk:** LLM analysis can invent traits, events, or quotes not in canon.
- **Solution:** strict prompt rules ("derive everything from the dialogue only, never
  invent, quote exact lines as evidence") + post-check: every `evidence` quote is
  verified verbatim against `personal-memories.md` (script + manual spot-check). The
  project charter (`preference_store.py` docstring) also forbids fabricating "hidden
  depths" — depth must come from canon.

---

## Appendix — exact commands & details

Concrete commands behind each entry above (measured/verified on this machine).

### 1.1 Network mirrors

```powershell
# GitHub release asset via gh-proxy (resumable, ~9.1 MB/s):
curl.exe -L -C - "https://gh-proxy.com/https://github.com/ollama/ollama/releases/download/v0.32.6/OllamaSetup.exe" -o OllamaSetup.exe
Get-FileHash OllamaSetup.exe -Algorithm SHA256   # 526E47DB7C295D017E9514DF5BB20C6F32B3D1170F2C8BB9C59B53185F5BD6FF

# ModelScope file listing + download (~8.3 MB/s, resumable):
curl.exe "https://modelscope.cn/api/v1/models/Qwen/Qwen2.5-14B-Instruct-GGUF/repo/files?Recursive=true&PageSize=50&PageNumber=1"
curl.exe -L -C - "https://modelscope.cn/models/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/master/qwen2.5-14b-instruct-q4_k_m.gguf" -o qwen.gguf

# Ollama pull (blobs from registry.ollama.ai are fast):
$env:OLLAMA_MODELS='D:\Workspace\Amphoreus\models\ollama'; ollama pull qwen2.5vl:7b
```

### 1.2 Fandom verification

```powershell
# Probe (expected on this network: HTTP 000 / SSL UNEXPECTED_EOF):
curl.exe --max-time 12 "https://hsr.fandom.com/api.php?action=query&meta=siteinfo&format=json"

# Tool usage — auto-discovers Fandom -> mirrors -> relays, caches, offline fallback:
python tools/verify_dialogues_against_fandom.py                # all 13 Heirs
python tools/verify_dialogues_against_fandom.py --api <mirror>  # force a working endpoint
python tools/verify_dialogues_against_fandom.py --no-fetch      # offline, cache only
```

### 2.1 mmproj attachment

```powershell
powershell -File tools\attach_mmproj.ps1 -ModelName qwen2.5vl:7b -MmprojPath models\gguf\vl\mmproj-model-f16.gguf
```

Steps the script performs: copy the projector into `models\ollama\blobs\sha256-<hash>`;
add a layer `mediaType = application/vnd.ollama.image.projector` to
`manifests\registry.ollama.ai\library\<repo>\<tag>`; **write the manifest WITHOUT a UTF-8
BOM** (`[System.Text.UTF8Encoding]::new($false)`) — a BOM crashes the server JSON parser
with `invalid character '´'`.

### 2.2 14B manual registration (bypasses `ollama create`)

```powershell
powershell -File tools\register_gguf_model.ps1
```

Writes a config blob (`model_format=gguf`, `model_family=qwen2.5`, `model_type=14.8B`,
`file_type=Q4_K_M`) + a v2 docker manifest whose single layer points at the existing
model blob `sha256:6b53d183…` (8,988,110,272 B), under
`manifests\registry.ollama.ai\library\qwen2.5\14b-instruct`. `ollama create` itself needs
~18 GB peak (quantize temp) and failed on the full drive.

### 2.3 Start the Ollama server

```powershell
powershell -ExecutionPolicy Bypass -File tools\start_ollama.ps1
```

Kills every stale `*ollama*` process (the tray app may serve a stale models dir →
"model not found"), starts a **detached** `ollama serve` with
`OLLAMA_MODELS=models\ollama` / `OLLAMA_HOST=127.0.0.1:11434`, then verifies the three
models through `/api/tags`.

### 2.4 Raise the context window (native API)

Ollama 0.32.6's `/v1/chat/completions` ignores `options`, so the context stays at the
server default (4096). The **native** endpoint honours it:

```json
POST http://127.0.0.1:11434/api/chat
{
  "model": "qwen2.5:14b-instruct",
  "messages": [ ... ],
  "stream": false,
  "options": { "num_ctx": 32768, "num_predict": 2400, "temperature": 0.4 }
}
```

Implemented with stdlib `urllib` in `tools/refine_personal_traits.py`.

### 3.1 Disk space

```powershell
Remove-Item D:\OllamaSetup.exe   # freed ~1.45 GB (installer no longer needed)
```

⚠️ Do **not** delete further files — the user's own data and the ~20 GB of models stay.

### 4.1 Console encoding

```python
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # and stderr
```

Added to `src/world/world_engine.py` and every CLI tool (cp1252 console crashes on
emoji/CJK otherwise).

### 5.1 RAG embedding OOM

```powershell
# fresh process per character to avoid chromadb ONNX memory accumulation:
foreach ($c in 'aglaea','anaxa','castorice','cerydra','cipher','cyrene','dan-heng-permansor-terrae','evernight','hyacine','hysilens','mydei','phainon','tribbie') {
  python build_kb.py --embedding local --character $c
}
```

Plus `gc.collect()` in `build_all()`/`build_character()`; rebuilt all 13 collections =
11,332 docs. Custom embedding functions must implement `name()`, `__call__`,
`embed_query`, `embed_documents`, and queries must use the same embedding function.

### 6.1 GitHub push with >100 MB files

```powershell
# models/ is gitignored; rebuild clean single-commit history if blobs were tracked:
git rm -r --cached models; git add -A; git commit -m "..."; git push -u origin main --force
```

GitHub hard limits: regular push rejects files >100 MB; free LFS = 1 GB; repo soft limit
~5 GB. Models (19.9 GB) stay local — re-download per `docs/DOWNLOADS.md`.

### 7.1 Language guardrails

- Chat system prompt: "When you reply, use the same language the visitor speaks to you."
- World-agent system prompt: "Always reply in English." (added to `decide()`/`react()`)

### 7.2 Anti-fabrication in LLM refinement

- Prompt rules: "Derive EVERYTHING strictly from the dialogue. Never invent. Quote exact
  lines as evidence."
- Post-check: every `evidence` quote is grepped back against `personal-memories.md`, e.g.
  `Select-String -Path NeiKos496-Phainon/personal-memories.md -Pattern 'pawns'` (the
  suspected "pawns" quote turned out to be genuine canon, line 318).

---

## How to keep this document honest

- Each entry records: symptom → root cause → verified solution (not theory).
- Network numbers are measured on this machine at the time of writing.
- When a workaround becomes unnecessary (e.g. a mirror dies or a mirror works), update
  the entry rather than adding a new one.
