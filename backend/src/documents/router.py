import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.dependencies import get_current_user
from src.documents import schemas, service
from src.db.session import get_db

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/markdown": "md",
}


def _resolve_file_type(filename: str, content_type: str | None) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext in ("pdf", "docx", "txt", "md"):
        return ext
    if content_type and content_type in ALLOWED_CONTENT_TYPES:
        return ALLOWED_CONTENT_TYPES[content_type]
    raise ValueError(f"Cannot determine file type for: {filename}")


@router.post("/upload", response_model=schemas.UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        file_type = _resolve_file_type(file.filename or "", file.content_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty file")

    try:
        document = await service.upload_document(db, current_user.id, file.filename, content, file_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    background_tasks.add_task(service.process_document, db, document.id)
    return schemas.UploadResponse(document=schemas.DocumentResponse.model_validate(document))


@router.get("", response_model=schemas.DocumentListResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = await service.get_documents(db, current_user.id)
    return schemas.DocumentListResponse(
        documents=[schemas.DocumentResponse.model_validate(d) for d in documents],
        total=len(documents),
    )


@router.get("/{document_id}", response_model=schemas.DocumentDetailResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = await service.get_document(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return schemas.DocumentDetailResponse.model_validate(document)


@router.delete("/{document_id}", response_model=schemas.DeleteResponse)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = await service.delete_document(db, document_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return schemas.DeleteResponse(message="Document deleted successfully")
