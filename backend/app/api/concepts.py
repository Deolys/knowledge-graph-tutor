"""Роутер понятий: детали понятия и вопросы для теста."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Concept
from app.schemas.concept import ConceptOut, QuestionOut
from app.services import test_service

router = APIRouter(prefix="/api/concepts", tags=["concepts"])


@router.get("/{concept_id}", response_model=ConceptOut)
async def concept_detail(
    concept_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> Concept:
    concept = await session.get(Concept, concept_id)
    if not concept:
        raise HTTPException(404, "Понятие не найдено")
    return concept


@router.get("/{concept_id}/questions", response_model=list[QuestionOut])
async def concept_questions(
    concept_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> list:
    concept = await session.get(Concept, concept_id)
    if not concept:
        raise HTTPException(404, "Понятие не найдено")
    # Вопросы генерируются лениво и кэшируются в БД при первом запросе.
    return await test_service.get_or_generate_questions(session, concept)
