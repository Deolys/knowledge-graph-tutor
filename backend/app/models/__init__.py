"""Экспорт всех ORM-моделей. Импорт здесь регистрирует их в Base.metadata."""
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.concept import Concept
from app.models.progress import Progress
from app.models.question import Question
from app.models.relation import Relation

__all__ = ["Book", "Chapter", "Concept", "Progress", "Question", "Relation"]
