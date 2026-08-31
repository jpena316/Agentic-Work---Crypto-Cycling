"""FastAPI backend exposing the financial RAG pipeline as a REST API."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from financial_rag.mcp_server.server import (
    answer_question as _answer_question,
)
from financial_rag.mcp_server.server import (
    ingest_document as _ingest_document,
)
from financial_rag.mcp_server.server import (
    search_documents as _search_documents,
)

from api.models import (
    AskRequest,
    GroundedAnswer,
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
)

PORT = 8002

app = FastAPI(title="Financial RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    result = _ingest_document(request.source, request.metadata)
    return IngestResponse(
        chunks_created=result.chunks_created,
        vectors_upserted=result.vectors_upserted,
        document=result.source,
    )


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    filters = request.filters.to_pinecone_filter() if request.filters else None
    results = _search_documents(request.query, filters=filters, top_k=request.top_k)
    return SearchResponse(results=results, query=request.query, total=len(results))


@app.post("/ask", response_model=GroundedAnswer)
def ask(request: AskRequest) -> GroundedAnswer:
    filters = request.filters.to_pinecone_filter() if request.filters else None
    return _answer_question(request.question, filters=filters)


def main() -> None:
    uvicorn.run("api.main:app", host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
