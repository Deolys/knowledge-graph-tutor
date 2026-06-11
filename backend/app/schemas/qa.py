"""Схемы QA."""
import uuid

from pydantic import BaseModel


class QARequest(BaseModel):
    query: str
    book_id: uuid.UUID
    session_id: str | None = None


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
    # graphrag | vector_fallback
    mode: str
