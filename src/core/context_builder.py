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
        """Retrieve top-k canon excerpts for a character + question."""
        if self.vector_store is None:
            return []
        try:
            return self.vector_store.query(
                character_id,
                question,
                k=k or self.k,
                threshold=self.threshold,
            )
        except Exception:
            return []

    def format_context(self, hits: List[dict]) -> str:
        """Format retrieved excerpts into a 'Knowledge' block for the prompt."""
        if not hits:
            return ""
        lines = [
            "# Knowledge excerpts (canon lore retrieved for this reply)",
            "# Use these only to ground your answer — never contradict them.",
            "",
        ]
        any_low = any(h.get("below_threshold") for h in hits)
        if any_low:
            lines.insert(
                2,
                "# NOTE: the following excerpts are low-confidence matches — prefer your own persona knowledge if they seem irrelevant.",
            )
        for i, hit in enumerate(hits, start=1):
            lines.append(f"[{i}] (source: {hit.get('source', 'unknown')})")
            lines.append(hit.get("text", ""))
            lines.append("")
        return "\n".join(lines)

    def inject_context(self, system_prompt: str, context_text: str) -> str:
        """Append the formatted context block to a system prompt."""
        if not context_text:
            return system_prompt
        return f"{system_prompt}\n\n{context_text}"

    def retrieve_for_chat(self, character_id: str, system_prompt: str, question: str) -> str:
        """One-call helper: retrieve + format + inject. Returns the enriched prompt."""
        if not self.is_available(character_id):
            return system_prompt
        hits = self.retrieve(character_id, question)
        return self.inject_context(system_prompt, self.format_context(hits))
