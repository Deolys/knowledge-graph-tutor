"""Загрузка тестового учебника в БД через ingestion pipeline.

Использование:
    python scripts/seed_test_book.py path/to/book.pdf "Название учебника"

Запускается из каталога backend (нужен доступ к app.*). Создаёт запись книги
и прогоняет полный пайплайн синхронно — удобно для эксперимента диссертации.
"""
import asyncio
import os
import shutil
import sys

# Позволяет запускать из корня репозитория или из backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import settings  # noqa: E402
from app.database import async_session_maker  # noqa: E402
from app.models import Book  # noqa: E402
from app.services.ingestion import pipeline  # noqa: E402


async def seed(pdf_path: str, title: str) -> None:
    async with async_session_maker() as session:
        book = Book(title=title, filename=os.path.basename(pdf_path))
        session.add(book)
        await session.flush()

        os.makedirs(settings.upload_dir, exist_ok=True)
        dest = os.path.join(settings.upload_dir, f"{book.id}.pdf")
        shutil.copyfile(pdf_path, dest)
        await session.commit()

        print(f"Книга создана: {book.id} — {title}")
        print("Запуск ingestion…")
        await pipeline.run_ingestion(session, book.id, dest)
        print("Готово.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/seed_test_book.py <pdf_path> [title]")
        raise SystemExit(1)
    pdf = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(pdf)
    asyncio.run(seed(pdf, name))
