"""Full ingestion pipeline: parse -> chunk -> embed -> upsert, for all 4 source documents."""

import json
import time
from pathlib import Path

from financial_rag.chunking.chunker import chunk_sections
from financial_rag.chunking.parser import parse_10k, parse_transcript
from financial_rag.config import settings
from financial_rag.embeddings.embedder import embed_chunks
from financial_rag.vectorstore.pinecone_store import get_index, upsert_chunks

DOCS = [
    dict(
        parser=parse_10k,
        source_path="corpus/raw/10k/vrt_10k_fy2025.html",
        company="Vertiv Holdings Co",
        ticker="VRT",
        doc_type="10-K",
        fiscal_period="FY2025",
    ),
    dict(
        parser=parse_10k,
        source_path="corpus/raw/10k/snow_10k_fy2026.html",
        company="Snowflake Inc.",
        ticker="SNOW",
        doc_type="10-K",
        fiscal_period="FY2026",
    ),
    dict(
        parser=parse_transcript,
        source_path="corpus/raw/transcripts/vrt_transcript_q4_2025.txt",
        company="Vertiv Holdings Co",
        ticker="VRT",
        doc_type="transcript",
        fiscal_period="Q4 2025",
    ),
    dict(
        parser=parse_transcript,
        source_path="corpus/raw/transcripts/snow_transcript_q4_2025.txt",
        company="Snowflake Inc.",
        ticker="SNOW",
        doc_type="transcript",
        fiscal_period="Q4 2025",
    ),
]


def main() -> None:
    processed_dir = Path("corpus/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    index = get_index()

    summary = []
    t_start = time.monotonic()

    for doc in DOCS:
        doc = dict(doc)
        parser = doc.pop("parser")
        source_path = doc["source_path"]

        print(f"--- {source_path} ---")

        sections = parser(source_path)
        print(f"  parsed {len(sections)} sections")

        chunks = chunk_sections(sections, **doc)
        avg_tokens = sum(c.token_count for c in chunks) / len(chunks) if chunks else 0
        print(f"  chunked into {len(chunks)} chunks (avg {avg_tokens:.1f} tokens)")

        out_path = processed_dir / f"{Path(source_path).stem}_chunks.json"
        out_path.write_text(json.dumps([c.model_dump() for c in chunks], indent=2))

        embedded = embed_chunks(chunks)
        print(f"  embedded {len(embedded)} chunks")

        upserted = upsert_chunks(embedded, index=index)
        print(f"  upserted {upserted} vectors")

        summary.append((source_path, len(chunks)))

    elapsed = time.monotonic() - t_start
    stats = index.describe_index_stats()

    print()
    print("=== Ingestion summary ===")
    for source_path, n_chunks in summary:
        print(f"  {source_path}: {n_chunks} chunks")
    print(f"  total chunks: {sum(n for _, n in summary)}")
    print(f"  total vectors in Pinecone index '{settings.pinecone_index_name}': {stats.total_vector_count}")
    print(f"  elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
