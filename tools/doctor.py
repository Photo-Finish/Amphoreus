"""doctor.py — read-only preflight check for a fresh install of Project
Amphoreus. Verifies the environment (Python deps), the project layout, Ollama
+ the runtime models, the senses config (.env / SENSES_MODE), the RAG knowledge
base, the per-Heir folders, and the ports. Prints a checklist and the next
steps. Never modifies anything.

USAGE:
    d:/Workspace/.venv/Scripts/python.exe tools/doctor.py
"""

import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # so `src.*` imports work when run as tools/doctor.py
OK = "\u2705"; WARN = "\u26a0\ufe0f"; FAIL = "\u274c"; SKIP = "\u2796"

# Runtime models that must be visible in `ollama list`.
RUNTIME_MODELS = [
    "gemma3:27b", "deepseek-r1-distill:32b", "deepseek-r1-distill:14b",
    "qwen2.5:14b-instruct", "gemma3n", "qwen3-vl:8b", "qwen2.5-omni",
    "qwen2.5vl:7b",
]


def check_deps():
    print("\n[1/6] Python dependencies")
    required = ["dotenv", "streamlit", "chromadb", "PIL", "faster_whisper",
                "pandas", "openai", "av"]
    for mod in required:
        try:
            __import__(mod)
            print(f"  {OK} {mod}")
        except Exception:
            print(f"  {FAIL} {mod} — missing (pip install -r requirements.txt)")


def check_layout():
    print("\n[2/6] Project layout")
    checks = {
        "src/characters (13 cards)": list((ROOT / "src/characters").glob("*.json")),
        "databank/wiki dump": list((ROOT / "databank/wiki").rglob("*.md")),
        "databank/missions canon": list((ROOT / "databank/missions").rglob("*.md")),
        "assets/heirs portraits": list((ROOT / "assets/heirs").glob("*.*")),
        "assets/avatars icons": list((ROOT / "assets/avatars").glob("*.*")),
        "assets/galgame backgrounds": list((ROOT / "assets/galgame").glob("*.jpg")),
        "docs/IMPLEMENTATION.md": [(ROOT / "docs/IMPLEMENTATION.md")],
        "docs/TEACHING.md": [(ROOT / "docs/TEACHING.md")],
    }
    for label, files in checks.items():
        if files:
            print(f"  {OK} {label} ({len(files)})")
        else:
            print(f"  {WARN} {label} — empty (see README / DOWNLOADS)")


def check_ollama():
    print("\n[3/6] Ollama + runtime models")
    import urllib.request

    url = os.environ.get("OPENAI_BASE_URL", "http://localhost:11434").split("/v1")[0]
    try:
        with urllib.request.urlopen(f"{url}/api/version", timeout=6) as r:
            ver = json.loads(r.read().decode("utf-8", "replace")).get("version", "?")
        print(f"  {OK} server reachable at {url} (v{ver})")
    except Exception as e:
        print(f"  {FAIL} server NOT reachable at {url}: {e}")
        print("         Start it:  powershell -File tools\\start_ollama.ps1")
        return
    try:
        with urllib.request.urlopen(f"{url}/api/tags", timeout=8) as r:
            tags = [t["name"] for t in json.loads(r.read().decode("utf-8", "replace")).get("models", [])]
    except Exception as e:
        print(f"  {FAIL} could not list models: {e}")
        return
    for m in RUNTIME_MODELS:
        present = any(m.split(":")[0] in t for t in tags)
        print(f"  {OK if present else WARN} {m}" + ("" if present else " — missing (ollama pull)"))
    if not any("gemma3:27b" in t for t in tags):
        print(f"  {FAIL} gemma3:27b (the Heir voice) is missing — the sanctuary cannot chat.")


def check_senses():
    print("\n[4/6] Senses config (.env / SENSES_MODE)")
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env", override=True)
    except Exception:
        pass
    vision = os.environ.get("VISION_MODEL", "gemma3n (default)")
    audio = os.environ.get("AUDIO_MODEL", "gemma3n (default)")
    mode = os.environ.get("SENSES_MODE", "unified")
    print(f"  {OK} SENSES_MODE={mode}  VISION_MODEL={vision}  AUDIO_MODEL={audio}")
    if not (ROOT / ".env").exists():
        print(f"  {WARN} no .env found — defaults used. Copy .env.example to .env to pick a mode.")


def check_kb():
    print("\n[5/6] RAG knowledge base")
    kb = ROOT / ".chroma_db"
    if not kb.exists():
        print(f"  {WARN} no .chroma_db yet — build it:  python build_kb.py --embedding local")
        return
    try:
        from src.knowledge.vector_store import VectorStore
        store = VectorStore(persist_dir=str(kb), characters_dir=str(ROOT / "src/characters"))
        counts = store.counts()
        n = len([c for c in counts.values() if c])
        total = sum(counts.values())
        print(f"  {OK} ChromaDB present; {n} collections / {total} docs")
        if n < 13:
            print(f"  {WARN} expected 13 collections — rebuild: python build_kb.py --embedding local")
    except Exception as e:
        print(f"  {WARN} could not inspect KB: {e}")


def check_folders():
    print("\n[6/6] Per-Heir folders + ports")
    from src.core.heir_folders import HEIR_FOLDERS
    missing = [f for f in HEIR_FOLDERS.values() if not (ROOT / f).exists()]
    if missing:
        print(f"  {WARN} missing per-Heir folders: {', '.join(missing)} (created on first chat)")
    else:
        print(f"  {OK} all {len(HEIR_FOLDERS)} per-Heir folders present")
    try:
        import socket
        for port, name in ((11434, "Ollama"), (8501, "Streamlit UI")):
            s = socket.socket()
            try:
                s.bind(("127.0.0.1", port))
                print(f"  {OK} port {port} ({name}) free")
            except OSError:
                print(f"  {WARN} port {port} ({name}) in use")
            finally:
                s.close()
    except Exception:
        pass


def main():
    print("Amphoreus preflight — tools/doctor.py (read-only)")
    print(f"repo root: {ROOT}")
    try:
        check_deps()
        check_layout()
        check_ollama()
        check_senses()
        check_kb()
        check_folders()
    except Exception as e:  # noqa: BLE001
        print(f"\n{FAIL} doctor crashed: {e}")
        return 1
    print("\nNext steps if anything is missing:  python -m venv ..\\.venv  →  "
          "pip install -r requirements.txt  →  powershell -File tools\\start_ollama.ps1  →  "
          "python build_kb.py --embedding local  →  python -m streamlit run src/ui_app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
