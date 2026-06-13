"""GraphRAG: классификация вопроса → entity linking → типизированный обход → ответ.

Поток (knowledge_graph_analytics.md §5):
1. Классификация типа вопроса (дешёвая модель) → шаблон обхода.
2. Entity linking: эмбеддинг вопроса → top-3 сущности книги.
3. Обход графа по шаблону (BFS вдоль заданных отношений/направлений/глубины)
   с затуханием релевантности вдоль пути (см. _traverse).
4. Сборка структурированного контекста (группировка по типам, с цитатами).
5. LLM-ответ строго из контекста.
Если ни одна сущность не привязалась с порогом — vector_fallback (top-5 без обхода).

Поле QARequest.mode позволяет принудительно выбрать стратегию для экспериментов:
auto (обычное поведение), graphrag (обход даже при слабой привязке),
vector (только векторный поиск), none (бейзлайн без контекста).
"""
import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import prompts
from app.config import settings
from app.models import Entity, Relation
from app.ontology import Ontology, TraversalTemplate, load_ontology
from app.schemas.qa import QARequest, QAResponse, QASource, TraversalEdge
from app.services import embeddings, llm

LINK_TOP_K = 3
FALLBACK_TOP_K = 5


async def answer(session: AsyncSession, payload: QARequest) -> QAResponse:
    if payload.mode == "none":
        return await _no_context(payload)

    ontology = load_ontology()
    query_vec = embeddings.encode(payload.query)

    if payload.mode == "vector":
        return await _vector_fallback(session, payload, query_vec)

    linked = await _link_entities(session, payload.book_id, query_vec, LINK_TOP_K)
    best_sim = linked[0][1] if linked else 0.0

    if not linked or (
        payload.mode != "graphrag"
        and best_sim < settings.entity_link_threshold
    ):
        return await _vector_fallback(session, payload, query_vec)

    template = await _classify(payload.query, ontology)
    matched_pairs = [
        (e, sim) for e, sim in linked if e.entity_type in template.match_types
    ]
    if not matched_pairs:
        matched_pairs = linked
    matched = [e for e, _ in matched_pairs]

    context_entities, edges = await _traverse(
        session, payload.book_id, matched_pairs, template, ontology
    )

    context = _format_context(context_entities, ontology)
    answer_text = await llm.generate_text(
        prompts.qa_system(context), payload.query
    )

    sources = [QASource(id=e.id, name=e.name, entity_type=e.entity_type) for e in matched]
    traversal_nodes = [e.id for e in context_entities]
    traversal_edges = [
        TraversalEdge(source=f, target=t, relation_type=rt)
        for f, t, rt in edges
    ]
    return QAResponse(
        answer=answer_text,
        sources=sources,
        traversal_nodes=traversal_nodes,
        traversal_edges=traversal_edges,
        mode="graphrag",
    )


async def _classify(query: str, ontology: Ontology) -> TraversalTemplate:
    names = list(ontology.templates.keys())
    default = ontology.templates.get("definition") or next(
        iter(ontology.templates.values())
    )
    if not names:
        return default
    try:
        data = await llm.generate_json(
            prompts.classify_question_system(names),
            query,
            model=settings.llm_classifier_model,
        )
        return ontology.templates.get(data.get("type", ""), default)
    except llm.LLMError:
        return default


async def _link_entities(
    session: AsyncSession,
    book_id: uuid.UUID,
    query_vec: list[float],
    limit: int,
) -> list[tuple[Entity, float]]:
    rows = (
        await session.execute(
            select(
                Entity,
                Entity.embedding.cosine_distance(query_vec).label("dist"),
            )
            .where(Entity.book_id == book_id, Entity.embedding.isnot(None))
            .order_by("dist")
            .limit(limit)
        )
    ).all()
    return [(row[0], 1.0 - float(row[1])) for row in rows]


async def _traverse(
    session: AsyncSession,
    book_id: uuid.UUID,
    matched: list[tuple[Entity, float]],
    template: TraversalTemplate,
    ontology: Ontology,
) -> tuple[list[Entity], list[tuple[uuid.UUID, uuid.UUID, str]]]:
    """BFS с затуханием релевантности вдоль пути.

    Стартовый скор узла — близость вопроса к привязанной сущности; при переходе
    по ребру он умножается на traversal_weight × confidence, поэтому дальние
    узлы естественно ранжируются ниже ближних. Итоговый скор узла — максимум
    по всем путям/шагам шаблона.
    """
    relations = (
        await session.execute(
            select(Relation).where(Relation.book_id == book_id)
        )
    ).scalars().all()

    out_by_node: dict[uuid.UUID, list[Relation]] = defaultdict(list)
    in_by_node: dict[uuid.UUID, list[Relation]] = defaultdict(list)
    for r in relations:
        out_by_node[r.from_id].append(r)
        in_by_node[r.to_id].append(r)

    seeds = {e.id: sim for e, sim in matched}
    matched_ids = set(seeds)
    scores: dict[uuid.UUID, float] = dict(seeds)
    used_edges: set[tuple[uuid.UUID, uuid.UUID, str]] = set()

    for step in template.expand:
        weight = (
            ontology.relation_types[step.relation].traversal_weight
            if step.relation in ontology.relation_types
            else 0.5
        )
        frontier: dict[uuid.UUID, float] = dict(seeds)
        for _ in range(step.depth):
            nxt: dict[uuid.UUID, float] = {}
            for node, node_score in frontier.items():
                edges: list[tuple[Relation, uuid.UUID]] = []
                if step.direction in ("out", "both"):
                    edges += [
                        (r, r.to_id)
                        for r in out_by_node[node]
                        if r.relation_type == step.relation
                    ]
                if step.direction in ("in", "both"):
                    edges += [
                        (r, r.from_id)
                        for r in in_by_node[node]
                        if r.relation_type == step.relation
                    ]
                for r, other in edges:
                    used_edges.add((r.from_id, r.to_id, r.relation_type))
                    cand_score = node_score * weight * r.confidence
                    if cand_score > nxt.get(other, 0.0):
                        nxt[other] = cand_score
                    if other not in matched_ids and cand_score > scores.get(
                        other, 0.0
                    ):
                        scores[other] = cand_score
            frontier = nxt

    # Бюджет контекста: matched первыми, остальные по убыванию score.
    ranked = sorted(
        scores.keys(),
        key=lambda nid: (nid in matched_ids, scores[nid]),
        reverse=True,
    )[: settings.graphrag_max_entities]

    rows = (
        await session.execute(select(Entity).where(Entity.id.in_(ranked)))
    ).scalars().all()
    by_id = {e.id: e for e in rows}
    ordered = [by_id[nid] for nid in ranked if nid in by_id]

    kept = set(ranked)
    edges = [
        (f, t, rt) for (f, t, rt) in used_edges if f in kept and t in kept
    ]
    return ordered, edges


async def _no_context(payload: QARequest) -> QAResponse:
    """Бейзлайн для экспериментов: LLM отвечает без какого-либо контекста."""
    answer_text = await llm.generate_text(
        prompts.qa_no_context_system(), payload.query
    )
    return QAResponse(
        answer=answer_text,
        sources=[],
        traversal_nodes=[],
        traversal_edges=[],
        mode="no_context",
    )


async def _vector_fallback(
    session: AsyncSession, payload: QARequest, query_vec: list[float]
) -> QAResponse:
    linked = await _link_entities(
        session, payload.book_id, query_vec, FALLBACK_TOP_K
    )
    if not linked:
        return QAResponse(
            answer="В учебнике это не рассматривается",
            sources=[],
            traversal_nodes=[],
            traversal_edges=[],
            mode="vector_fallback",
        )
    entities = [e for e, _ in linked]
    context = _format_context(entities, load_ontology())
    answer_text = await llm.generate_text(
        prompts.qa_system(context), payload.query
    )
    return QAResponse(
        answer=answer_text,
        sources=[
            QASource(id=e.id, name=e.name, entity_type=e.entity_type)
            for e in entities
        ],
        traversal_nodes=[e.id for e in entities],
        traversal_edges=[],
        mode="vector_fallback",
    )


def _format_context(entities: list[Entity], ontology: Ontology) -> str:
    """Группировка по типу; каждый блок — с атрибутами и цитатой."""
    by_type: dict[str, list[Entity]] = defaultdict(list)
    for e in entities:
        by_type[e.entity_type].append(e)

    sections: list[str] = []
    for etype, group in by_type.items():
        label = (
            ontology.entity_types[etype].label
            if etype in ontology.entity_types
            else etype
        )
        sections.append(f"## {label}")
        for e in group:
            block = [f"### {e.name}"]
            for key, val in (e.attrs or {}).items():
                if val in (None, "", [], {}):
                    continue
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                block.append(f"{key}: {val}")
            if e.source_quote:
                block.append(f"Цитата: «{e.source_quote}»")
            sections.append("\n".join(block))
    return "\n\n".join(sections)
