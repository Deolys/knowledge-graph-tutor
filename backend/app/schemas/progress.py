"""Схемы прогресса и проверки теста."""
import uuid

from pydantic import BaseModel


class TestSubmit(BaseModel):
    """Ответы на тест по сущности."""
    session_id: str
    entity_id: uuid.UUID
    # answers[question_id] = выбранный индекс варианта
    answers: dict[uuid.UUID, int]


class TestResult(BaseModel):
    entity_id: uuid.UUID
    score: float
    status: str
    # узлы, разблокированные каскадом после прохождения
    unlocked: list[uuid.UUID]


class ProgressOut(BaseModel):
    entity_id: uuid.UUID
    status: str
    score: float | None = None
    attempts: int

    model_config = {"from_attributes": True}
