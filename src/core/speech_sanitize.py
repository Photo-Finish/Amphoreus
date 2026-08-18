"""Strip self-narration from Heir speech (Stage 2).

Sanctuary replies must be the words an Heir would actually say. Instruct
models still wrap dialogue in novel tags even after the sanctuary prompt
forbids it — ``"Exactly," I reply with a slight nod.`` This post-processor
unwraps that wrapping. Real first-person speech (``I went to Okhema``,
``I haven't heard from Cyrene``) is kept. Voice marks (Cyrene ``♪``,
Evernight ``♭``) are kept. The world-engine chronicle is not passed through
here.
"""

from __future__ import annotations

import re

_SPEECH_VERBS = (
    r"(?:reply|respond|say|begin|continue|add|ask|answer|"
    r"note|murmur|whisper|offer|return|counter|agree)"
)

# "line," I reply with a nod. "rest"  OR  "Hyacine," I continue …, "do you…"
_INTERRUPTED_QUOTE = re.compile(
    r'["“]([^"”]*?)["”]\s*'
    r"I\s+" + _SPEECH_VERBS + r"\b[^\"“”]*?"
    r'["“]([^"”]+)["”]',
    re.IGNORECASE | re.DOTALL,
)

_QUOTE_THEN_TAG = re.compile(
    r'["“]([^"”]+)["”]\s*,?\s*'
    r"I\s+" + _SPEECH_VERBS + r"\b(?:[^.\"“”\n]*?)(?:[.!?]|$)",
    re.IGNORECASE,
)

# *Silent contemplation* / *smiles* — not Cyrene's ♪ which lives outside asterisks
_ASTERISK_BEAT = re.compile(r"\*[^*\n]{1,80}\*")

# Whole-sentence stage directions (after quotes have been unwrapped)
_STAGE_SENTENCE = re.compile(
    r"^(?:"
    r"I pause\b"
    r"|I (?:reply|respond)\b"
    r"|I say(?:\s*,|\s+with\s+|\s+warmly|\s+softly|\s+gently|"
    r"\s+quietly|\s+firmly|\s+my\b)"
    r"|I (?:begin|continue|add)(?:\s*,|\s+with\s+|\s+gently|"
    r"\s+softly|\s+slowly|\s+quietly)"
    r"|I (?:nod|smile|grin|frown|sigh|shrug)\b"
    r"|I incline my (?:head|chin)\b"
    r"|I (?:offer|give) a\b.{0,48}(?:nod|smile|look|glance|hand)\b"
    r"|I let my words hang\b"
    r"|I step (?:forward|back|closer|slightly)\b"
    r"|I extend my (?:hand|arm)\b"
    r"|My (?:tone|gaze|expression)\b"
    r"|My voice (?:carries|remains|stays|softens|hardens|is|grows)\b"
    r"|My words seem\b"
    r"|He (?:hesitates|nods|turns|smiles|frowns|sighs|takes|allows|"
    r"lowers|sheathes|extends|steps|looks|says)\b"
    r"|She (?:hesitates|nods|turns|smiles|frowns|sighs|takes|allows|"
    r"lowers|sheathes|extends|steps|looks|says)\b"
    r"|As (?:he|she)\b"
    r")",
    re.IGNORECASE | re.DOTALL,
)

_DETECT = re.compile(
    r"(?:"
    r'["”]\s*,?\s*I\s+(?:reply|respond|say|begin|continue|add)\b'
    r"|\bI reply\b"
    r"|\bI respond with\b"
    r"|\bI pause\b"
    r"|\bmy tone remains\b"
    r"|\bMy gaze\b"
    r"|\bI give a .{0,24}nod\b"
    r"|\bI offer a .{0,36}smile\b"
    r"|\*[A-Za-z][^*]{1,60}\*"
    r")",
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“I])")
_MULTI_NL = re.compile(r"\n{3,}")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


def has_self_narration(text: str) -> bool:
    """True when the reply still wraps speech in stage directions."""
    if not text:
        return False
    return bool(_DETECT.search(text))


def spoken_words(text: str) -> str:
    """Return the Heir's spoken words, without novel tags or beats."""
    if not text or not str(text).strip():
        return text
    original = text
    out = str(text)
    out = _ASTERISK_BEAT.sub(" ", out)
    out = _unwrap_quoted_tags(out)
    out = _drop_stage_sentences(out)
    out = _unwrap_whole_line_quotes(out)
    out = _tidy(out)
    if len(out.strip()) < 8 and len(original.strip()) > 24:
        return original
    return out


def _join_interrupted(match: re.Match) -> str:
    left = match.group(1).strip()
    right = match.group(2).strip()
    if left.endswith(","):
        return f"{left} {right}"
    if left.endswith((".", "!", "?", "…", "...")):
        return f"{left} {right}"
    return f"{left}. {right}"


def _unwrap_quoted_tags(text: str) -> str:
    prev = None
    out = text
    for _ in range(8):
        if out == prev:
            break
        prev = out
        out = _INTERRUPTED_QUOTE.sub(_join_interrupted, out)
        out = _QUOTE_THEN_TAG.sub(lambda m: _bare_quote(m.group(1)), out)
    return out


def _bare_quote(inner: str) -> str:
    spoken = inner.strip()
    if spoken.endswith(","):
        spoken = spoken[:-1].rstrip() + "."
    return spoken


def _drop_stage_sentences(text: str) -> str:
    kept_paras = []
    for para in re.split(r"\n\s*\n", text):
        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(para) if s.strip()]
        if len(sentences) <= 1:
            # A paragraph that is itself one stage beat — or a single line
            # that never ended on .!? (still match the whole paragraph).
            blob = para.strip()
            if blob and _STAGE_SENTENCE.match(blob):
                continue
            if blob:
                kept_paras.append(para.strip())
            continue
        kept = [s for s in sentences if not _STAGE_SENTENCE.match(s)]
        if kept:
            kept_paras.append(" ".join(kept))
    return "\n\n".join(kept_paras)


def _unwrap_whole_line_quotes(text: str) -> str:
    lines = []
    for line in text.split("\n"):
        s = line.strip()
        if len(s) >= 2 and s[0] in "\"“" and s[-1] in "\"”":
            inner = s[1:-1].strip()
            if inner and '"' not in inner and "“" not in inner:
                lines.append(inner)
                continue
        lines.append(line)
    return "\n".join(lines)


def _tidy(text: str) -> str:
    text = _MULTI_NL.sub("\n\n", text)
    text = "\n".join(_MULTI_SPACE.sub(" ", ln).rstrip() for ln in text.split("\n"))
    text = text.strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text
