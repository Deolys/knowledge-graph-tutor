"""Роутер сущностей: детали сущности и вопросы для теста."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Entity
from app.schemas.entity import EntityOut, QuestionOut
from app.services import test_service

router = APIRouter(prefix="/api/entities", tags=["entities"])


@router.get("/{entity_id}", response_model=EntityOut)
async def entity_detail(
    entity_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> Entity:
    entity = await session.get(Entity, entity_id)
    if not entity:
        raise HTTPException(404, "Сущность не найдена")
    return entity


@router.get("/{entity_id}/questions", response_model=list[QuestionOut])
async def entity_questions(
    entity_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> list:
    entity = await session.get(Entity, entity_id)
    if not entity:
        raise HTTPException(404, "Сущность не найдена")
    # Вопросы генерируются лениво и кэшируются в БД при первом запросе.
    return await test_service.get_or_generate_questions(session, entity)
