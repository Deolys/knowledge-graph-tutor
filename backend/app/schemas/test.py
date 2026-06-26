"""Схемы тестов по графу."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TestCreate(BaseModel):
    book_id: uuid.UUID
    session_id: str
    question_count: int = Field(ge=1, le=100)
    title: str | None = None
    # выбор охвата: конкретные сущности и/или главы; пусто — вся книга
    entity_ids: list[uuid.UUID] = Field(default_factory=list)
    chapter_ids: list[uuid.UUID] = Field(default_factory=list)


class TestQuestionOut(BaseModel):
    """Вопрос без правильного ответа (для прохождения)."""

    id: uuid.UUID
    order_num: int
    text: str
    options: list[str]
    difficulty: str
    entity_id: uuid.UUID | None = None
    entity_name: str | None = None

    model_config = {"from_attributes": True}


class TestQuestionResult(TestQuestionOut):
    """Вопрос с правильным ответом и выбором пользователя (после прохождения)."""

    correct_idx: int
    selected_idx: int | None = None


class TestListItem(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    book_title: str
    title: str
    status: str
    question_count: int
    score: float | None = None
    created_at: datetime


class TestDetail(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    book_title: str
    title: str
    status: str
    question_count: int
    score: float | None = None
    created_at: datetime
    questions: list[TestQuestionOut | TestQuestionResult]


class TestAnswerSubmit(BaseModel):
    # question_id -> выбранный индекс варианта
    answers: dict[uuid.UUID, int]


class TestSubmitResult(BaseModel):
    id: uuid.UUID
    score: float
    correct: int
    total: int
    questions: list[TestQuestionResult]
