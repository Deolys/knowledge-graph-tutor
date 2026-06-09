"""Роутер прогресса: отправка результатов теста и получение прогресса сессии."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Progress
from app.schemas.progress import ProgressOut, TestResult, TestSubmit
from app.services import progress_service

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.post("", response_model=TestResult)
async def submit_test(
    payload: TestSubmit, session: AsyncSession = Depends(get_session)
) -> TestResult:
    """Проверяет тест, обновляет прогресс, применяет каскадную логику."""
    return await progress_service.submit_test(session, payload)


@router.get("/{session_id}", response_model=list[ProgressOut])
async def get_progress(
    session_id: str, session: AsyncSession = Depends(get_session)
) -> list:
    rows = (
        await session.execute(
            select(Progress).where(Progress.session_id == session_id)
        )
    ).scalars().all()
    return list(rows)
