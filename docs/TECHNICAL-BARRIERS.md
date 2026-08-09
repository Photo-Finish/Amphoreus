# Amphoreus — Technical Barriers & How They Were Solved

A running log of the major technical obstacles hit while building the Sanctuary,
what caused them, and exactly how each was solved. Also tracks the task currently
in progress.

> Philosophy: every barrier here was solved **for real** on this machine
> (Windows 11, RTX 5070 Laptop 8 GiB, ~31 GB RAM, disk nearly full). Where a
> workaround is network-specific it is marked as such.

---

## Live status — current task

### ✅ Trait refinement — COMPLETE (2026-08-10)

**Round 1** (LLM, `qwen2.5:14b`): all 13 cards refined from `personal-memories.md` —
73/73 evidence quotes verbatim (`tools/refine_personal_traits.py`, `--verify`).

**Round 2 (fallacy hunt, same day):**
- Attempted an LLM re-audit, but the 14B would not load that day (see §9) and the
  7B fallback's output was unreliable → **reverted**.
- A **deterministic audit** (`tools/audit_card_quotes.py`) verified every quoted
  claim verbatim against the canon databank: 29/34 exact, 5 truncated-but-genuine
  fragments; **2 real fallacies fixed** (castorice + tribbie catchphrases).
  See `docs/FALLACY-REFINEMENT.md`.

**Visual interface:** `src/ui_app.py` now shows an Amphoreus hero banner, per-Heir
portraits (official 立绘 in `assets/heirs/`, fetched from wiki.biligame.com/sr via
`tools/fetch_heir_images.py`), a themed gold-on-dark style, and portraits as chat
avatars.

**Next:** commit + push everything (in progress).

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

## 8. Music perception: an energetic march felt as "sorrow and hope"

**Incident (2026-08-10).** Two Bilibili clips were downloaded and played to
Hysilens through her audio model (`qwen2.5-omni`):

| clip | source | actual piece | Hysilens' first impression |
|---|---|---|---|
| 1 (100 s) | `BV1WK4UzoEea` | Rachmaninoff, Piano Concerto No. 3, 2nd mvt (slow, melancholic) | "part sorrow, part hope" — **correct** |
| 2 (174 s) | `BV1ZV411U7nv` | Johann Strauss II, *Einzugsmarsch* from *Der Zigeunerbaron* (energetic) | "sorrow and hope / longing for home" — **WRONG** |

**Symptom:** an obviously energetic march was perceived as sorrowful/hopeful — a
clear perception error, caught by the visitor who knew the piece.

**Root cause (verified by re-test): prompt anchoring — not the model's ears.**
The test framing injected the previous piece's reading ("you felt it as part
sorrow, part hope") to give "this time" continuity — which primed the model
toward sorrow/hope. Re-tests on the same audio:
- Neutral prompt, same question → "…hopes for the future… Do not give up, my
  friends" (no sorrow/hope).
- With the piece correctly identified as an energetic Strauss march → "vibrant
  rhythm… the ocean's dance… the brass section, like the sun breaking through".

**Contributing constraints (also documented in §2.4 / appendix):**
- The OpenAI-compatible audio endpoint caps context at 4096 tokens (~95 s of
  16 kHz mono audio), so long clips are trimmed. The native `/api/chat` honours
  `num_ctx` but cannot carry audio content (`cannot unmarshal array into …
  content of type string`).
- `qwen2.5-omni` gives short (~1–2 sentence) impressions when audio is in
  context (it wrote a full 138-word paragraph on text alone) and often trails
  off mid-sentence; it perceives tempo/energy but answers tersely.

**Solution / lesson:** never prime a sense-perception prompt with an expected
emotion — let the Heir hear freely, then (optionally) identify the piece.
Hysilens' stored memory of piece 2 was corrected to the energetic reading, and
this is the standing caveat for all future music-appreciation tests.

## 9. 14B model would not load: orphaned llama-server holding VRAM

**Incident (2026-08-10).** `qwen2.5:14b-instruct` returned HTTP 500 on every load
attempt: `failed to allocate CUDA_Host buffer` (3.4–5.5 GB pinned host RAM), and
after restarts `cudaMalloc failed … CUDA0 buffer` (4.4–5.1 GB), while the 7B
models loaded fine. `nvidia-smi` showed **6.8 GB of VRAM "used"** with no
obvious owner.

**Root cause:** **orphaned `llama-server.exe` children.** When the Ollama server
is force-killed (`Stop-Process -Force`), its model-loading child keeps the loaded
model's VRAM forever. Every restart spawned another orphan until the GPU had
~1 GB free — so the 14B's multi-GB allocation failed. Not a driver/reboot issue.

**Fix:** kill the orphans → VRAM dropped 6835→258 MiB → the 14B loaded in ~7 s:
```powershell
Get-Process -Name 'llama-server' -ErrorAction SilentlyContinue | Stop-Process -Force
```
`tools/start_ollama.ps1` now kills `llama-server` alongside `ollama`.

**Lesson:** after any force-kill of Ollama, also kill `llama-server`; check
`nvidia-smi` for phantom VRAM before blaming the model or the driver.

**Deeper follow-up (same day).** The orphans also exhaust **system commit**:
each resident `llama-server` held ~8 GB of commit (charge reached 39.7/40.7 GB,
i.e. 0.7 GB free → even PowerShell threw `OutOfMemoryException`, and pinned
`CUDA_Host` allocations of 3–4 GB failed despite 11 GB free RAM). Killing all
`ollama` + `llama-server` freed commit to ~8.4 GB and VRAM to ~250 MiB.

**Definitive recovery recipe** (works when the 14B refuses to load):
1. `Get-Process -Name '*ollama*','llama-server' | Stop-Process -Force`; wait ~5 s.
2. Verify `nvidia-smi` shows ≤ ~250 MiB and commit free ≥ ~8 GB
   (`(Get-CimInstance Win32_OperatingSystem).FreeVirtualMemory`).
3. Start the server and load the **14B first**, before any other model.
4. If `CUDA_Host buffer` still fails with GPU+commit free → the **CUDA pinned
   (page-locked) pool** is exhausted by today's many load/unload cycles — a
   driver-state issue that only a **reboot** resets (the same model loaded fine
   that morning). Note the 14B's weights (8.4 GB) exceed the 8.15 GB VRAM, so it
   always needs partial host offload → a few GB of free commit are mandatory.

## 10. Visual interface + image acquisition

**What was done (2026-08-10):**
- `tools/fetch_heir_images.py` downloads official character art (立绘) from
  **wiki.biligame.com/sr** (the reachable Chinese HSR wiki — Fandom stays blocked)
  into `assets/heirs/<id>.png` (13 portraits) plus the Amphoreus background
  (`assets/amphoreus_bg.jpg`). biligame's `parse.images` + `imageinfo` API is the
  working path (`pageimages` returned nothing on that wiki).
- `src/ui_app.py` now renders: a hero banner with the Amphoreus background, the
  Heir's portrait beside their name/titles, the portrait as the chat avatar, and
  a themed gold-on-dark style.

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

### Music perception tests (2026-08-10)

```powershell
# download an audio track from Bilibili (yt-dlp, installed in the venv):
python -m yt_dlp -f "ba/b" --no-playlist -o "D:\Workspace\Amphoreus\.cache\music.%(ext)s" "https://www.bilibili.com/video/<BV>"
# decode m4a -> 16 kHz mono WAV (faster-whisper decoder + wave module, no ffmpeg),
# trim to <=90 s, ask via LLMClient.chat_audio:   (see .cache/ask_hysilens*.py)
python D:\Workspace\Amphoreus\.cache\ask_hysilens3b.py
# neutral / identified re-test (diagnosis of the perception error):
python D:\Workspace\Amphoreus\.cache\hysilens_diagnosis.py
```

Caveats encoded in the lesson: `/v1` audio caps at 4096 tokens (~95 s); the
native API cannot carry audio; omni replies tersely with audio in context;
never prime a perception prompt with an expected emotion.

---

## How to keep this document honest

- Each entry records: symptom → root cause → verified solution (not theory).
- Network numbers are measured on this machine at the time of writing.
- When a workaround becomes unnecessary (e.g. a mirror dies or a mirror works), update
  the entry rather than adding a new one.
