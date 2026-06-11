"""Схемы сущностей и вопросов теста."""
import uuid
from typing import Any

from pydantic import BaseModel


class EntityOut(BaseModel):
    id: uuid.UUID
    entity_type: str
    name: str
    attrs: dict[str, Any]
    source_quote: str | None = None
    chapter_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    """Вопрос без correct_idx — правильный ответ не уходит на клиент."""
    id: uuid.UUID
    text: str
    options: list[str]
    difficulty: str

    model_config = {"from_attributes": True}
