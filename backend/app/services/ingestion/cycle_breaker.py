"""Разрыв циклов в транзитивных отношениях — их подграфы должны быть DAG.

Каскадная логика learned (progress_service) блокируется циклом намертво:
в цикле A→B→A ни один узел не станет learned, каждый ждёт другого. LLM
извлекает такие циклы регулярно. Стратегия разрыва: в найденном цикле
удаляется ребро с минимальным confidence; повторяем, пока подграф типа
не станет ацикличным. Циклы ищутся отдельно по каждому транзитивному типу
(REQUIRES и PART_OF независимы друг от друга).
"""
from collections import defaultdict
from typing import Hashable


def break_cycles(
    edges: list[dict], transitive_types: set[str]
) -> tuple[list[dict], list[dict]]:
    """Принимает рёбра вида {"from_id", "to_id", "relation_type", "confidence", …}.

    Возвращает (kept, removed). Рёбра нетранзитивных типов не проверяются
    и проходят как есть.
    """
    kept = [e for e in edges if e["relation_type"] not in transitive_types]
    removed: list[dict] = []
    for rtype in sorted(transitive_types):
        group = [e for e in edges if e["relation_type"] == rtype]
        acyclic, dropped = _break_cycles_one_type(group)
        kept.extend(acyclic)
        removed.extend(dropped)
    return kept, removed


def _break_cycles_one_type(
    edges: list[dict],
) -> tuple[list[dict], list[dict]]:
    removed: list[dict] = []
    current = list(edges)
    while True:
        cycle = _find_cycle(current)
        if cycle is None:
            return current, removed
        weakest = min(cycle, key=lambda e: e.get("confidence", 0.0))
        current = [e for e in current if e is not weakest]
        removed.append(weakest)


def _find_cycle(edges: list[dict]) -> list[dict] | None:
    """Итеративный DFS с трёхцветной раскраской; возвращает рёбра цикла."""
    out: dict[Hashable, list[dict]] = defaultdict(list)
    nodes: set[Hashable] = set()
    for e in edges:
        out[e["from_id"]].append(e)
        nodes.add(e["from_id"])
        nodes.add(e["to_id"])

    white, gray, black = 0, 1, 2
    color = dict.fromkeys(nodes, white)

    for start in nodes:
        if color[start] != white:
            continue
        color[start] = gray
        stack: list[tuple[Hashable, object]] = [(start, iter(out[start]))]
        path_edges: list[dict] = []
        while stack:
            node, it = stack[-1]
            advanced = False
            for edge in it:
                nxt = edge["to_id"]
                if color[nxt] == gray:
                    idx = next(
                        (
                            i
                            for i, pe in enumerate(path_edges)
                            if pe["from_id"] == nxt
                        ),
                        None,
                    )
                    if idx is None:
                        return [edge]
                    return path_edges[idx:] + [edge]
                if color[nxt] == white:
                    color[nxt] = gray
                    stack.append((nxt, iter(out[nxt])))
                    path_edges.append(edge)
                    advanced = True
                    break
            if not advanced:
                color[node] = black
                stack.pop()
                if path_edges:
                    path_edges.pop()
    return None
