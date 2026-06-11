"""Оценка качества графа: precision/recall/F1 против эталона, по типам.

Метрики считаются отдельно по типам сущностей и по типам отношений
(knowledge_graph_analytics.md §10). Эталон — ручная разметка одной главы.

Использование:
    python scripts/eval_graph_quality.py <book_id> path/to/gold.json

Формат gold.json:
    {
      "entities": [
        {"name": "Предел", "entity_type": "concept"},
        {"name": "Теорема Вейерштрасса", "entity_type": "theorem"}
      ],
      "relations": [
        ["Производная", "Предел", "REQUIRES"]
      ]
    }
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select  # noqa: E402

from app.database import async_session_maker  # noqa: E402
from app.models import Entity, Relation  # noqa: E402


def _norm(s: str) -> str:
    return s.strip().lower()


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return precision, recall, f1


def _report(title: str, gold: set, pred: set) -> None:
    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)
    p, r, f1 = _prf(tp, fp, fn)
    print(f"{title}: TP={tp} FP={fp} FN={fn} | P={p:.3f} R={r:.3f} F1={f1:.3f}")


async def evaluate(book_id: str, gold_path: str) -> None:
    with open(gold_path, encoding="utf-8") as f:
        gold = json.load(f)

    gold_entities = {
        (_norm(e["name"]), e["entity_type"]) for e in gold.get("entities", [])
    }

    async with async_session_maker() as session:
        entities = (
            await session.execute(
                select(Entity).where(Entity.book_id == book_id)
            )
        ).scalars().all()
        pred_entities = {(_norm(e.name), e.entity_type) for e in entities}
        id_to_name = {e.id: _norm(e.name) for e in entities}

        relations = (
            await session.execute(
                select(Relation).where(Relation.book_id == book_id)
            )
        ).scalars().all()

    print("=== Сущности (overall) ===")
    _report("ВСЕ", gold_entities, pred_entities)

    print("\n=== Сущности по типам ===")
    types = {t for _, t in gold_entities} | {t for _, t in pred_entities}
    for t in sorted(types):
        g = {n for n, tt in gold_entities if tt == t}
        p = {n for n, tt in pred_entities if tt == t}
        if g or p:
            _report(t, g, p)

    gold_rel = {
        (_norm(a), _norm(b), t) for a, b, t in gold.get("relations", [])
    }
    if gold_rel:
        pred_rel = {
            (id_to_name[r.from_id], id_to_name[r.to_id], r.relation_type)
            for r in relations
            if r.from_id in id_to_name and r.to_id in id_to_name
        }
        print("\n=== Отношения (overall) ===")
        _report("ВСЕ", gold_rel, pred_rel)

        print("\n=== Отношения по типам ===")
        rtypes = {t for _, _, t in gold_rel} | {t for _, _, t in pred_rel}
        for t in sorted(rtypes):
            g = {(a, b) for a, b, tt in gold_rel if tt == t}
            p = {(a, b) for a, b, tt in pred_rel if tt == t}
            if g or p:
                _report(t, g, p)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/eval_graph_quality.py <book_id> <gold.json>")
        raise SystemExit(1)
    asyncio.run(evaluate(sys.argv[1], sys.argv[2]))
