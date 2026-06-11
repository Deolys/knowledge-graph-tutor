"""Сервис прогресса: проверка теста + каскадная логика статуса "learned".

Правило (knowledge_graph_analytics.md §3):
узел "learned", если score >= LEARNED_SCORE_THRESHOLD И все пререквизиты
(сущности, на которые он указывает связью REQUIRES) тоже "learned".

После перехода узла в learned его прямые зависимые могут разблокироваться —
каскадно переоцениваем их вверх по графу REQUIRES.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Progress, Relation
from app.schemas.progress import TestResult, TestSubmit
from app.services import test_service

REQUIRES = "REQUIRES"


async def submit_test(
    session: AsyncSession, payload: TestSubmit
) -> TestResult:
    score = await test_service.score_answers(
        session, payload.entity_id, payload.answers
    )
    prog = await _get_or_create(session, payload.session_id, payload.entity_id)
    prog.score = score
    prog.attempts += 1

    learned = score >= settings.learned_score_threshold and await _deps_learned(
        session, payload.session_id, payload.entity_id
    )
    prog.status = "learned" if learned else "in_progress"
    await session.flush()

    unlocked: list[uuid.UUID] = []
    if learned:
        unlocked = await _cascade_unlock(
            session, payload.session_id, payload.entity_id
        )

    await session.commit()
    return TestResult(
        entity_id=payload.entity_id,
        score=score,
        status=prog.status,
        unlocked=unlocked,
    )


async def _get_or_create(
    session: AsyncSession, session_id: str, entity_id: uuid.UUID
) -> Progress:
    prog = (
        await session.execute(
            select(Progress).where(
                Progress.session_id == session_id,
                Progress.entity_id == entity_id,
            )
        )
    ).scalar_one_or_none()
    if prog is None:
        prog = Progress(session_id=session_id, entity_id=entity_id, attempts=0)
        session.add(prog)
        await session.flush()
    return prog


async def _deps_learned(
    session: AsyncSession, session_id: str, entity_id: uuid.UUID
) -> bool:
    """True, если все REQUIRES-пререквизиты узла имеют статус learned."""
    dep_ids = (
        await session.execute(
            select(Relation.to_id).where(
                Relation.from_id == entity_id,
                Relation.relation_type == REQUIRES,
            )
        )
    ).scalars().all()
    if not dep_ids:
        return True

    statuses = dict(
        (
            await session.execute(
                select(Progress.entity_id, Progress.status).where(
                    Progress.session_id == session_id,
                    Progress.entity_id.in_(dep_ids),
                )
            )
        ).all()
    )
    return all(statuses.get(dep_id) == "learned" for dep_id in dep_ids)


async def _cascade_unlock(
    session: AsyncSession, session_id: str, entity_id: uuid.UUID
) -> list[uuid.UUID]:
    """После learned-узла переоценить зависящие от него узлы вверх по графу.

    Зависимый узел становится learned, если он уже сдан на проходной балл
    и теперь все его пререквизиты выполнены.
    """
    unlocked: list[uuid.UUID] = []
    queue: list[uuid.UUID] = [entity_id]
    seen: set[uuid.UUID] = {entity_id}

    while queue:
        current = queue.pop()
        dependents = (
            await session.execute(
                select(Relation.from_id).where(
                    Relation.to_id == current,
                    Relation.relation_type == REQUIRES,
                )
            )
        ).scalars().all()

        for dep in dependents:
            if dep in seen:
                continue
            seen.add(dep)
            prog = (
                await session.execute(
                    select(Progress).where(
                        Progress.session_id == session_id,
                        Progress.entity_id == dep,
                    )
                )
            ).scalar_one_or_none()
            if prog is None or prog.score is None:
                continue
            if (
                prog.status != "learned"
                and prog.score >= settings.learned_score_threshold
                and await _deps_learned(session, session_id, dep)
            ):
                prog.status = "learned"
                await session.flush()
                unlocked.append(dep)
                queue.append(dep)

    return unlocked
