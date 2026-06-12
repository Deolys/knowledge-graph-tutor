"""Проверка графа книги на циклы в транзитивных отношениях (REQUIRES, PART_OF).

Цикл в REQUIRES намертво блокирует каскадную логику learned, поэтому такие
подграфы обязаны быть DAG. Для новых книг циклы разрываются в ingestion
(cycle_breaker); этот скрипт находит циклы у уже загруженных книг и
с флагом --fix удаляет слабейшие рёбра (минимальный confidence в цикле).

Использование:
    python scripts/check_graph_cycles.py <book_id> [--fix]
"""
import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import delete, select  # noqa: E402

from app.database import async_session_maker  # noqa: E402
from app.models import Entity, Relation  # noqa: E402
from app.ontology import load_ontology  # noqa: E402
from app.services.ingestion import cycle_breaker  # noqa: E402


async def check(book_id: str, fix: bool) -> None:
    ontology = load_ontology()
    transitive_types = {
        name
        for name, rt in ontology.relation_types.items()
        if rt.is_transitive
    }

    async with async_session_maker() as session:
        relations = (
            await session.execute(
                select(Relation).where(
                    Relation.book_id == book_id,
                    Relation.relation_type.in_(transitive_types),
                )
            )
        ).scalars().all()
        names = dict(
            (
                await session.execute(
                    select(Entity.id, Entity.name).where(
                        Entity.book_id == book_id
                    )
                )
            ).all()
        )

        edges = [
            {
                "id": r.id,
                "from_id": r.from_id,
                "to_id": r.to_id,
                "relation_type": r.relation_type,
                "confidence": r.confidence,
            }
            for r in relations
        ]
        _, removed = cycle_breaker.break_cycles(edges, transitive_types)

        if not removed:
            print(f"Циклов нет: проверено {len(edges)} рёбер "
                  f"({', '.join(sorted(transitive_types))})")
            return

        print(f"Найдено циклов (рёбер к удалению): {len(removed)}\n")
        for e in removed:
            print(f"  {e['relation_type']}: "
                  f"«{names.get(e['from_id'], e['from_id'])}» → "
                  f"«{names.get(e['to_id'], e['to_id'])}» "
                  f"(confidence={e['confidence']:.2f})")

        if fix:
            await session.execute(
                delete(Relation).where(
                    Relation.id.in_([e["id"] for e in removed])
                )
            )
            await session.commit()
            print(f"\nУдалено рёбер: {len(removed)}")
        else:
            print("\nЗапустите с --fix для удаления этих рёбер")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book_id")
    parser.add_argument(
        "--fix", action="store_true", help="удалить рёбра, разрывающие циклы"
    )
    args = parser.parse_args()
    asyncio.run(check(args.book_id, args.fix))
