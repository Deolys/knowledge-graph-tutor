"""QA-сервис: векторный поиск -> расширение контекста по графу -> ответ LLM.

1. Эмбеддинг вопроса -> top-k ближайших понятий (pgvector, cosine).
2. Расширение контекста соседями глубины 1 (входящие/исходящие рёбра).
3. Формирование текстового контекста и вызов LLM (ответ только по контексту).
"""
import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import prompts
from app.models import Concept, Relation
from app.schemas.qa import QARequest, QAResponse, QASource
from app.services import embeddings, llm

TOP_K = 5


async def answer(session: AsyncSession, payload: QARequest) -> QAResponse:
    query_vec = embeddings.encode(payload.query)

    # 1. Векторный поиск ближайших понятий книги
    relevant = (
        await session.execute(
            select(Concept)
            .where(Concept.book_id == payload.book_id)
            .order_by(Concept.embedding.cosine_distance(query_vec))
            .limit(TOP_K)
        )
    ).scalars().all()

    if not relevant:
        return QAResponse(
            answer="В данной главе это не рассматривается", sources=[]
        )

    # 2. Расширение контекста соседями глубины 1
    relevant_ids = [c.id for c in relevant]
    neighbor_ids = (
        await session.execute(
            select(Relation.from_id, Relation.to_id).where(
                or_(
                    Relation.from_id.in_(relevant_ids),
                    Relation.to_id.in_(relevant_ids),
                )
            )
        )
    ).all()
    context_ids: set[uuid.UUID] = set(relevant_ids)
    for frm, to in neighbor_ids:
        context_ids.add(frm)
        context_ids.add(to)

    context_concepts = (
        await session.execute(
            select(Concept).where(Concept.id.in_(context_ids))
        )
    ).scalars().all()

    # 3. Контекст -> LLM
    context = _format_context(context_concepts)
    answer_text = await llm.generate_text(
        prompts.qa_system(context), payload.query
    )

    sources = [QASource(id=c.id, name=c.name) for c in relevant]
    return QAResponse(answer=answer_text, sources=sources)


def _format_context(concepts: list[Concept]) -> str:
    parts = []
    for c in concepts:
        block = f"### {c.name}\n{c.definition}"
        if c.formula:
            block += f"\nФормула: {c.formula}"
        parts.append(block)
    return "\n\n".join(parts)
