"""Node list and update endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.document_repository import get_document
from app.repositories.node_repository import get_node, list_nodes, update_node
from app.schemas.node import NodeListResponse, NodeResponse, NodeUpdateRequest

router = APIRouter(tags=["nodes"])


@router.get("/documents/{document_id}/nodes", response_model=NodeListResponse)
async def list_document_nodes(
    document_id: str,
    limit: int = 500,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> NodeListResponse:
    """List all nodes for a document."""
    doc = await get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    nodes = await list_nodes(db, document_id, limit=limit, offset=offset)
    return NodeListResponse(
        data=[NodeResponse.model_validate(n) for n in nodes],
        meta={"limit": limit, "offset": offset, "count": len(nodes)},
    )


@router.patch("/nodes/{node_id}", response_model=NodeResponse)
async def update_node_endpoint(
    node_id: str,
    body: NodeUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    """Update a node's applicability and/or conformity."""
    existing = await get_node(db, node_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Node not found")

    updated = await update_node(
        db,
        node_id,
        applicability=body.applicability,
        conformity=body.conformity,
    )
    await db.commit()
    return NodeResponse.model_validate(updated)
