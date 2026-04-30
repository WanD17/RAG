import uuid

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    conversation_id: uuid.UUID | None = None


class SourceChunk(BaseModel):
    document_id: uuid.UUID
    filename: str
    chunk_index: int
    content: str
    similarity_score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    query: str
    conversation_id: uuid.UUID
