"""Схемы QA."""
import uuid
from typing import Literal

from pydantic import BaseModel

# auto — обычное поведение (graphrag с fallback на вектор);
# graphrag / vector / none — принудительный режим для экспериментов.
QAMode = Literal["auto", "graphrag", "vector", "none"]


class QARequest(BaseModel):
    query: str
    book_id: uuid.UUID
    session_id: str | None = None
    mode: QAMode = "auto"


class QASource(BaseModel):
    id: uuid.UUID
    name: str
    entity_type: str


class TraversalEdge(BaseModel):
    source: uuid.UUID
    target: uuid.UUID
    relation_type: str


class QAResponse(BaseModel):
    answer: str
    sources: list[QASource]
    # узлы и рёбра, использованные при обходе — для подсветки на графе
    traversal_nodes: list[uuid.UUID]
    traversal_edges: list[TraversalEdge]
    # graphrag | vector_fallback | no_context
    mode: str
