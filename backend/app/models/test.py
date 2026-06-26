"""Модели полноценного теста по графу: Test (набор) + TestQuestion (вопрос).

В отличие от per-entity вопросов (questions), тест — это самостоятельный набор
из N вопросов (1–100), сгенерированный по выбранным сущностям/главам книги.
Привязан к session_id (без auth). Хранит счёт и статус прохождения.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("gen_random_uuid()"),
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    # status: ready | completed
    status: Mapped[str] = mapped_column(
        String, server_default=sa_text("'ready'")
    )
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # доля правильных ответов после прохождения (0.0–1.0), пока None
    score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    questions: Mapped[list["TestQuestion"]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="TestQuestion.order_num",
    )


class TestQuestion(Base):
    __tablename__ = "test_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("gen_random_uuid()"),
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tests.id", ondelete="CASCADE"),
        nullable=False,
    )
    # сущность-источник вопроса (для отображения «по какому узлу»)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL")
    )
    entity_name: Mapped[str | None] = mapped_column(String)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    correct_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(
        String, server_default=sa_text("'medium'")
    )
    # выбранный пользователем вариант после прохождения (None — не отвечено)
    selected_idx: Mapped[int | None] = mapped_column(Integer)

    test: Mapped["Test"] = relationship(back_populates="questions")
