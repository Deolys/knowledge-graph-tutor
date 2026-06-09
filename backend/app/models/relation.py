"""Модель связи между понятиями (ребро графа)."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# type: depends_on | part_of | example_of | related_to


class Relation(Base):
    __tablename__ = "relations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    from_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False
    )
    to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_cross_chapter: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
