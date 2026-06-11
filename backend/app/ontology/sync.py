"""Синхронизация онтологии из YAML в таблицы БД.

Логика вынесена сюда (а не в scripts/), чтобы быть доступной и для CLI-скрипта,
и для авто-синхронизации при старте приложения. Upsert по первичному ключу +
удаление строк, исчезнувших из YAML. Идемпотентна.
"""
import logging

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import EntityTypeRow, ProfileRow, RelationTypeRow
from app.ontology import load_ontology

logger = logging.getLogger(__name__)


async def sync_ontology(session: AsyncSession) -> tuple[int, int, int]:
    """Переносит онтологию из YAML в БД. Возвращает счётчики (типы, отношения, профили)."""
    ont = load_ontology()

    entity_rows = [
        {
            "type_name": et.type_name,
            "label": et.label,
            "description": et.description,
            "attrs": et.attrs,
            "color": et.color,
            "tier": et.tier,
        }
        for et in ont.entity_types.values()
    ]
    relation_rows = [
        {
            "type_name": rt.type_name,
            "label": rt.label,
            "domain_types": rt.domain_types,
            "range_types": rt.range_types,
            "is_transitive": rt.is_transitive,
            "is_symmetric": rt.is_symmetric,
            "traversal_weight": rt.traversal_weight,
        }
        for rt in ont.relation_types.values()
    ]
    profile_rows = [
        {"profile_name": p.profile_name, "entity_types": p.entity_types}
        for p in ont.profiles.values()
    ]

    await _upsert(session, EntityTypeRow, "type_name", entity_rows)
    await _upsert(session, RelationTypeRow, "type_name", relation_rows)
    await _upsert(session, ProfileRow, "profile_name", profile_rows)
    await session.commit()
    return len(entity_rows), len(relation_rows), len(profile_rows)


async def sync_on_startup() -> None:
    """Авто-синхронизация при старте. Если схемы ещё нет — мягко пропускаем."""
    try:
        async with async_session_maker() as session:
            counts = await sync_ontology(session)
        logger.info(
            "Онтология синхронизирована: %d типов, %d отношений, %d профилей",
            *counts,
        )
    except ProgrammingError:
        logger.warning(
            "Таблицы онтологии не найдены — пропускаю синхронизацию. "
            "Выполните 'alembic upgrade head' и перезапустите backend."
        )
    except Exception:
        logger.exception("Не удалось синхронизировать онтологию при старте")


async def _upsert(session, model, pk: str, rows: list[dict]) -> None:
    if not rows:
        return
    keys = {r[pk] for r in rows}
    await session.execute(delete(model).where(getattr(model, pk).notin_(keys)))
    stmt = insert(model).values(rows)
    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in model.__table__.columns
        if c.name != pk
    }
    stmt = stmt.on_conflict_do_update(index_elements=[pk], set_=update_cols)
    await session.execute(stmt)
