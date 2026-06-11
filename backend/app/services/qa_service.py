"""QA-сервис: тонкая обёртка над GraphRAG.

Вся логика обхода и сборки контекста — в graphrag. Здесь оставлен слой
сервиса, чтобы роутер не зависел напрямую от деталей GraphRAG.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.qa import QARequest, QAResponse
from app.services import graphrag


async def answer(session: AsyncSession, payload: QARequest) -> QAResponse:
    return await graphrag.answer(session, payload)
