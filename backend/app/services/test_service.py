"""Сервис тестов: ленивая генерация вопросов через LLM и проверка ответов.

Вопросы генерируются при первом запросе по сущности и кэшируются в БД.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import prompts
from app.config import settings
from app.models import Entity, Question
from app.ontology import load_ontology
from app.services import llm


async def get_or_generate_questions(
    session: AsyncSession, entity: Entity
) -> list[Question]:
    existing = (
        await session.execute(
            select(Question).where(Question.entity_id == entity.id)
        )
    ).scalars().all()
    if existing:
        return list(existing)

    ontology = load_ontology()
    label = (
        ontology.entity_types[entity.entity_type].label
        if entity.entity_type in ontology.entity_types
        else entity.entity_type
    )
    data = await llm.generate_json(
        prompts.generate_questions_system(settings.questions_per_concept),
        prompts.generate_questions_user(
            entity.name, label, entity.attrs or {}, entity.source_quote
        ),
    )
    questions: list[Question] = []
    for q in data.get("questions", []):
        options = q.get("options", [])
        correct = q.get("correct_idx", 0)
        if len(options) < 2 or not (0 <= correct < len(options)):
            continue
        row = Question(
            entity_id=entity.id,
            text=q["text"],
            options=options,
            correct_idx=correct,
            difficulty=q.get("difficulty", "medium"),
        )
        session.add(row)
        questions.append(row)
    await session.commit()
    return questions


async def score_answers(
    session: AsyncSession,
    entity_id: uuid.UUID,
    answers: dict[uuid.UUID, int],
) -> float:
    """Доля правильных ответов (0.0-1.0) по сущности."""
    questions = (
        await session.execute(
            select(Question).where(Question.entity_id == entity_id)
        )
    ).scalars().all()
    if not questions:
        return 0.0

    correct = sum(
        1 for q in questions if answers.get(q.id) == q.correct_idx
    )
    return correct / len(questions)
