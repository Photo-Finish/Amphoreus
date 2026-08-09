# Model Evaluation — audio / video / picture processing

Considered assessment (2026-08-10) of whether the Sanctuary should adopt
**better models** for vision (pictures/videos), audio (music/voice) and text,
given the hardware and the ~27.5 GB free on `D:`.

## Current stack (19.9 GB in `models/`)

| Role | Model | Size | Notes |
|---|---|---|---|
| Text / chat | `qwen2.5:14b-instruct` | 9.0 GB | The main persona model |
| Vision (pictures/videos) | `qwen2.5vl:7b` | 6.0 GB | `VISION_MODEL` |
| Audio (music/voice-understanding) | `qwen2.5-omni` | 6.2 GB | `AUDIO_MODEL` |
| Speech-to-text | `faster-whisper-base` | 0.15 GB | `STT_MODEL` |

Hardware: RTX 5070 Laptop **8 GB VRAM**, 32 GB RAM, CUDA 12/13.

## The deciding constraint (measured today)

- The 14B text model **cannot currently load** in any configuration:
  - default → `failed to allocate CUDA_Host buffer` (3.4–5.5 GB pinned host RAM);
  - `OLLAMA_GPU_LAYERS=8` and `=0` → `cudaMalloc failed … CUDA0 buffer 4.4 GB`;
  - while the 7B models (`qwen2.5vl:7b`, `qwen2.5-omni`) load fine.
- This worked earlier the same day and the real culprit turned out to be
  **orphaned `llama-server.exe` processes holding VRAM** after force-killing
  Ollama (6.8 GB phantom usage; killing them freed the GPU instantly — see
  `TECHNICAL-BARRIERS.md` §9). Not a permanent hardware/driver limit, and a
  reboot is NOT required.

## Options considered

### Vision (pictures / videos) — current `qwen2.5vl:7b`
| Candidate | Size | Verdict |
|---|---|---|
| **Qwen3-VL-8B** (GGUF) | ~9–10 GB | ✅ Best upgrade *if* we spend disk: better OCR/reasoning, same size class, fits 8 GB VRAM with offload; ~10 GB one-time download (modelscope) |
| Gemma 3 12B (vision) | ~8–9 GB | Acceptable alternative, slightly heavier |
| Qwen2.5-VL-32B | ~20 GB+ | ❌ Too big for disk headroom and 8 GB VRAM |
| InternVL / MiniCPM-V | ~7–10 GB | Possible, but ecosystem support is weaker in Ollama |

### Audio (music understanding) — current `qwen2.5-omni`
| Candidate | Size | Verdict |
|---|---|---|
| **Qwen3-Omni** | likely >20 GB | ❌ Not feasible (disk + VRAM) |
| Qwen2-Audio (7B, audio-only) | ~5 GB | Would lose omni's unified speech+music handling; no clear win |
| keep `qwen2.5-omni` | — | ✅ Recommended — its only quirk is *terse* replies with audio in context (documented in `TECHNICAL-BARRIERS.md` §8) |

### Speech-to-text — current `faster-whisper-base`
| Candidate | Size | Verdict |
|---|---|---|
| `faster-whisper-small` | ~0.5 GB | ✅ Cheap, meaningful accuracy boost; trivial disk cost |
| `faster-whisper-medium` | ~1.5 GB | Fine too if STT quality matters most |

### Text (chat backbone) — current `qwen2.5:14b-instruct`
| Candidate | Size | Verdict |
|---|---|---|
| keep 14B | 9.0 GB | ✅ Best quality; environment issue is transient (reboot) |
| `qwen2.5:7b` / `qwen3:8b` (~5 GB) as a **fallback** | ~5 GB | Worth registering so the sanctuary keeps working if the 14B won't load; small cost |

## Recommendation

1. **Keep the current stack** — it is the verified, working set; the 27.5 GB of
   free disk is best kept as headroom (the whole `models/` is only 19.9 GB and
   re-downloadable per `docs/DOWNLOADS.md`).
2. **If** we do spend disk on one upgrade, the priority is **Qwen3-VL-8B** for
   vision (biggest visible gain per GB), plus **faster-whisper-small** (cheap).
3. **Do not** adopt any >20 GB model (Qwen3-Omni, 32B VL): disk and 8 GB VRAM
   both rule them out.
4. **Robustness**: register a smaller text model (`qwen2.5:7b`) as a fallback
   so a transient 14B load failure (like today's) never takes the whole
   sanctuary offline.
5. **Before any swap**: reboot the machine to clear the current CUDA host-memory
   state, then re-verify the 14B loads; add models one at a time and re-test.
