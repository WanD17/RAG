import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class DocumentDetailResponse(DocumentResponse):
    pass


class UploadResponse(BaseModel):
    document: DocumentResponse
    message: str = "Document uploaded and processing started"


class DeleteResponse(BaseModel):
    message: str
