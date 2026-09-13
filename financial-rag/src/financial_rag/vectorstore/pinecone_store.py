"""Pinecone-backed vector store: index bootstrap, upsert, and similarity search."""

import re

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

from financial_rag.config import settings
from financial_rag.embeddings.embedder import EmbeddedChunk

_UPSERT_BATCH_SIZE = 100
_ID_SANITIZE_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _slug(value: str) -> str:
    return _ID_SANITIZE_RE.sub("-", value).strip("-")


def _vector_id(chunk) -> str:
    return f"{_slug(chunk.ticker)}_{_slug(chunk.doc_type)}_{_slug(chunk.fiscal_period)}_{chunk.chunk_index}"


def get_index(client: Pinecone | None = None):
    """Create the index if it doesn't exist yet, then return a handle to it."""
    client = client or Pinecone(api_key=settings.pinecone_api_key)

    existing = {idx.name for idx in client.list_indexes()}
    if settings.pinecone_index_name not in existing:
        client.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.embedding_dimensions,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )

    return client.Index(settings.pinecone_index_name)


def upsert_chunks(chunks_with_embeddings: list[EmbeddedChunk], index=None) -> int:
    """Upsert embedded chunks with full metadata payload. Returns count upserted."""
    index = index or get_index()

    total = 0
    for i in range(0, len(chunks_with_embeddings), _UPSERT_BATCH_SIZE):
        batch = chunks_with_embeddings[i : i + _UPSERT_BATCH_SIZE]
        vectors = [
            {
                "id": _vector_id(ec.chunk),
                "values": ec.embedding,
                "metadata": ec.chunk.model_dump(),
            }
            for ec in batch
        ]
        index.upsert(vectors=vectors)
        total += len(vectors)

    return total


def search(
    query_text: str,
    top_k: int = 5,
    filters: dict | None = None,
    index=None,
    openai_client: OpenAI | None = None,
) -> list[dict]:
    """Embed query_text and return the top_k most similar chunks with scores and metadata."""
    index = index or get_index()
    openai_client = openai_client or OpenAI(api_key=settings.openai_api_key)

    query_embedding = (
        openai_client.embeddings.create(model=settings.embedding_model, input=[query_text])
        .data[0]
        .embedding
    )

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        filter=filters,
        include_metadata=True,
    )

    return [
        {"id": match.id, "score": match.score, "metadata": match.metadata}
        for match in results.matches
    ]
