"""Загрузка тестового учебника в БД через ingestion pipeline.

Использование:
    python scripts/seed_test_book.py path/to/book.pdf "Название" [profile]

profile — один из профилей онтологии (universal|math|cs|history|economics),
по умолчанию universal. Прогоняет полный пайплайн синхронно.
Перед запуском убедитесь, что онтология синхронизирована: scripts/sync_ontology.py
"""
import asyncio
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import settings  # noqa: E402
from app.database import async_session_maker  # noqa: E402
from app.models import Book  # noqa: E402
from app.ontology import load_ontology  # noqa: E402
from app.services.ingestion import pipeline  # noqa: E402


async def seed(pdf_path: str, title: str, profile: str) -> None:
    if profile not in load_ontology().profiles:
        print(f"Неизвестный профиль: {profile}")
        raise SystemExit(1)

    async with async_session_maker() as session:
        book = Book(
            title=title, filename=os.path.basename(pdf_path), profile=profile
        )
        session.add(book)
        await session.flush()

        os.makedirs(settings.upload_dir, exist_ok=True)
        dest = os.path.join(settings.upload_dir, f"{book.id}.pdf")
        shutil.copyfile(pdf_path, dest)
        await session.commit()

        print(f"Книга создана: {book.id} — {title} (профиль: {profile})")
        print("Запуск ingestion…")
        await pipeline.run_ingestion(session, book.id, dest)
        print("Готово.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/seed_test_book.py "
            "<pdf_path> [title] [profile]"
        )
        raise SystemExit(1)
    pdf = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(pdf)
    prof = sys.argv[3] if len(sys.argv) > 3 else "universal"
    asyncio.run(seed(pdf, name, prof))
