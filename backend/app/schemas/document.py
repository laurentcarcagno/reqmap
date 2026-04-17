"""Pydantic schemas for document endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    customer: str
    status: Literal["pending", "processing", "completed", "failed"]
    error_message: str | None
    node_count: int
    title_count: int
    requirement_count: int
    doc_title: str | None
    doc_reference: str | None
    doc_author: str | None
    doc_company: str | None
    uploaded_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    data: list[DocumentResponse]
    meta: dict = Field(default_factory=dict)
