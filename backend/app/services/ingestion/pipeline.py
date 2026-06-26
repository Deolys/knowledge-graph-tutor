"""Оркестратор ingestion — единая точка входа для всего пайплайна.

API-роутеры вызывают только run_ingestion(). Поток (онтологически управляемый):
parse PDF → главы → по каждой главе типизированное извлечение сущностей и
отношений (промпты из активного профиля) → онтологическая валидация →
merge внутри типа → разрыв циклов в транзитивных отношениях → запись
типизированных узлов и рёбер.
"""
import logging
import uuid

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Book, Chapter, Entity, Relation
from app.ontology import load_ontology
from app.services import llm
from app.services.ingestion import (
    cycle_breaker,
    extractor,
    merger,
    pdf_parser,
    validator,
)

logger = logging.getLogger(__name__)


async def run_ingestion(
    session: AsyncSession, book_id: uuid.UUID, pdf_path: str
) -> None:
    """Полный прогон пайплайна для одной книги (по её профилю онтологии).

    Все LLM-вызовы пайплайна оборачиваются в track_usage; суммарные токены
    записываются в книгу (оценка стоимости построения графа).
    """
    with llm.track_usage() as usage:
        await _run_ingestion(session, book_id, pdf_path, usage)


async def _run_ingestion(
    session: AsyncSession,
    book_id: uuid.UUID,
    pdf_path: str,
    usage: "llm.TokenUsage",
) -> None:
    book = await session.get(Book, book_id)
    ontology = load_ontology()
    profile = ontology.profile(book.profile if book else "universal")

    raw_chapters = pdf_parser.extract_chapters(pdf_path)

    chapter_rows: list[Chapter] = []
    for ch in raw_chapters:
        row = Chapter(
            book_id=book_id,
            title=ch["title"],
            order_num=ch["order_num"],
            raw_text=ch["raw_text"],
            status="pending",
        )
        session.add(row)
        chapter_rows.append(row)
    await session.flush()

    all_entities: list[dict] = []
    all_relations: list[dict] = []

    for ch_row, ch in zip(chapter_rows, raw_chapters):
        await _set_status(session, ch_row.id, "processing")
        try:
            entities = validator.validate_entities(
                await extractor.extract_entities(
                    profile, ch["title"], ch["raw_text"]
                ),
                profile,
                ch["raw_text"],
            )
            relations = validator.validate_relations(
                entities,
                await extractor.extract_relations(
                    profile, entities, ch["raw_text"]
                ),
                profile,
                ch["raw_text"],
            )
            for e in entities:
                e["chapter_id"] = ch_row.id
            all_entities.extend(entities)
            all_relations.extend(relations)
            await _set_status(session, ch_row.id, "done")
        except Exception:
            await _set_status(session, ch_row.id, "error")
            raise

    # Merge между главами — строго внутри типа.
    canonical, name_map = merger.merge_entities(all_entities)

    # Запись канонических узлов; name(lower) -> (Entity.id, chapter_id).
    entity_ids: dict[str, uuid.UUID] = {}
    chapter_by_name: dict[str, uuid.UUID | None] = {}
    for e in canonical:
        row = Entity(
            book_id=book_id,
            chapter_id=e.get("chapter_id"),
            entity_type=e["entity_type"],
            name=e["name"],
            attrs=e.get("attrs") or {},
            source_quote=e.get("source_quote"),
            embedding=e["embedding"],
        )
        session.add(row)
        await session.flush()
        entity_ids[e["name"].lower()] = row.id
        chapter_by_name[e["name"].lower()] = e.get("chapter_id")

    # Резолвинг рёбер: имена → канонические имена → id.
    seen: set[tuple[uuid.UUID, uuid.UUID, str]] = set()
    edge_dicts: list[dict] = []
    for r in all_relations:
        frm_name = name_map.get(r["from"].lower())
        to_name = name_map.get(r["to"].lower())
        if not frm_name or not to_name:
            continue
        from_id = entity_ids.get(frm_name.lower())
        to_id = entity_ids.get(to_name.lower())
        if not from_id or not to_id or from_id == to_id:
            continue
        key = (from_id, to_id, r["relation_type"])
        if key in seen:
            continue
        seen.add(key)
        from_ch = chapter_by_name.get(frm_name.lower())
        to_ch = chapter_by_name.get(to_name.lower())
        edge_dicts.append(
            {
                "from_id": from_id,
                "to_id": to_id,
                "relation_type": r["relation_type"],
                "confidence": r["confidence"],
                "source_quote": r["source_quote"],
                "is_cross_chapter": bool(
                    from_ch and to_ch and from_ch != to_ch
                ),
            }
        )

    # Транзитивные отношения (REQUIRES, PART_OF) должны быть DAG — иначе
    # каскадная логика learned блокируется циклом навсегда.
    transitive_types = {
        name
        for name, rt in ontology.relation_types.items()
        if rt.is_transitive
    }
    kept_edges, removed_edges = cycle_breaker.break_cycles(
        edge_dicts, transitive_types
    )
    for e in removed_edges:
        logger.warning(
            "Разрыв цикла %s: удалено ребро %s → %s (confidence=%.2f)",
            e["relation_type"],
            e["from_id"],
            e["to_id"],
            e["confidence"],
        )

    for e in kept_edges:
        session.add(Relation(book_id=book_id, **e))

    if book is not None:
        book.prompt_tokens = usage.prompt_tokens
        book.completion_tokens = usage.completion_tokens
        book.total_tokens = usage.total_tokens
        book.llm_calls = usage.calls
        logger.info(
            "Ingestion tokens book_id=%s: total=%d (prompt=%d, completion=%d) "
            "за %d вызовов LLM",
            book_id,
            usage.total_tokens,
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.calls,
        )

    await session.commit()


async def _set_status(
    session: AsyncSession, chapter_id: uuid.UUID, status: str
) -> None:
    await session.execute(
        update(Chapter).where(Chapter.id == chapter_id).values(status=status)
    )
    await session.flush()
