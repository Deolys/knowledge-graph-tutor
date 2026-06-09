"""Модель главы учебника."""
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# status: pending | processing | done | error


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, server_default=text("'pending'"))
