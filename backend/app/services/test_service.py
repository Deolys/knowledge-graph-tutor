"""Сервис тестов: ленивая генерация вопросов через LLM и проверка ответов.

Вопросы генерируются при первом запросе по понятию и кэшируются в БД,
чтобы не дёргать LLM повторно (см. раздел 8 аналитики, риск со сроками).
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import prompts
from app.config import settings
from app.models import Concept, Question
from app.services import llm


async def get_or_generate_questions(
    session: AsyncSession, concept: Concept
) -> list[Question]:
    existing = (
        await session.execute(
            select(Question).where(Question.concept_id == concept.id)
        )
    ).scalars().all()
    if existing:
        return list(existing)

    data = await llm.generate_json(
        prompts.generate_questions_system(settings.questions_per_concept),
        prompts.generate_questions_user(
            concept.name, concept.definition, concept.quote, concept.formula
        ),
    )
    questions: list[Question] = []
    for q in data.get("questions", []):
        options = q.get("options", [])
        correct = q.get("correct_idx", 0)
        if len(options) < 2 or not (0 <= correct < len(options)):
            continue
        row = Question(
            concept_id=concept.id,
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
    concept_id: uuid.UUID,
    answers: dict[uuid.UUID, int],
) -> float:
    """Доля правильных ответов (0.0-1.0) по понятию."""
    questions = (
        await session.execute(
            select(Question).where(Question.concept_id == concept_id)
        )
    ).scalars().all()
    if not questions:
        return 0.0

    correct = sum(
        1
        for q in questions
        if answers.get(q.id) == q.correct_idx
    )
    return correct / len(questions)
