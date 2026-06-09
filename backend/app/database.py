"""Async SQLAlchemy engine, session factory и базовый класс моделей."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-зависимость: выдаёт сессию на запрос."""
    async with async_session_maker() as session:
        yield session
