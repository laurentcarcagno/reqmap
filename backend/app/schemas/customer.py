"""Pydantic schemas for customer endpoints."""

from pydantic import BaseModel


class CustomerResponse(BaseModel):
    id: str
    label: str


class CustomerListResponse(BaseModel):
    data: list[CustomerResponse]
