"""Pydantic schemas for node endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ApplicabilityValue = Literal["NA", "A", "A/M", "TBC", "T"]
ConformityValue = Literal["NA", "C", "C TBC", "PC", "NC", "TBC", "T"]


class NodeResponse(BaseModel):
    id: str
    document_id: str
    order: int
    type: Literal["title", "requirement"]
    section: str | None
    req_id: str | None
    title: str
    description: str
    applicability: ApplicabilityValue
    conformity: ConformityValue
    comment: str
    updated_by: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class NodeUpdateRequest(BaseModel):
    applicability: ApplicabilityValue | None = None
    conformity: ConformityValue | None = None
    comment: str | None = Field(default=None, max_length=5000)
    description: str | None = Field(default=None, max_length=200_000)


class NodeListResponse(BaseModel):
    data: list[NodeResponse]
    meta: dict = Field(default_factory=dict)
