"""Схемы понятий и вопросов теста."""
import uuid

from pydantic import BaseModel


class ConceptOut(BaseModel):
    id: uuid.UUID
    name: str
    definition: str
    formula: str | None = None
    quote: str | None = None
    chapter_id: uuid.UUID

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    """Вопрос без correct_idx — правильный ответ не уходит на клиент."""
    id: uuid.UUID
    text: str
    options: list[str]
    difficulty: str

    model_config = {"from_attributes": True}
