"""PDF processing service — runs the reqmap pipeline in the background."""

import logging
import sys
import uuid
from pathlib import Path

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.repositories.document_repository import update_document_status
from app.repositories.node_repository import bulk_insert_nodes
from app.services.customer_config import get_customer

logger = logging.getLogger(__name__)

_DEFAULT_APPLICABILITY = {"title": "T", "requirement": "A"}
_DEFAULT_CONFORMITY = {"title": "T", "requirement": "C"}


def _ensure_reqmap_importable() -> None:
    """Add the project root to sys.path so reqmap is importable from the backend."""
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


async def process_document(
    document_id: str,
    file_path: str,
    customer_id: str,
) -> None:
    """Run the full reqmap pipeline for a document and persist results.

    Uses its own database session — never shares the request-scoped session.
    """
    settings = get_settings()
    _ensure_reqmap_importable()

    async with AsyncSessionLocal() as db:
        try:
            await update_document_status(db, document_id, "processing")
            await db.commit()
        except Exception:
            logger.exception("Failed to set processing status for %s", document_id)
            return

    try:
        parsed, node_rows = _run_reqmap(file_path, customer_id, document_id, settings)
    except Exception as exc:
        logger.exception("reqmap pipeline failed for document %s", document_id)
        async with AsyncSessionLocal() as db:
            await update_document_status(db, document_id, "failed", error_message=str(exc)[:500])
            await db.commit()
        return

    async with AsyncSessionLocal() as db:
        try:
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
        except Exception as exc:
            logger.exception("Failed to persist nodes for document %s", document_id)
            await db.rollback()
            async with AsyncSessionLocal() as db2:
                await update_document_status(db2, document_id, "failed", error_message=str(exc)[:500])
                await db2.commit()


def assets_dir(document_id: str) -> Path:
    """Where the figures extracted from a document are stored."""
    return get_settings().upload_dir / "assets" / document_id


def _run_reqmap(file_path: str, customer_id: str, document_id: str, settings) -> tuple[dict, list[dict]]:
    """Synchronous reqmap extraction — runs in the async background task."""
    from reqmap.node_parser import parse_nodes
    from reqmap.pdf_source import pdf_to_markdown

    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Upload file not found: {pdf_path}")

    customer = get_customer(str(settings.customers_config_path), customer_id)
    req_id_pattern = customer.req_id_pattern if customer else None
    noise_patterns = customer.noise_patterns if customer else None
    title_pattern = customer.title_pattern if customer else None

    clean_md = pdf_to_markdown(
        pdf_path,
        req_id_pattern,
        images_dir=assets_dir(document_id),
        asset_url_prefix=f"/api/v1/documents/{document_id}/assets",
        tables_as_images=settings.tables_as_images,
    )

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

    return parsed, node_rows
