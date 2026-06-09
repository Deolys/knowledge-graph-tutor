"""Оценка качества графа: precision/recall/F1 против эталона.

Эталон — JSON со списком имён понятий (и опционально связей), составленный
вручную по одной главе. Скрипт сверяет извлечённые понятия книги из БД
с эталоном по нормализованным именам.

Использование:
    python scripts/eval_graph_quality.py <book_id> path/to/gold.json

Формат gold.json:
    {
      "concepts": ["Предел", "Производная", ...],
      "relations": [["Производная", "Предел", "depends_on"], ...]   # опционально
    }
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select  # noqa: E402

from app.database import async_session_maker  # noqa: E402
from app.models import Concept, Relation  # noqa: E402


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


async def evaluate(book_id: str, gold_path: str) -> None:
    with open(gold_path, encoding="utf-8") as f:
        gold = json.load(f)

    gold_concepts = {_norm(c) for c in gold.get("concepts", [])}

    async with async_session_maker() as session:
        concepts = (
            await session.execute(
                select(Concept).where(Concept.book_id == book_id)
            )
        ).scalars().all()
        pred_concepts = {_norm(c.name) for c in concepts}
        id_to_name = {c.id: _norm(c.name) for c in concepts}

        relations = (
            await session.execute(
                select(Relation).where(
                    Relation.from_id.in_(list(id_to_name)),
                )
            )
        ).scalars().all()

    # Понятия
    tp = len(pred_concepts & gold_concepts)
    fp = len(pred_concepts - gold_concepts)
    fn = len(gold_concepts - pred_concepts)
    p, r, f1 = _prf(tp, fp, fn)
    print("=== Понятия ===")
    print(f"TP={tp} FP={fp} FN={fn}")
    print(f"Precision={p:.3f} Recall={r:.3f} F1={f1:.3f}")

    # Связи (если есть эталон)
    gold_rel = {
        (_norm(a), _norm(b), t) for a, b, t in gold.get("relations", [])
    }
    if gold_rel:
        pred_rel = {
            (id_to_name[rel.from_id], id_to_name[rel.to_id], rel.type)
            for rel in relations
            if rel.from_id in id_to_name and rel.to_id in id_to_name
        }
        rtp = len(pred_rel & gold_rel)
        rfp = len(pred_rel - gold_rel)
        rfn = len(gold_rel - pred_rel)
        rp, rr, rf1 = _prf(rtp, rfp, rfn)
        print("\n=== Связи ===")
        print(f"TP={rtp} FP={rfp} FN={rfn}")
        print(f"Precision={rp:.3f} Recall={rr:.3f} F1={rf1:.3f}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/eval_graph_quality.py <book_id> <gold.json>")
        raise SystemExit(1)
    asyncio.run(evaluate(sys.argv[1], sys.argv[2]))
