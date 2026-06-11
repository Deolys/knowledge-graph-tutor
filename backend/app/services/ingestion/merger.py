"""Merge дублирующихся сущностей между главами — СТРОГО внутри одного типа.

Концепт «Python» и инструмент «Python» — разные узлы, не мержим. Внутри
группы одного entity_type объединяем по косинусной близости ≥ MERGE_THRESHOLD.
Канонический — с наибольшим числом заполненных атрибутов. Возвращает
канонические сущности (с embedding и aliases) и карту name(lower)→canonical name.

Источник: knowledge_graph_analytics.md §4.3.
"""
from collections import defaultdict

import numpy as np

from app.config import settings
from app.services import embeddings


def _embed_text(entity: dict) -> str:
    """Текст для эмбеддинга: имя + ключевой текстовый атрибут, если есть."""
    parts = [entity["name"]]
    attrs = entity.get("attrs") or {}
    for key in ("definition", "statement", "description"):
        val = attrs.get(key)
        if isinstance(val, str) and val:
            parts.append(val)
            break
    return " — ".join(parts)


def _richness(entity: dict) -> int:
    """Насколько сущность «полная»: число непустых атрибутов."""
    attrs = entity.get("attrs") or {}
    return sum(1 for v in attrs.values() if v not in (None, "", [], {}))


def merge_entities(
    all_entities: list[dict],
) -> tuple[list[dict], dict[str, str]]:
    """Возвращает (канонические сущности, карту имя(lower)→каноническое имя)."""
    if not all_entities:
        return [], {}

    vecs = np.asarray(embeddings.encode_batch([_embed_text(e) for e in all_entities]))

    # Индексы сгруппированы по типу — мержим только внутри типа.
    by_type: dict[str, list[int]] = defaultdict(list)
    for idx, e in enumerate(all_entities):
        by_type[e["entity_type"]].append(idx)

    result: list[dict] = []
    name_map: dict[str, str] = {}

    for indices in by_type.values():
        visited: set[int] = set()
        for i in indices:
            if i in visited:
                continue
            group = [i]
            visited.add(i)
            for j in indices:
                if j in visited:
                    continue
                if float(np.dot(vecs[i], vecs[j])) >= settings.merge_threshold:
                    group.append(j)
                    visited.add(j)

            canonical_idx = max(group, key=lambda k: _richness(all_entities[k]))
            canonical = dict(all_entities[canonical_idx])
            canonical["attrs"] = dict(canonical.get("attrs") or {})
            canonical["embedding"] = vecs[canonical_idx].tolist()
            aliases = sorted(
                {
                    all_entities[k]["name"]
                    for k in group
                    if k != canonical_idx
                    and all_entities[k]["name"] != canonical["name"]
                }
            )
            if aliases:
                existing = canonical["attrs"].get("aliases") or []
                merged = list(dict.fromkeys([*existing, *aliases]))
                canonical["attrs"]["aliases"] = merged
            result.append(canonical)
            for k in group:
                name_map[all_entities[k]["name"].lower()] = canonical["name"]

    return result, name_map
