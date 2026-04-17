"""Document data access layer."""

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


async def create_document(db: AsyncSession, **kwargs) -> Document:
    doc = Document(**kwargs)
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


async def get_document(db: AsyncSession, document_id: str) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    return result.scalar_one_or_none()


async def list_documents(
    db: AsyncSession,
    uploaded_by: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Document]:
    stmt = select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
    if uploaded_by is not None:
        stmt = stmt.where(Document.uploaded_by == uploaded_by)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_document_status(
    db: AsyncSession,
    document_id: str,
    status: str,
    error_message: str | None = None,
    node_count: int = 0,
    title_count: int = 0,
    requirement_count: int = 0,
) -> None:
    values: dict = {"status": status}
    if error_message is not None:
        values["error_message"] = error_message
    if node_count:
        values["node_count"] = node_count
    if title_count:
        values["title_count"] = title_count
    if requirement_count:
        values["requirement_count"] = requirement_count
    await db.execute(update(Document).where(Document.id == document_id).values(**values))


async def delete_document(db: AsyncSession, document_id: str) -> bool:
    result = await db.execute(delete(Document).where(Document.id == document_id))
    return result.rowcount > 0
