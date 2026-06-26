"""Сервис тестов по графу: генерация набора из N вопросов по выбранным узлам.

Охват теста — выбранные сущности и/или главы (пусто = вся книга). Сущности
ранжируются по числу инцидентных связей (важные узлы — приоритет), берётся
top-K под бюджет вопросов, LLM генерирует ровно N вопросов разом. Правильные
ответы хранятся на сервере; клиенту вопросы отдаются без correct_idx.
"""
import uuid
from collections import defaultdict
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import prompts
from app.models import Book, Entity, Relation, Test, TestQuestion
from app.ontology import load_ontology
from app.services import llm

# Сколько сущностей максимум подаём в LLM-контекст (на ~1 вопрос приходится
# не больше пары узлов; больше — лишний расход токенов).
MAX_CONTEXT_ENTITIES = 60


class TestGenerationError(Exception):
    """Не удалось сгенерировать тест (нет сущностей или пустой ответ LLM)."""


async def create_test(
    session: AsyncSession,
    book_id: uuid.UUID,
    session_id: str,
    question_count: int,
    title: str | None,
    entity_ids: list[uuid.UUID],
    chapter_ids: list[uuid.UUID],
) -> Test:
    book = await session.get(Book, book_id)
    if book is None:
        raise TestGenerationError("Книга не найдена")

    entities = await _select_entities(
        session, book_id, entity_ids, chapter_ids
    )
    if not entities:
        raise TestGenerationError("Нет сущностей для генерации теста")

    ontology = load_ontology()
    context = [
        {
            "name": e.name,
            "label": (
                ontology.entity_types[e.entity_type].label
                if e.entity_type in ontology.entity_types
                else e.entity_type
            ),
            "attrs": e.attrs or {},
            "source_quote": e.source_quote,
        }
        for e in entities[:MAX_CONTEXT_ENTITIES]
    ]
    name_to_id = {e.name: e.id for e in entities}

    data = await llm.generate_json(
        prompts.generate_test_system(question_count),
        prompts.generate_test_user(context),
    )
    raw_questions = data.get("questions", [])

    test = Test(
        book_id=book_id,
        session_id=session_id,
        title=title or _default_title(book.title, question_count),
        question_count=0,
        status="ready",
    )
    session.add(test)
    await session.flush()

    order = 0
    for q in raw_questions:
        options = q.get("options", [])
        correct = q.get("correct_idx", 0)
        text = q.get("text")
        if not text or len(options) < 2 or not (0 <= correct < len(options)):
            continue
        ent_name = q.get("entity_name")
        session.add(
            TestQuestion(
                test_id=test.id,
                entity_id=name_to_id.get(ent_name),
                entity_name=ent_name,
                order_num=order,
                text=text,
                options=options,
                correct_idx=correct,
                difficulty=q.get("difficulty", "medium"),
            )
        )
        order += 1

    if order == 0:
        raise TestGenerationError("LLM не вернул валидных вопросов")

    test.question_count = order
    await session.commit()
    await session.refresh(test)
    return test


async def _select_entities(
    session: AsyncSession,
    book_id: uuid.UUID,
    entity_ids: list[uuid.UUID],
    chapter_ids: list[uuid.UUID],
) -> list[Entity]:
    """Сущности охвата, отсортированные по убыванию числа инцидентных связей."""
    stmt = select(Entity).where(Entity.book_id == book_id)
    if entity_ids:
        stmt = stmt.where(Entity.id.in_(entity_ids))
    elif chapter_ids:
        stmt = stmt.where(Entity.chapter_id.in_(chapter_ids))
    entities = (await session.execute(stmt)).scalars().all()
    if not entities:
        return []

    ids = {e.id for e in entities}
    relations = (
        await session.execute(
            select(Relation.from_id, Relation.to_id).where(
                Relation.book_id == book_id
            )
        )
    ).all()
    degree: dict[uuid.UUID, int] = defaultdict(int)
    for frm, to in relations:
        if frm in ids:
            degree[frm] += 1
        if to in ids:
            degree[to] += 1

    return sorted(entities, key=lambda e: degree.get(e.id, 0), reverse=True)


def _default_title(book_title: str, n: int) -> str:
    return f"Тест по «{book_title}» ({n} вопр.)"


async def list_tests(
    session: AsyncSession, session_id: str
) -> list[tuple[Test, str]]:
    """Тесты сессии с названием книги, новые сверху."""
    rows = (
        await session.execute(
            select(Test, Book.title)
            .join(Book, Test.book_id == Book.id)
            .where(Test.session_id == session_id)
            .order_by(Test.created_at.desc())
        )
    ).all()
    return [(t, title) for t, title in rows]


async def get_test(
    session: AsyncSession, test_id: uuid.UUID
) -> tuple[Test, str] | None:
    row = (
        await session.execute(
            select(Test, Book.title)
            .join(Book, Test.book_id == Book.id)
            .where(Test.id == test_id)
        )
    ).first()
    if row is None:
        return None
    test, title = row
    await session.refresh(test, ["questions"])
    return test, title


async def submit_test(
    session: AsyncSession,
    test_id: uuid.UUID,
    answers: dict[uuid.UUID, int],
) -> Test | None:
    test = await session.get(Test, test_id)
    if test is None:
        return None
    await session.refresh(test, ["questions"])

    correct = 0
    for q in test.questions:
        selected = answers.get(q.id)
        q.selected_idx = selected
        if selected is not None and selected == q.correct_idx:
            correct += 1

    total = len(test.questions)
    test.score = correct / total if total else 0.0
    test.status = "completed"
    # naive UTC — колонка TIMESTAMP WITHOUT TIME ZONE (как остальная схема)
    test.completed_at = datetime.utcnow()
    await session.commit()
    await session.refresh(test, ["questions"])
    return test


async def delete_test(session: AsyncSession, test_id: uuid.UUID) -> bool:
    result = await session.execute(delete(Test).where(Test.id == test_id))
    await session.commit()
    return result.rowcount > 0
