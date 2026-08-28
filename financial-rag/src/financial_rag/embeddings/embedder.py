"""Batch-embeds chunks (loaded from corpus/processed/ JSON) via OpenAI."""

import json
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel

from financial_rag.chunking.chunker import Chunk
from financial_rag.config import settings

_BATCH_SIZE = 100


class EmbeddedChunk(BaseModel):
    chunk: Chunk
    embedding: list[float]


def load_chunks(processed_dir: str | Path = "corpus/processed") -> list[Chunk]:
    """Load every {filename}_chunks.json file in the processed corpus directory."""
    processed_dir = Path(processed_dir)
    chunks: list[Chunk] = []
    for path in sorted(processed_dir.glob("*_chunks.json")):
        raw = json.loads(path.read_text())
        chunks.extend(Chunk(**item) for item in raw)
    return chunks


def embed_chunks(chunks: list[Chunk], client: OpenAI | None = None) -> list[EmbeddedChunk]:
    """Batch-embed chunks (batch size 100) using the configured OpenAI embedding model."""
    client = client or OpenAI(api_key=settings.openai_api_key)

    embedded: list[EmbeddedChunk] = []
    for i in range(0, len(chunks), _BATCH_SIZE):
        batch = chunks[i : i + _BATCH_SIZE]
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=[c.text for c in batch],
        )
        for chunk, data in zip(batch, response.data):
            embedded.append(EmbeddedChunk(chunk=chunk, embedding=data.embedding))

    return embedded
