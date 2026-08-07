"""
Build the ChromaDB knowledge base for Project Amphoreus.

Indexes the databank markdown corpus into one collection per Chrysos Heir,
so the chat UI can serve RAG-grounded responses.

Usage:
    python build_kb.py                       # build all collections (auto embeddings)
    python build_kb.py --embedding hashing   # fully offline embeddings
    python build_kb.py --embedding openai    # text-embedding-3-small (needs OPENAI_API_KEY)
    python build_kb.py --embedding local     # chromadb default all-MiniLM-L6-v2
    python build_kb.py --character phainon   # build a single character
    python build_kb.py --status              # show what is already built
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.knowledge.vector_store import VectorStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Amphoreus knowledge base.")
    parser.add_argument(
        "--embedding",
        default="local",
        choices=["auto", "openai", "local", "ollama", "hashing"],
        help="Embedding backend (default: local all-MiniLM-L6-v2 via ONNX, offline)",
    )
    parser.add_argument("--character", default=None, help="Build only one character ID")
    parser.add_argument("--persist-dir", default=".chroma_db", help="ChromaDB directory")
    parser.add_argument("--status", action="store_true", help="Show built collections only")
    args = parser.parse_args()

    store = VectorStore(persist_dir=args.persist_dir, embedding=args.embedding)

    if args.status:
        print(json.dumps(store.counts(), indent=2))
        return

    if args.character:
        count = store.build_character(args.character)
        print(f"Built '{args.character}': {count} documents")
        return

    counts = store.build_all(progress=lambda i, n, cid, cnt: print(f"[{i}/{n}] {cid}: {cnt} docs"))
    total = sum(counts.values())
    print("-" * 50)
    print(f"Built {len(counts)} collections, {total} documents total.")
    for cid, cnt in sorted(counts.items()):
        print(f"  {cid}: {cnt}")
    print("-" * 50)
    print("Start the chat UI with:  streamlit run src/ui_app.py")


if __name__ == "__main__":
    main()
