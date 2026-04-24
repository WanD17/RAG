import os
import uuid
from pathlib import Path

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.documents.chunker import chunk_text
from src.documents.models import Document, DocumentChunk
from src.documents.parser import parse_file
from src.embeddings.service import embedding_service
from src.rag.qdrant import qdrant_service

ALLOWED_TYPES = {"pdf", "docx", "txt", "md"}


def _get_upload_path(document_id: uuid.UUID, filename: str) -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / f"{document_id}_{filename}"


async def upload_document(
    db: AsyncSession, user_id: uuid.UUID, filename: str, file_content: bytes, file_type: str
) -> Document:
    if file_type.lower() not in ALLOWED_TYPES:
        raise ValueError(f"Unsupported file type: {file_type}. Allowed: {', '.join(ALLOWED_TYPES)}")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_content) > max_bytes:
        raise ValueError(f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB")

    document = Document(
        user_id=user_id,
        filename=filename,
        file_type=file_type.lower(),
        file_size=len(file_content),
        status="pending",
        chunk_count=0,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    file_path = _get_upload_path(document.id, filename)
    file_path.write_bytes(file_content)

    return document


async def process_document(db: AsyncSession, document_id: uuid.UUID) -> None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        logger.error(f"Document {document_id} not found for processing")
        return

    try:
        document.status = "processing"
        await db.commit()

        file_path = _get_upload_path(document.id, document.filename)
        raw_text = parse_file(str(file_path), document.file_type)

        chunks = chunk_text(raw_text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        if not chunks:
            raise ValueError("No content extracted from document")

        embeddings = embedding_service.embed_texts(chunks)

        chunk_ids = [uuid.uuid4() for _ in chunks]
        chunk_records = [
            DocumentChunk(
                id=chunk_ids[idx],
                document_id=document.id,
                content=chunk,
                chunk_index=idx,
                metadata_={
                    "filename": document.filename,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                },
            )
            for idx, chunk in enumerate(chunks)
        ]

        db.add_all(chunk_records)
        document.chunk_count = len(chunks)
        document.status = "completed"
        await db.commit()

        payloads = [
            {
                "user_id": str(document.user_id),
                "document_id": str(document.id),
                "filename": document.filename,
                "chunk_index": idx,
                "content": chunk,
            }
            for idx, chunk in enumerate(chunks)
        ]
        await qdrant_service.upsert_chunks(chunk_ids, embeddings, payloads)
        logger.info(
            f"Document {document_id} processed: {len(chunks)} chunks "
            f"(Postgres + Qdrant)"
        )

    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}")
        document.status = "failed"
        await db.commit()


async def get_documents(db: AsyncSession, user_id: uuid.UUID) -> list[Document]:
    result = await db.execute(
        select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def get_document(db: AsyncSession, document_id: uuid.UUID, user_id: uuid.UUID) -> Document | None:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def delete_document(db: AsyncSession, document_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    document = await get_document(db, document_id, user_id)
    if not document:
        return False

    file_path = _get_upload_path(document.id, document.filename)
    if file_path.exists():
        os.remove(file_path)

    await db.delete(document)
    await db.commit()
    await qdrant_service.delete_by_document(document_id)
    return True
