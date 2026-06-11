"""Извлечение типизированных сущностей и отношений (два LLM-вызова на главу).

Промпты собираются динамически из активного профиля онтологии
(prompt_builder), а не хардкодятся. Намеренно два вызова на главу.
"""
import json

from app.ontology import Profile
from app.services import llm
from app.services.ingestion import prompt_builder


async def extract_entities(
    profile: Profile, chapter_title: str, chapter_text: str
) -> list[dict]:
    """Вызов 1: типизированные сущности из текста главы."""
    data = await llm.generate_json(
        prompt_builder.build_entity_extraction_prompt(profile),
        prompt_builder.entity_extraction_user(chapter_title, chapter_text),
    )
    return data.get("entities", [])


async def extract_relations(
    profile: Profile, entities: list[dict], chapter_text: str
) -> list[dict]:
    """Вызов 2: типизированные отношения между извлечёнными сущностями."""
    if len(entities) < 2:
        return []
    entities_json = json.dumps(
        [
            {"entity_type": e.get("entity_type"), "name": e.get("name")}
            for e in entities
        ],
        ensure_ascii=False,
    )
    data = await llm.generate_json(
        prompt_builder.build_relation_extraction_prompt(profile),
        prompt_builder.relation_extraction_user(entities_json, chapter_text),
    )
    return data.get("relations", [])
