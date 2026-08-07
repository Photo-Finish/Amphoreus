"""
VectorStore — ChromaDB-backed knowledge base for the Chrysos Heirs.

Builds one ChromaDB collection per character from the databank markdown
corpus and provides similarity retrieval for RAG-grounded responses.

Usage:
    from knowledge.vector_store import VectorStore
    store = VectorStore(persist_dir=".chroma_db", embedding="auto")
    store.build_all()                       # index databank -> per-character collections
    hits = store.query("phainon", "What does he think about the Coreflame?", k=5)
    print(store.counts())
"""

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from ..utils.text_utils import chunk_markdown
from . import kb_builder


class VectorStore:
    """Per-character ChromaDB collections over the Amphoreus databank."""

    def __init__(
        self,
        persist_dir: str = ".chroma_db",
        embedding: str = "local",
        characters_dir: str = "src/characters",
        databank_dir: str = "databank",
    ):
        """
        Args:
            persist_dir: Directory for the persistent ChromaDB store.
            embedding: "local" (chromadb all-MiniLM-L6-v2 ONNX, offline — default),
                       "auto" (OpenAI if key present, else hashing),
                       "openai" (text-embedding-3-small, needs OPENAI_API_KEY),
                       "ollama" (bge-m3 via local Ollama),
                       "hashing" (offline deterministic embeddings, rough).
        """
        self.persist_dir = persist_dir
        self.embedding = embedding
        self.ollama_embedding_model = os.getenv(
            "OLLAMA_EMBEDDING_MODEL", "bge-m3"
        )
        self.characters_dir = Path(characters_dir)
        self.databank_dir = Path(databank_dir)
        self._client = None
        self._embed_fn = None

    # ------------------------------------------------------------------ #
    # Client / embedding setup
    # ------------------------------------------------------------------ #
    def _get_client(self):
        """Lazily create the persistent ChromaDB client."""
        if self._client is None:
            import chromadb

            self._client = chromadb.PersistentClient(path=self.persist_dir)
        return self._client

    def _get_embedding_function(self):
        """Resolve the embedding function for this store."""
        if self._embed_fn is not None:
            return self._embed_fn

        mode = self.embedding
        if mode == "auto":
            mode = "openai" if os.getenv("OPENAI_API_KEY") else "hashing"
        elif mode == "local":
            mode = "local"

        if mode == "openai":
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "Embedding mode 'openai' requires OPENAI_API_KEY. "
                    "Use embedding='hashing' or 'local' for offline operation."
                )
            base_url = os.getenv("OPENAI_BASE_URL")
            self._embed_fn = OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name="text-embedding-3-small",
                **({"api_base": base_url} if base_url else {}),
            )
        elif mode == "local":
            # ChromaDB's default ONNX embedding (all-MiniLM-L6-v2).
            import chromadb.utils.embedding_functions as ef

            self._embed_fn = ef.DefaultEmbeddingFunction()
        elif mode == "ollama":
            # Fully local embeddings via Ollama (e.g. bge-m3).
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            self._embed_fn = _OllamaEmbeddingFunction(
                model=self.ollama_embedding_model, host=host
            )
        else:  # hashing — deterministic, fully offline
            self._embed_fn = _HashingEmbeddingFunction()

        return self._embed_fn

    # ------------------------------------------------------------------ #
    # Building
    # ------------------------------------------------------------------ #
    def build_all(self, progress=None) -> Dict[str, int]:
        """Build (or refresh) a collection for every character card.

        Returns a mapping {character_id: num_documents_indexed}.
        """
        counts: Dict[str, int] = {}
        card_ids = self._list_character_ids()
        for idx, character_id in enumerate(card_ids, start=1):
            count = self.build_character(character_id)
            counts[character_id] = count
            if progress:
                progress(idx, len(card_ids), character_id, count)
            import gc

            gc.collect()
        return counts

    def build_character(self, character_id: str) -> int:
        """Build a single character's collection. Returns document count."""
        sources = kb_builder.collect_sources(character_id, self.databank_dir)
        aliases = kb_builder.character_aliases(character_id)

        documents: List[str] = []
        metadatas: List[dict] = []
        ids: List[str] = []

        for src in sources:
            path: Path = src["path"]
            rel = path.relative_to(self.databank_dir).as_posix()
            try:
                raw = path.read_text(encoding="utf-8")
            except Exception:
                continue

            chunks = chunk_markdown(raw)
            for ci, chunk in enumerate(chunks):
                if src["filter"] and not _mentions_any(chunk, aliases):
                    continue
                documents.append(chunk)
                metadatas.append({"source": rel, "kind": src["kind"]})
                ids.append(f"{character_id}::{rel}::{ci}")

        # Delete and rebuild the collection so stale chunks never linger.
        client = self._get_client()
        try:
            client.delete_collection(character_id)
        except Exception:
            pass

        if not documents:
            return 0

        collection = client.get_or_create_collection(
            name=character_id,
            embedding_function=self._get_embedding_function(),
            metadata={"hnsw:space": "cosine"},
        )
        batch = 64
        for i in range(0, len(documents), batch):
            collection.add(
                ids=ids[i : i + batch],
                documents=documents[i : i + batch],
                metadatas=metadatas[i : i + batch],
            )
            # The chromadb ONNX embedding can accumulate memory across many
            # batches — release it so long builds don't run out of RAM.
            if i % 512 == 0:
                import gc

                gc.collect()
        return len(documents)

    # ------------------------------------------------------------------ #
    # Retrieval
    # ------------------------------------------------------------------ #
    def query(
        self,
        character_id: str,
        question: str,
        k: int = 5,
        threshold: Optional[float] = None,
    ) -> List[dict]:
        """Retrieve the top-k relevant chunks for a character and question.

        Returns a list of dicts: {text, source, kind, distance, score}.
        """
        if not self.is_built(character_id):
            return []

        collection = self._get_client().get_collection(
            name=character_id,
            embedding_function=self._get_embedding_function(),
        )
        try:
            result = collection.query(
                query_texts=[question],
                n_results=k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]

        hits: List[dict] = []
        below: List[dict] = []
        for doc, meta, dist in zip(docs, metas, dists):
            # cosine distance -> similarity score (1 - distance, clipped to [0,1])
            score = max(0.0, min(1.0, 1.0 - float(dist)))
            entry = {
                "text": doc,
                "source": (meta or {}).get("source", "unknown"),
                "kind": (meta or {}).get("kind", "unknown"),
                "distance": round(float(dist), 4),
                "score": round(score, 4),
            }
            if threshold is not None and score < threshold:
                below.append(entry)
            else:
                hits.append(entry)

        # Graceful degradation: never return empty — if nothing cleared the
        # threshold, fall back to the top-k and flag them as low-confidence.
        if not hits and below:
            for entry in below:
                entry["below_threshold"] = True
            return below[:k]
        return hits

    # ------------------------------------------------------------------ #
    # Introspection
    # ------------------------------------------------------------------ #
    def is_built(self, character_id: str) -> bool:
        try:
            self._get_client().get_collection(character_id)
            return True
        except Exception:
            return False

    def counts(self) -> Dict[str, int]:
        """Return {character_id: num_documents} for built collections."""
        result: Dict[str, int] = {}
        for character_id in self._list_character_ids():
            if not self.is_built(character_id):
                continue
            try:
                result[character_id] = self._get_client().get_collection(character_id).count()
            except Exception:
                pass
        return result

    def _list_character_ids(self) -> List[str]:
        return sorted(p.stem for p in self.characters_dir.glob("*.json"))


# ---------------------------------------------------------------------- #
# Offline deterministic embeddings
# ---------------------------------------------------------------------- #
class _OllamaEmbeddingFunction:
    """Local embeddings via Ollama's /api/embed endpoint (e.g. bge-m3)."""

    def __init__(self, model: str = "bge-m3", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def name(self) -> str:
        return f"ollama-{self.model}"

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.embed_documents(input)

    def embed_query(self, input) -> List[float]:
        if isinstance(input, str):
            input = [input]
        return self._embed(input)[0]

    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return self._embed(input)

    def _embed(self, texts: List[str]) -> List[List[float]]:
        import requests

        out: List[List[float]] = []
        batch = 32
        for i in range(0, len(texts), batch):
            resp = requests.post(
                f"{self.host}/api/embed",
                json={"model": self.model, "input": texts[i : i + batch]},
                timeout=120,
            )
            resp.raise_for_status()
            out.extend(resp.json()["embeddings"])
        return out


class _HashingEmbeddingFunction:
    """Deterministic, dependency-free embedding for offline operation.

    Builds a fixed-dimension vector from character n-gram hashes. Quality is
    lower than real semantic embeddings — use 'openai' or 'local' for
    production-grade retrieval.
    """

    def __init__(self, dim: int = 256):
        self._dim = dim

    def name(self) -> str:
        """ChromaDB embedding-function protocol: unique name."""
        return f"hashing-v{self._dim}"

    def __call__(self, input: List[str]) -> List[List[float]]:
        return [self._embed_one(t) for t in input]

    def embed_query(self, input) -> List[float]:
        """ChromaDB query-embedding protocol (accepts str or list[str])."""
        if isinstance(input, str):
            return self._embed_one(input)
        return [self._embed_one(t) for t in input]

    def embed_documents(self, input: List[str]) -> List[List[float]]:
        """ChromaDB document-embedding protocol."""
        return [self._embed_one(t) for t in input]

    def _embed_one(self, text: str) -> List[float]:
        vector = [0.0] * self._dim
        normalized = re.sub(r"\s+", " ", (text or "").lower())
        for n in (1, 2, 3):
            for i in range(len(normalized) - n + 1):
                gram = normalized[i : i + n]
                digest = hashlib.md5(gram.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:4], "big") % self._dim
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[idx] += sign
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector


def _mentions_any(chunk: str, aliases: List[str]) -> bool:
    """Case-insensitive check whether a chunk mentions any alias."""
    lower = chunk.lower()
    return any(alias.lower() in lower for alias in aliases)


# ---------------------------------------------------------------------- #
# CLI entry: python -m src.knowledge.vector_store --build
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the Amphoreus knowledge base.")
    parser.add_argument("--build", action="store_true", help="Build all collections")
    parser.add_argument("--embedding", default="auto", choices=["auto", "openai", "local", "ollama", "hashing"])
    parser.add_argument("--character", default=None, help="Build only one character ID")
    parser.add_argument("--persist-dir", default=".chroma_db")
    args = parser.parse_args()

    store = VectorStore(persist_dir=args.persist_dir, embedding=args.embedding)

    if args.build:
        if args.character:
            n = store.build_character(args.character)
            print(f"Built '{args.character}': {n} documents")
        else:
            counts = store.build_all()
            total = sum(counts.values())
            print(f"Built {len(counts)} collections, {total} documents total.")
            for cid, cnt in sorted(counts.items()):
                print(f"  {cid}: {cnt}")
    else:
        print("Current collections:", json.dumps(store.counts(), indent=2))
