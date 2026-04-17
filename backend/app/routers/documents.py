"""Document upload, list, and detail endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.repositories.document_repository import (
    create_document,
    delete_document,
    get_document,
    list_documents,
)
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.customer_config import get_customer
from app.services.document_service import save_upload, validate_upload
from app.services.processing_service import process_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    customer: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Upload a document and trigger background processing."""
    settings = get_settings()

    try:
        validate_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if get_customer(str(settings.customers_config_path), customer) is None:
        raise HTTPException(status_code=422, detail=f"Unknown customer: '{customer}'")

    try:
        unique_name, file_path = await save_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    doc = await create_document(
        db,
        id=str(uuid.uuid4()),
        filename=unique_name,
        original_filename=file.filename or unique_name,
        file_path=file_path,
        customer=customer,
        status="pending",
    )
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(
        process_document,
        document_id=doc.id,
        file_path=file_path,
        customer_id=customer,
    )

    return DocumentResponse.model_validate(doc)


@router.get("", response_model=DocumentListResponse)
async def list_documents_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List documents."""
    docs = await list_documents(db, limit=limit, offset=offset)
    return DocumentListResponse(
        data=[DocumentResponse.model_validate(d) for d in docs],
        meta={"limit": limit, "offset": offset, "count": len(docs)},
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_endpoint(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Get a document by ID."""
    doc = await get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}", status_code=204)
async def delete_document_endpoint(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document and all its extracted nodes."""
    doc = await get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    await delete_document(db, document_id)
    await db.commit()
