"""Модель учебника."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    # активный профиль онтологии (подмножество классов для извлечения)
    profile: Mapped[str] = mapped_column(
        String,
        ForeignKey("profiles.profile_name"),
        server_default=text("'universal'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
