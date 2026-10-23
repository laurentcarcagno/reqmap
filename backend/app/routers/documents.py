"""Document upload, list, and detail endpoints."""

import shutil
import uuid

from pathlib import Path
from urllib.parse import quote

from fastapi.responses import FileResponse
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.repositories.document_repository import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    save_export_settings,
)
from app.repositories.node_repository import list_nodes
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.schemas.export import ExportSettings
from app.services.customer_config import get_customer
from app.services.document_service import save_upload, validate_upload
from app.services.export_service import build_compliance_matrix, load_export_settings
from app.services.processing_service import TABLE_MODES, assets_dir, process_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    customer: str = Form(...),
    tables: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Upload a document and trigger background processing."""
    settings = get_settings()

    try:
        validate_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if tables is not None and tables not in TABLE_MODES:
        raise HTTPException(status_code=422, detail=f"Unknown table mode: '{tables}'")

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
        tables_mode=tables,
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


_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _client_label(doc) -> str:
    customer = get_customer(str(get_settings().customers_config_path), doc.customer)
    return customer.label if customer else doc.customer


@router.get("/{document_id}/assets/{name}")
async def get_asset_endpoint(document_id: str, name: str) -> FileResponse:
    """A figure extracted from the document (referenced by node descriptions)."""
    path = assets_dir(document_id) / name
    if name != Path(name).name or not path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(path)


@router.get("/{document_id}/export-settings", response_model=ExportSettings)
async def get_export_settings_endpoint(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> ExportSettings:
    """Saved export settings, or the values deduced from the document."""
    doc = await get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return load_export_settings(doc, _client_label(doc))


@router.put("/{document_id}/export-settings", response_model=ExportSettings)
async def save_export_settings_endpoint(
    document_id: str,
    body: ExportSettings,
    db: AsyncSession = Depends(get_db),
) -> ExportSettings:
    """Save the values entered in the export form, to reuse them next time."""
    doc = await get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    await save_export_settings(db, document_id, body.model_dump_json())
    await db.commit()
    return body


@router.get("/{document_id}/export")
async def export_document_endpoint(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export the nodes as the Excel requirements compliance matrix (HMA-C-049 template)."""
    doc = await get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "completed":
        raise HTTPException(status_code=409, detail="Document is not processed yet")

    nodes = await list_nodes(db, document_id, limit=1_000_000)
    export_settings = load_export_settings(doc, _client_label(doc))
    content = await run_in_threadpool(
        build_compliance_matrix, doc, nodes, export_settings, assets_dir(document_id)
    )

    stem = doc.original_filename.rsplit(".", 1)[0]
    filename = quote(f"{stem}_matrice-conformite.xlsx")
    return Response(
        content=content,
        media_type=_XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


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
    shutil.rmtree(assets_dir(document_id), ignore_errors=True)
