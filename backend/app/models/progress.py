"""Модель прогресса пользователя (без авторизации — по session_id)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# status: not_started | in_progress | learned


class Progress(Base):
    __tablename__ = "progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    session_id: Mapped[str] = mapped_column(String, nullable=False)
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, server_default=text("'not_started'")
    )
    score: Mapped[float | None] = mapped_column(Float)  # последний результат 0.0-1.0
    attempts: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
