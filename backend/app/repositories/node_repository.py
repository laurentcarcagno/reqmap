"""Node data access layer."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.node import Node


async def bulk_insert_nodes(db: AsyncSession, nodes: list[dict]) -> int:
    objs = [Node(**n) for n in nodes]
    db.add_all(objs)
    await db.flush()
    return len(objs)


async def list_nodes(
    db: AsyncSession,
    document_id: str,
    limit: int = 500,
    offset: int = 0,
) -> list[Node]:
    result = await db.execute(
        select(Node)
        .where(Node.document_id == document_id)
        .order_by(Node.order)
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_node(db: AsyncSession, node_id: str) -> Node | None:
    result = await db.execute(select(Node).where(Node.id == node_id))
    return result.scalar_one_or_none()


async def update_node(
    db: AsyncSession,
    node_id: str,
    applicability: str | None = None,
    conformity: str | None = None,
    comment: str | None = None,
    description: str | None = None,
    updated_by: str | None = None,
) -> Node | None:
    values: dict = {}
    if applicability is not None:
        values["applicability"] = applicability
    if conformity is not None:
        values["conformity"] = conformity
    if description is not None:
        values["description"] = description
    if comment is not None:
        values["comment"] = comment
    if updated_by is not None:
        values["updated_by"] = updated_by
    if not values:
        return await get_node(db, node_id)
    await db.execute(update(Node).where(Node.id == node_id).values(**values))
    await db.flush()
    return await get_node(db, node_id)
