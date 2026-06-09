"""Оркестратор ingestion — единая точка входа для всего пайплайна.

API-роутеры вызывают только run_ingestion(), а не отдельные шаги. Это
позволяет менять/переставлять шаги, не трогая API.

Поток: parse PDF -> сохранить главы -> по каждой главе извлечь понятия+связи
-> валидация -> merge между главами -> запись узлов и рёбер в БД.
"""
import uuid

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chapter, Concept, Relation
from app.services.ingestion import extractor, merger, pdf_parser, validator


async def run_ingestion(
    session: AsyncSession, book_id: uuid.UUID, pdf_path: str
) -> None:
    """Полный прогон пайплайна для одной книги."""
    raw_chapters = pdf_parser.extract_chapters(pdf_path)

    # Сохраняем главы (status=pending)
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
    await session.flush()  # получить id глав

    # Аккумулируем понятия и связи со всех глав
    # каждый concept помечаем chapter_id, чтобы потом записать узлы
    all_concepts: list[dict] = []
    all_relations: list[dict] = []

    for ch_row, ch in zip(chapter_rows, raw_chapters):
        await _set_status(session, ch_row.id, "processing")
        try:
            concepts = validator.validate_concepts(
                await extractor.extract_concepts(ch["title"], ch["raw_text"])
            )
            relations = validator.validate_relations(
                concepts,
                await extractor.extract_relations(concepts, ch["raw_text"]),
            )
            for c in concepts:
                c["chapter_id"] = ch_row.id
            all_concepts.extend(concepts)
            all_relations.extend(relations)
            await _set_status(session, ch_row.id, "done")
        except Exception:
            await _set_status(session, ch_row.id, "error")
            raise

    # Merge между главами
    canonical, name_map = merger.merge_concepts(all_concepts)

    # Запись канонических узлов; name(lower) -> Concept.id
    concept_ids: dict[str, uuid.UUID] = {}
    for c in canonical:
        row = Concept(
            book_id=book_id,
            chapter_id=c["chapter_id"],
            name=c["name"],
            definition=c["definition"],
            formula=c.get("formula"),
            quote=c.get("quote"),
            embedding=c["embedding"],
        )
        session.add(row)
        await session.flush()
        concept_ids[c["name"].lower()] = row.id

    # Запись рёбер: имена переводим в канонические, затем в id
    seen: set[tuple[uuid.UUID, uuid.UUID, str]] = set()
    for r in all_relations:
        frm_name = name_map.get(r["from"].lower())
        to_name = name_map.get(r["to"].lower())
        if not frm_name or not to_name:
            continue
        from_id = concept_ids.get(frm_name.lower())
        to_id = concept_ids.get(to_name.lower())
        if not from_id or not to_id or from_id == to_id:
            continue
        key = (from_id, to_id, r["type"])
        if key in seen:
            continue
        seen.add(key)
        session.add(
            Relation(
                from_id=from_id,
                to_id=to_id,
                type=r["type"],
                confidence=r["confidence"],
            )
        )

    await session.commit()


async def _set_status(
    session: AsyncSession, chapter_id: uuid.UUID, status: str
) -> None:
    await session.execute(
        update(Chapter).where(Chapter.id == chapter_id).values(status=status)
    )
    await session.flush()
