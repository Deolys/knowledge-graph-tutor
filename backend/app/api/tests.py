"""Роутер тестов по графу: создание (генерация), список, прохождение, удаление."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.test import (
    TestAnswerSubmit,
    TestCreate,
    TestDetail,
    TestListItem,
    TestQuestionOut,
    TestQuestionResult,
    TestSubmitResult,
)
from app.services import graph_test_service

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.post("", response_model=TestListItem, status_code=201)
async def create_test(
    payload: TestCreate, session: AsyncSession = Depends(get_session)
) -> TestListItem:
    try:
        test = await graph_test_service.create_test(
            session,
            book_id=payload.book_id,
            session_id=payload.session_id,
            question_count=payload.question_count,
            title=payload.title,
            entity_ids=payload.entity_ids,
            chapter_ids=payload.chapter_ids,
        )
    except graph_test_service.TestGenerationError as exc:
        raise HTTPException(400, str(exc)) from exc

    result = await graph_test_service.get_test(session, test.id)
    assert result is not None
    _, book_title = result
    return _to_list_item(test, book_title)


@router.get("", response_model=list[TestListItem])
async def list_tests(
    session_id: str, session: AsyncSession = Depends(get_session)
) -> list[TestListItem]:
    rows = await graph_test_service.list_tests(session, session_id)
    return [_to_list_item(t, title) for t, title in rows]


@router.get("/{test_id}", response_model=TestDetail)
async def test_detail(
    test_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> TestDetail:
    result = await graph_test_service.get_test(session, test_id)
    if result is None:
        raise HTTPException(404, "Тест не найден")
    test, book_title = result

    completed = test.status == "completed"
    questions: list = [
        (
            TestQuestionResult.model_validate(q)
            if completed
            else TestQuestionOut.model_validate(q)
        )
        for q in test.questions
    ]
    return TestDetail(
        id=test.id,
        book_id=test.book_id,
        book_title=book_title,
        title=test.title,
        status=test.status,
        question_count=test.question_count,
        score=test.score,
        created_at=test.created_at,
        questions=questions,
    )


@router.post("/{test_id}/submit", response_model=TestSubmitResult)
async def submit_test(
    test_id: uuid.UUID,
    payload: TestAnswerSubmit,
    session: AsyncSession = Depends(get_session),
) -> TestSubmitResult:
    test = await graph_test_service.submit_test(
        session, test_id, payload.answers
    )
    if test is None:
        raise HTTPException(404, "Тест не найден")

    questions = [TestQuestionResult.model_validate(q) for q in test.questions]
    correct = sum(
        1
        for q in test.questions
        if q.selected_idx is not None and q.selected_idx == q.correct_idx
    )
    return TestSubmitResult(
        id=test.id,
        score=test.score or 0.0,
        correct=correct,
        total=len(test.questions),
        questions=questions,
    )


@router.delete("/{test_id}", status_code=204)
async def delete_test(
    test_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> None:
    deleted = await graph_test_service.delete_test(session, test_id)
    if not deleted:
        raise HTTPException(404, "Тест не найден")


def _to_list_item(test, book_title: str) -> TestListItem:
    return TestListItem(
        id=test.id,
        book_id=test.book_id,
        book_title=book_title,
        title=test.title,
        status=test.status,
        question_count=test.question_count,
        score=test.score,
        created_at=test.created_at,
    )
