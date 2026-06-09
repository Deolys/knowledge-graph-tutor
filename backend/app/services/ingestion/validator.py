"""Шаг 4: валидация и фильтрация по confidence.

Отсеивает структурно битые понятия и галлюцинированные/неуверенные связи.
Источник правил: knowledge_graph_analytics.md, шаг 4.
"""
from app.config import settings


def validate_concepts(raw: list[dict]) -> list[dict]:
    valid = []
    for c in raw:
        if not c.get("name") or not c.get("definition"):
            continue
        if len(c["name"]) < 2 or len(c["name"]) > 100:
            continue
        if len(c["definition"]) < 10:
            continue
        valid.append(c)
    return valid


def validate_relations(
    concepts: list[dict], relations: list[dict]
) -> list[dict]:
    names = {c["name"].lower() for c in concepts}
    valid = []
    for r in relations:
        if r.get("confidence", 0) < settings.confidence_threshold:
            continue
        frm, to = r.get("from", ""), r.get("to", "")
        if frm.lower() not in names or to.lower() not in names:
            continue  # галлюцинированная связь
        if frm == to:
            continue
        valid.append(r)
    return valid
