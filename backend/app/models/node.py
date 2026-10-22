"""Node ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("title", "requirement", name="node_type"), nullable=False
    )
    section: Mapped[str | None] = mapped_column(String(64), nullable=True)
    req_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    applicability: Mapped[str] = mapped_column(
        Enum("NA", "A", "A/M", "TBC", "T", name="applicability_value"),
        nullable=False,
        default="A",
    )
    conformity: Mapped[str] = mapped_column(
        Enum("NA", "C", "C TBC", "PC", "NC", "TBC", "T", name="conformity_value"),
        nullable=False,
        default="C",
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    document: Mapped["Document"] = relationship(  # noqa: F821
        "Document", back_populates="nodes"
    )
