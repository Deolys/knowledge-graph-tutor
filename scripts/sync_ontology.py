"""Синхронизация онтологии: ontology.yaml → таблицы БД.

Переносит entity_types / relation_types / profiles из YAML в PostgreSQL
(upsert по первичному ключу, удаление исчезнувших). Запускать после правки
ontology.yaml и до ingestion (entities FK ссылается на entity_types).

Использование:
    python scripts/sync_ontology.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import delete  # noqa: E402
from sqlalchemy.dialects.postgresql import insert  # noqa: E402

from app.database import async_session_maker  # noqa: E402
from app.models import EntityTypeRow, ProfileRow, RelationTypeRow  # noqa: E402
from app.ontology import load_ontology  # noqa: E402


async def sync() -> None:
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

    async with async_session_maker() as session:
        await _upsert(session, EntityTypeRow, "type_name", entity_rows)
        await _upsert(session, RelationTypeRow, "type_name", relation_rows)
        await _upsert(session, ProfileRow, "profile_name", profile_rows)
        await session.commit()

    print(
        f"Синхронизировано: {len(entity_rows)} типов сущностей, "
        f"{len(relation_rows)} типов отношений, {len(profile_rows)} профилей."
    )


async def _upsert(session, model, pk: str, rows: list[dict]) -> None:
    if not rows:
        return
    keys = {r[pk] for r in rows}
    # Удаляем строки, исчезнувшие из YAML.
    await session.execute(
        delete(model).where(getattr(model, pk).notin_(keys))
    )
    stmt = insert(model).values(rows)
    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in model.__table__.columns
        if c.name != pk
    }
    stmt = stmt.on_conflict_do_update(index_elements=[pk], set_=update_cols)
    await session.execute(stmt)


if __name__ == "__main__":
    asyncio.run(sync())
