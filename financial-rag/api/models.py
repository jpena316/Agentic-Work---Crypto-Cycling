"""Pydantic v2 request/response models for the FastAPI backend."""

from pydantic import BaseModel

from financial_rag.mcp_server.server import Citation, GroundedAnswer
from financial_rag.mcp_server.server import ScoredChunk as SearchResult

__all__ = [
    "IngestRequest",
    "IngestResponse",
    "MetadataFilter",
    "SearchRequest",
    "SearchResult",
    "SearchResponse",
    "AskRequest",
    "Citation",
    "GroundedAnswer",
]


class IngestRequest(BaseModel):
    source: str
    metadata: dict


class IngestResponse(BaseModel):
    chunks_created: int
    vectors_upserted: int
    document: str


class MetadataFilter(BaseModel):
    company: str | None = None
    doc_type: str | None = None
    fiscal_period: str | None = None

    def to_pinecone_filter(self) -> dict | None:
        filter_dict = {k: v for k, v in self.model_dump().items() if v is not None}
        return filter_dict or None


class SearchRequest(BaseModel):
    query: str
    filters: MetadataFilter | None = None
    top_k: int = 10


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str
    total: int


class AskRequest(BaseModel):
    question: str
    filters: MetadataFilter | None = None
