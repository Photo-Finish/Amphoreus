"""
ContextBuilder — assembles RAG context and message payloads for AgentManager.

Retrieves canon excerpts from the per-character ChromaDB collections and
injects them into the system prompt so the LLM answers are grounded in the
verified Amphoreus databank rather than hallucinated lore.

Usage:
    from core.context_builder import ContextBuilder
    builder = ContextBuilder(vector_store)
    hits = builder.retrieve("phainon", "What about the Coreflame?")
    system_prompt = builder.inject_context(base_prompt, builder.format_context(hits))
"""

from typing import List, Optional


class ContextBuilder:
    """Retrieves and formats RAG context for a character conversation."""

    def __init__(self, vector_store=None, k: int = 5, threshold: float = 0.7):
        self.vector_store = vector_store
        self.k = k
        self.threshold = threshold

    # ------------------------------------------------------------------ #
    def is_available(self, character_id: str) -> bool:
        """Whether RAG can serve this character (store present + collection built)."""
        if self.vector_store is None:
            return False
        try:
            return self.vector_store.is_built(character_id)
        except Exception:
            return False

    def retrieve(self, character_id: str, question: str, k: Optional[int] = None) -> List[dict]:
        """Retrieve top-k canon excerpts for a character + question.

        Keyed lorebook entries come **first**: vector search cannot be stopped from
        surfacing Okhema for a question about Kremnos, but a key that actually appears
        in the question is a stronger signal than a cosine distance. Pinned entries
        are capped at two and the vector results fill the rest of the budget.
        """
        limit = k or self.k
        pinned = self.pinned(character_id, question)
        hits: List[dict] = []
        if self.vector_store is not None:
            try:
                hits = self.vector_store.query(
                    character_id,
                    question,
                    k=limit,
                    threshold=self.threshold,
                ) or []
            except Exception:
                hits = []
        merged = pinned + hits
        # dedupe by text: a pinned entry often duplicates a retrieved excerpt
        seen, out = set(), []
        for hit in merged:
            key = str(hit.get("text", ""))[:160]
            if key in seen:
                continue
            seen.add(key)
            out.append(hit)
        return out[:limit]

    def _book_for(self, character_id: str):
        """The keyed lorebook for one Heir, built from their databank profile."""
        import os

        if os.environ.get("AMP_LOREBOOK", "1") in {"0", "off", "false", "False"}:
            return None
        books = getattr(self, "_books", None)
        if books is None:
            books = self._books = {}
        if character_id in books:
            return books[character_id]
        book = None
        try:
            from pathlib import Path

            from src.knowledge.lorebook import from_markdown

            path = (Path(__file__).resolve().parents[2] / "databank" / "chrysos-heirs"
                    / f"{character_id}.md")
            if path.is_file():
                book = from_markdown(path)
        except Exception:
            book = None
        books[character_id] = book
        return book

    def pinned(self, character_id: str, question: str) -> List[dict]:
        """Entries whose keys appear in the question, as retrieval hits."""
        book = self._book_for(character_id)
        if book is None or not question:
            return []
        turns = getattr(self, "_turns", None)
        if turns is None:
            turns = self._turns = {}
        turn = turns.get(character_id, 0)
        turns[character_id] = turn + 1
        out = []
        try:
            for entry in book.activate(question, turn=turn, limit=2):
                out.append({
                    "text": entry.text,
                    "kind": "lorebook",
                    "source": f"lorebook:{entry.title or ', '.join(entry.keys[:2])}",
                    "score": 1.0,
                })
        except Exception:
            return []
        return out

    @staticmethod
    def prefer_voice_hits(hits: List[dict]) -> List[dict]:
        """Stable-reorder: mission dialogue first (voice anchors), then profile, then rest.

        Used when optional skills aid is ON — retrieval strategy for speech style,
        not a persona rewrite.
        """
        if not hits:
            return hits
        # A keyed lorebook match is pinned ahead of everything: it fired because
        # the question named the thing, not because it was nearby in vector space.
        rank = {"lorebook": -1, "mission": 0, "profile": 1, "global": 2}

        def _key(h: dict):
            kind = str(h.get("kind") or "").lower()
            return (rank.get(kind, 3), -float(h.get("score") or 0.0))

        return sorted(hits, key=_key)

    def format_context(self, hits: List[dict], *, voice_bias: bool = False) -> str:
        """Format retrieved excerpts into a 'Knowledge' block for the prompt."""
        if not hits:
            return ""
        if voice_bias:
            hits = self.prefer_voice_hits(hits)
        lines = [
            "# Knowledge excerpts (canon lore retrieved for this reply)",
            "# Use these only to ground your answer — never contradict them.",
            "",
        ]
        if voice_bias:
            lines.insert(
                2,
                "# VOICE: prefer mission dialogue rhythm/diction when speaking; "
                "do not dump lore as an encyclopedia. Match your measured speech first.",
            )
        any_low = any(h.get("below_threshold") for h in hits)
        if any_low:
            lines.insert(
                2,
                "# NOTE: the following excerpts are low-confidence matches — prefer your own persona knowledge if they seem irrelevant.",
            )
        for i, hit in enumerate(hits, start=1):
            kind = hit.get("kind")
            kind_bit = f", kind: {kind}" if kind else ""
            lines.append(f"[{i}] (source: {hit.get('source', 'unknown')}{kind_bit})")
            lines.append(hit.get("text", ""))
            lines.append("")
        return "\n".join(lines)

    def inject_context(self, system_prompt: str, context_text: str) -> str:
        """Append the formatted context block to a system prompt."""
        if not context_text:
            return system_prompt
        return f"{system_prompt}\n\n{context_text}"

    def retrieve_for_chat(
        self,
        character_id: str,
        system_prompt: str,
        question: str,
        *,
        voice_bias: bool = False,
    ) -> str:
        """One-call helper: retrieve + format + inject. Returns the enriched prompt."""
        if not self.is_available(character_id):
            return system_prompt
        hits = self.retrieve(character_id, question)
        return self.inject_context(
            system_prompt, self.format_context(hits, voice_bias=voice_bias)
        )
