"""PDF processing service — runs the reqmap pipeline in the background."""

import logging
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.repositories.document_repository import update_document_status
from app.repositories.node_repository import bulk_insert_nodes
from app.services.customer_config import get_customer

logger = logging.getLogger(__name__)

_DEFAULT_APPLICABILITY = {"title": "T", "requirement": "A"}
_DEFAULT_CONFORMITY = {"title": "T", "requirement": "C"}


async def process_document(
    db: AsyncSession,
    document_id: str,
    file_path: str,
    customer_id: str,
) -> None:
    """Run the full reqmap pipeline for a document and persist results."""
    settings = get_settings()

    await update_document_status(db, document_id, "processing")
    await db.commit()

    try:
        _run_pipeline(db, document_id, file_path, customer_id, settings)
    except Exception as exc:
        logger.exception("Processing failed for document %s", document_id)
        async with db:
            await update_document_status(
                db, document_id, "failed", error_message=str(exc)
            )
            await db.commit()


def _run_pipeline(db, document_id: str, file_path: str, customer_id: str, settings) -> None:
    """Synchronous pipeline — called from async context via background task."""
    import asyncio

    asyncio.get_event_loop().run_until_complete(
        _async_pipeline(db, document_id, file_path, customer_id, settings)
    )


async def _async_pipeline(db: AsyncSession, document_id: str, file_path: str, customer_id: str, settings) -> None:
    # Ensure reqmap package is importable (it lives one level up from backend/)
    backend_dir = Path(__file__).resolve().parents[3]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    from reqmap.extractor import PDFExtractor
    from reqmap.node_parser import parse_nodes

    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Upload file not found: {pdf_path}")

    customer = get_customer(str(settings.customers_config_path), customer_id)
    req_id_pattern = customer.req_id_pattern if customer else None
    noise_patterns = customer.noise_patterns if customer else None
    title_pattern = customer.title_pattern if customer else None

    extractor = PDFExtractor(enable_ocr=True)
    _raw_md, clean_md = extractor.extract(pdf_path)

    parse_kwargs: dict = {"source": pdf_path.name}
    if req_id_pattern:
        parse_kwargs["req_id_pattern"] = req_id_pattern
    if noise_patterns:
        parse_kwargs["noise_patterns"] = noise_patterns
    if title_pattern:
        parse_kwargs["title_pattern"] = title_pattern

    parsed = parse_nodes(clean_md, **parse_kwargs)

    node_rows: list[dict] = []
    for n in parsed["nodes"]:
        node_type = n["type"]
        node_rows.append({
            "id": str(uuid.uuid4()),
            "document_id": document_id,
            "order": n["order"],
            "type": node_type,
            "section": n.get("section"),
            "req_id": n.get("req_id"),
            "title": n.get("title", ""),
            "description": n.get("description", ""),
            "applicability": _DEFAULT_APPLICABILITY[node_type],
            "conformity": _DEFAULT_CONFORMITY[node_type],
        })

    async with db:
        await bulk_insert_nodes(db, node_rows)
        await update_document_status(
            db,
            document_id,
            "completed",
            node_count=parsed["node_count"],
            title_count=parsed["title_count"],
            requirement_count=parsed["requirement_count"],
        )
        await db.commit()

    logger.info(
        "Processed document %s: %d nodes (%d titles, %d requirements)",
        document_id,
        parsed["node_count"],
        parsed["title_count"],
        parsed["requirement_count"],
    )
