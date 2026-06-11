"""Экспорт всех ORM-моделей. Импорт здесь регистрирует их в Base.metadata."""
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.entity import Entity
from app.models.ontology import EntityTypeRow, ProfileRow, RelationTypeRow
from app.models.progress import Progress
from app.models.question import Question
from app.models.relation import Relation

__all__ = [
    "Book",
    "Chapter",
    "Entity",
    "EntityTypeRow",
    "ProfileRow",
    "RelationTypeRow",
    "Progress",
    "Question",
    "Relation",
]
