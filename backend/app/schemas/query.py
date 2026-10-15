"""Schemas for the /query endpoint."""
import uuid

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    """A single source citation referenced in the answer."""
    index: int  # matches [1], [2] in the answer
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_filename: str
    page_number: int | None
    content: str  # full chunk text for the source viewer
    score: float


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    query: str 