"""Recursively splits parser-produced sections into token-budgeted, sentence-safe chunks."""

import re

import tiktoken
from pydantic import BaseModel

from financial_rag.config import settings

_ENCODING = tiktoken.get_encoding("cl100k_base")

# Split after sentence-ending punctuation + whitespace, when the next token
# looks like the start of a new sentence (capital letter, digit, quote, paren).
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


class Chunk(BaseModel):
    company: str
    ticker: str
    doc_type: str
    fiscal_period: str
    section: str
    source_path: str
    chunk_index: int
    text: str
    token_count: int


def _token_count(text: str) -> int:
    return len(_ENCODING.encode(text))


def _split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        sentences.extend(s.strip() for s in _SENTENCE_SPLIT_RE.split(paragraph) if s.strip())
    return sentences


def _hard_split_long_sentence(sentence: str, max_tokens: int) -> list[str]:
    """Fallback for a single sentence longer than the chunk budget: split on
    token boundaries. The only path that can break mid-sentence."""
    tokens = _ENCODING.encode(sentence)
    return [
        _ENCODING.decode(tokens[i : i + max_tokens]) for i in range(0, len(tokens), max_tokens)
    ]


def _pack_sentences(
    sentences: list[str], chunk_size_tokens: int, chunk_overlap_tokens: int
) -> list[str]:
    """Greedily pack sentences into ~chunk_size_tokens chunks, carrying the
    trailing ~chunk_overlap_tokens worth of sentences into the next chunk."""
    units: list[tuple[str, int]] = []
    for sentence in sentences:
        n = _token_count(sentence)
        if n > chunk_size_tokens:
            units.extend(
                (piece, _token_count(piece))
                for piece in _hard_split_long_sentence(sentence, chunk_size_tokens)
            )
        else:
            units.append((sentence, n))

    chunks: list[str] = []
    current: list[tuple[str, int]] = []
    current_tokens = 0

    for sentence, n in units:
        if current and current_tokens + n > chunk_size_tokens:
            chunks.append(" ".join(s for s, _ in current))

            overlap: list[tuple[str, int]] = []
            overlap_tokens = 0
            for s, tok in reversed(current):
                if overlap_tokens + tok > chunk_overlap_tokens:
                    break
                overlap.insert(0, (s, tok))
                overlap_tokens += tok

            current, current_tokens = overlap, overlap_tokens

        current.append((sentence, n))
        current_tokens += n

    if current:
        chunks.append(" ".join(s for s, _ in current))

    return chunks


def chunk_sections(
    sections: list[dict],
    *,
    company: str,
    ticker: str,
    doc_type: str,
    fiscal_period: str,
    source_path: str,
    chunk_size_tokens: int | None = None,
    chunk_overlap_tokens: int | None = None,
) -> list[Chunk]:
    """Stage 2: recursively split each parser-produced section into
    ~chunk_size_tokens chunks with chunk_overlap_tokens overlap, never
    splitting mid-sentence."""
    chunk_size_tokens = chunk_size_tokens or settings.chunk_size_tokens
    chunk_overlap_tokens = chunk_overlap_tokens or settings.chunk_overlap_tokens

    chunks: list[Chunk] = []
    for section in sections:
        sentences = _split_sentences(section["text"])
        if not sentences:
            continue
        for text in _pack_sentences(sentences, chunk_size_tokens, chunk_overlap_tokens):
            chunks.append(
                Chunk(
                    company=company,
                    ticker=ticker,
                    doc_type=doc_type,
                    fiscal_period=fiscal_period,
                    section=section["section"],
                    source_path=source_path,
                    chunk_index=len(chunks),
                    text=text,
                    token_count=_token_count(text),
                )
            )
    return chunks
