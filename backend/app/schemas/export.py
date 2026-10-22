"""Pydantic schemas for the Excel export settings (HMA-C-049 compliance matrix)."""

from typing import Literal

from pydantic import BaseModel, Field

Text = Field(default="", max_length=2000)


class DocumentRef(BaseModel):
    """One row of the applicable (AD) or reference (RD) documents tables."""

    title: str = Text
    reference: str = Text
    edition: str = Text


class Acronym(BaseModel):
    acronym: str = Text
    description: str = Text


class ExportSettings(BaseModel):
    """Values that cannot be deduced from the PDF, entered by the user before exporting."""

    # HEADER sheet
    client: str = Text
    project: str = Text
    reference: str = Text
    edition: str = Text
    date: str = Field(default="", description="ISO date, YYYY-MM-DD", max_length=10)
    subject: str = Text
    subtitle: str = Text
    classification: Literal["", "public", "commercial", "internal"] = ""
    export_control: Literal["", "Not Listed/Not Controlled", "Listed/Controlled"] = ""
    quality_manager: str = Text
    project_manager: str = Text
    redactor: str = Text

    # Revisions sheet
    doc_type: str = Text
    author: str = Text
    revision_description: str = Text

    # DA-DR sheet
    applicable_docs: list[DocumentRef] = Field(default_factory=list, max_length=200)
    reference_docs: list[DocumentRef] = Field(default_factory=list, max_length=200)
    acronyms: list[Acronym] = Field(default_factory=list, max_length=500)
