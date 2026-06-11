"""Схемы книг и графа."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class BookOut(BaseModel):
    id: uuid.UUID
    title: str
    filename: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChapterStatusOut(BaseModel):
    id: uuid.UUID
    title: str
    order_num: int
    status: str

    model_config = {"from_attributes": True}


class BookStatusOut(BaseModel):
    """Статус обработки книги: агрегат по главам."""
    id: uuid.UUID
    title: str
    chapters: list[ChapterStatusOut]
    done: bool


class BookListItem(BaseModel):
    """Элемент списка книг с агрегатом обработки для страницы выбора графа."""
    id: uuid.UUID
    title: str
    filename: str
    created_at: datetime
    chapters_total: int
    chapters_done: int
    concepts_count: int
    # processing | done | error — агрегатный статус по главам
    status: str


class GraphNode(BaseModel):
    id: uuid.UUID
    name: str
    chapter_id: uuid.UUID
    status: str = "not_started"


class GraphEdge(BaseModel):
    source: uuid.UUID
    target: uuid.UUID
    type: str
    confidence: float


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
