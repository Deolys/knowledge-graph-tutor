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


class QAResponse(BaseModel):
    answer: str
    sources: list[QASource]
