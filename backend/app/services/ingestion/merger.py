"""Шаг 5: merge дублирующихся понятий между главами через эмбеддинги.

Группирует понятия с косинусной близостью >= MERGE_THRESHOLD. Канонический
в группе — с самым длинным определением. Возвращает канонические понятия
(с embedding и aliases) и карту name(lower) -> canonical name для переноса связей.

Источник: knowledge_graph_analytics.md, шаг 5.
"""
import numpy as np

from app.config import settings
from app.services import embeddings


def merge_concepts(
    all_concepts: list[dict],
) -> tuple[list[dict], dict[str, str]]:
    """Возвращает (канонические понятия, карту имя->каноническое имя)."""
    if not all_concepts:
        return [], {}

    names = [c["name"] for c in all_concepts]
    vecs = np.asarray(embeddings.encode_batch(names))

    visited: set[int] = set()
    groups: list[list[int]] = []
    for i in range(len(all_concepts)):
        if i in visited:
            continue
        group = [i]
        for j in range(i + 1, len(all_concepts)):
            if j in visited:
                continue
            sim = float(np.dot(vecs[i], vecs[j]))
            if sim >= settings.merge_threshold:
                group.append(j)
                visited.add(j)
        visited.add(i)
        groups.append(group)

    result: list[dict] = []
    name_map: dict[str, str] = {}
    for group in groups:
        canonical_idx = max(
            group, key=lambda i: len(all_concepts[i]["definition"])
        )
        canonical = dict(all_concepts[canonical_idx])
        canonical["embedding"] = vecs[canonical_idx].tolist()
        canonical["aliases"] = [
            all_concepts[i]["name"] for i in group if i != canonical_idx
        ]
        result.append(canonical)
        for i in group:
            name_map[all_concepts[i]["name"].lower()] = canonical["name"]

    return result, name_map
