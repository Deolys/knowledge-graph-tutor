"""Модель типизированной связи между сущностями (ребро графа)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Relation(Base):
    __tablename__ = "relations"
    __table_args__ = (
        UniqueConstraint("from_id", "to_id", "relation_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation_type: Mapped[str] = mapped_column(
        String, ForeignKey("relation_types.type_name"), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source_quote: Mapped[str] = mapped_column(Text, nullable=False)
    is_cross_chapter: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
