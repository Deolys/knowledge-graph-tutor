"""Модель понятия (узел графа)."""
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

EMBEDDING_DIM = 384


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id"), nullable=False
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    formula: Mapped[str | None] = mapped_column(Text)  # LaTeX, если есть
    quote: Mapped[str | None] = mapped_column(Text)  # цитата из текста
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    # ссылка на канонический узел после merge (NULL = сам канонический)
    canonical_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
