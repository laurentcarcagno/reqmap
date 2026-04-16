"""Document ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    customer: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "processing", "completed", "failed", name="document_status"),
        nullable=False,
        default="pending",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    node_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requirement_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uploaded_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    nodes: Mapped[list["Node"]] = relationship(  # noqa: F821
        "Node", back_populates="document", cascade="all, delete-orphan"
    )
