"""Синхронизация онтологии: ontology.yaml → таблицы БД (CLI-обёртка).

Логика — в app.ontology.sync; этот скрипт лишь запускает её с хоста.
Запускать после правки ontology.yaml. В Docker синхронизация выполняется
автоматически при старте backend (lifespan), поэтому скрипт нужен в основном
для локального (не контейнерного) прогона.

Использование:
    python scripts/sync_ontology.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import async_session_maker  # noqa: E402
from app.ontology.sync import sync_ontology  # noqa: E402


async def main() -> None:
    async with async_session_maker() as session:
        entities, relations, profiles = await sync_ontology(session)
    print(
        f"Синхронизировано: {entities} типов сущностей, "
        f"{relations} типов отношений, {profiles} профилей."
    )


if __name__ == "__main__":
    asyncio.run(main())
