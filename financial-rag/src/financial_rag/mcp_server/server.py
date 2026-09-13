"""MCP server exposing the financial RAG pipeline as 4 tools, over stdio transport."""

from anthropic import Anthropic
from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from financial_rag.chunking.chunker import chunk_sections
from financial_rag.chunking.parser import parse_10k, parse_transcript
from financial_rag.config import settings
from financial_rag.embeddings.embedder import embed_chunks
from financial_rag.vectorstore.pinecone_store import get_index, search, upsert_chunks

mcp = MCPServer("financial-rag")

_REQUIRED_METADATA_FIELDS = ("company", "ticker", "doc_type", "fiscal_period")

_GROUNDING_SYSTEM_PROMPT = (
    "You are a financial research assistant. Answer the user's question using ONLY the "
    "information in the numbered context entries below. Every claim in your answer must "
    "be immediately followed by a citation marker (e.g. [1], [2]) matching the context "
    "entry it came from. If the answer is not present in the provided context, respond "
    "with exactly: \"This is not in the provided documents.\" Do not use outside knowledge."
)

_index = None


def _get_index():
    global _index
    if _index is None:
        _index = get_index()
    return _index


class IngestResult(BaseModel):
    source: str
    sections_parsed: int
    chunks_created: int
    vectors_upserted: int


class ScoredChunk(BaseModel):
    id: str
    score: float
    company: str
    ticker: str
    doc_type: str
    fiscal_period: str
    section: str
    text: str


class Citation(BaseModel):
    marker: str
    company: str
    doc_type: str
    fiscal_period: str
    section: str


class GroundedAnswer(BaseModel):
    answer: str
    citations: list[Citation]


@mcp.tool()
def ingest_document(source: str, metadata: dict) -> IngestResult:
    """Parse, chunk, embed, and upsert a single document into the Pinecone index.

    `source` is a path to a 10-K HTML file or an earnings-call transcript text file.
    `metadata` must include company, ticker, doc_type ("10-K" or "transcript"), and
    fiscal_period; doc_type selects the parser.
    """
    missing = [field for field in _REQUIRED_METADATA_FIELDS if field not in metadata]
    if missing:
        raise ValueError(f"metadata missing required fields: {missing}")

    parser = parse_10k if metadata["doc_type"] == "10-K" else parse_transcript
    sections = parser(source)
    chunks = chunk_sections(sections, source_path=source, **metadata)
    embedded = embed_chunks(chunks)
    upserted = upsert_chunks(embedded, index=_get_index())

    return IngestResult(
        source=source,
        sections_parsed=len(sections),
        chunks_created=len(chunks),
        vectors_upserted=upserted,
    )


@mcp.tool()
def search_documents(
    query: str, filters: dict | None = None, top_k: int = 10
) -> list[ScoredChunk]:
    """Embed `query` and run a Pinecone similarity search, optionally filtered by
    metadata fields (company, doc_type, fiscal_period)."""
    results = search(query, top_k=top_k, filters=filters, index=_get_index())
    return [
        ScoredChunk(
            id=r["id"],
            score=r["score"],
            company=r["metadata"]["company"],
            ticker=r["metadata"]["ticker"],
            doc_type=r["metadata"]["doc_type"],
            fiscal_period=r["metadata"]["fiscal_period"],
            section=r["metadata"]["section"],
            text=r["metadata"]["text"],
        )
        for r in results
    ]


def _format_context(chunks: list[ScoredChunk]) -> str:
    return "\n\n".join(
        f"[{i}] {c.company} ({c.ticker}) — {c.doc_type}, {c.fiscal_period}, {c.section}\n{c.text}"
        for i, c in enumerate(chunks, 1)
    )


@mcp.tool()
def get_context(query: str, top_k: int = 5) -> str:
    """Search for the top_k chunks most relevant to `query` and format them into a
    citation-marked context block ([1], [2], ...) ready for prompt injection."""
    chunks = search_documents(query, top_k=top_k)
    return _format_context(chunks)


@mcp.tool()
def answer_question(question: str, filters: dict | None = None) -> GroundedAnswer:
    """Answer `question` grounded strictly in retrieved document context.

    Retrieves context via search_documents, injects it into a Claude prompt with
    strict grounding instructions, and returns the answer with citations resolved
    against the retrieved chunks' metadata.
    """
    chunks = search_documents(question, filters=filters, top_k=5)
    context = _format_context(chunks)

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=_GROUNDING_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ],
    )
    answer_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    citations = [
        Citation(
            marker=f"[{i}]",
            company=c.company,
            doc_type=c.doc_type,
            fiscal_period=c.fiscal_period,
            section=c.section,
        )
        for i, c in enumerate(chunks, 1)
        if f"[{i}]" in answer_text
    ]

    return GroundedAnswer(answer=answer_text, citations=citations)


if __name__ == "__main__":
    mcp.run(transport="stdio")
