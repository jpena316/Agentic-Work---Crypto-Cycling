# Financial RAG — Specification

A retrieval-augmented generation pipeline for financial documents: SEC 10-K and 10-Q filings, plus earnings call transcripts. Documents are chunked, embedded, stored in Pinecone, and exposed via an MCP server and FastAPI backend.

## Scope

| Stage | Location | Status |
|-------|----------|--------|
| Raw corpus | `corpus/raw/{10k,10q,transcripts}/` | Placeholder |
| Processed corpus | `corpus/processed/` | Placeholder |
| Chunking | `src/financial_rag/chunking/` | Placeholder |
| Embeddings | `src/financial_rag/embeddings/` | Placeholder |
| Vector store | `src/financial_rag/vectorstore/` | Placeholder |
| MCP server | `src/financial_rag/mcp_server/` | Placeholder |
| REST API | `api/` | Placeholder |
| Scripts | `scripts/` | Placeholder |

## Configuration

All settings are loaded via `src/financial_rag/config.py` (pydantic-settings). See `.env.example` for required variables.

## Tech Stack

- **Embeddings:** OpenAI `text-embedding-3-small`
- **Vector DB:** Pinecone
- **LLM:** Anthropic Claude (via MCP / API)
- **Protocol:** MCP + FastAPI
- **Package manager:** uv

## Directory Layout

```
financial-rag/
├── corpus/
│   ├── raw/
│   │   ├── 10k/
│   │   ├── 10q/
│   │   └── transcripts/
│   └── processed/
├── src/financial_rag/
│   ├── config.py
│   ├── chunking/
│   ├── embeddings/
│   ├── vectorstore/
│   └── mcp_server/
├── api/
├── scripts/
├── tests/
├── docs/
├── pyproject.toml
├── .env.example
├── .gitignore
└── SPEC.md
```
