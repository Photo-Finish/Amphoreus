"""
Text utilities for the Amphoreus knowledge base — markdown-aware chunking.

Used by the RAG pipeline to split the databank markdown corpus into
retrievable chunks before embedding into ChromaDB.
"""

import re
from typing import List


def chunk_markdown(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> List[str]:
    """Split a markdown document into overlapping chunks.

    Splits on markdown headers first, then on paragraphs (blank-line
    separated), then hard-wraps oversized paragraphs at sentence boundaries.
    """
    text = text.strip()
    if not text:
        return []

    sections = _split_by_headers(text)
    chunks: List[str] = []

    for section in sections:
        if len(section) <= chunk_size:
            if section.strip():
                chunks.append(section.strip())
            continue

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section) if p.strip()]
        current = ""
        for para in paragraphs:
            if len(current) + len(para) + 2 <= chunk_size:
                current = f"{current}\n\n{para}".strip()
            else:
                if current:
                    chunks.append(current)
                if len(para) <= chunk_size:
                    current = para
                else:
                    for piece in _wrap_long(para, chunk_size):
                        chunks.append(piece)
                    current = ""
        if current:
            chunks.append(current)

    if overlap > 0 and len(chunks) > 1:
        chunks = _apply_overlap(chunks, overlap)

    # De-duplicate while preserving order
    seen: set = set()
    result: List[str] = []
    for c in chunks:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


def _split_by_headers(text: str) -> List[str]:
    """Split markdown text into sections at each markdown header (``#`` ... ``######``)."""
    lines = text.splitlines()
    sections: List[str] = []
    current: List[str] = []
    for line in lines:
        if re.match(r"^#{1,6}\s", line) and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())
    return [s for s in sections if s]


def _wrap_long(paragraph: str, chunk_size: int) -> List[str]:
    """Wrap a paragraph longer than chunk_size at sentence boundaries."""
    sentences = re.split(r"(?<=[.!?。！？])\s+", paragraph)
    pieces: List[str] = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) + 1 <= chunk_size:
            current = f"{current} {sent}".strip()
        else:
            if current:
                pieces.append(current)
            if len(sent) <= chunk_size:
                current = sent
            else:
                # Sentence itself is too long — hard cut
                pieces.append(sent[:chunk_size])
                current = sent[chunk_size:]
    if current:
        pieces.append(current)
    return pieces


def _apply_overlap(chunks: List[str], overlap: int) -> List[str]:
    """Append the tail of each chunk to the head of the next for continuity."""
    result: List[str] = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            result.append(chunk)
        else:
            tail = chunks[i - 1][-overlap:]
            result.append(f"{tail}\n\n{chunk}")
    return result
