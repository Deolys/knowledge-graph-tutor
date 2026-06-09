"""Роутер QA: вопрос -> ответ на основе графа (без галлюцинаций)."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.qa import QARequest, QAResponse
from app.services import qa_service

router = APIRouter(prefix="/api/qa", tags=["qa"])


@router.post("", response_model=QAResponse)
async def answer_question(
    payload: QARequest, session: AsyncSession = Depends(get_session)
) -> QAResponse:
    return await qa_service.answer(session, payload)
