"""Шаги 2-3: извлечение понятий и связей через LLM (два отдельных вызова).

Намеренно два вызова на главу, а не один большой — так модель точнее
и проще отлаживать каждый шаг. Промпты берутся из app.prompts.
"""
import json

from app import prompts
from app.services import llm


async def extract_concepts(chapter_title: str, chapter_text: str) -> list[dict]:
    """Вызов 1: понятия из текста главы."""
    data = await llm.generate_json(
        prompts.EXTRACT_CONCEPTS_SYSTEM,
        prompts.extract_concepts_user(chapter_title, chapter_text),
    )
    return data.get("concepts", [])


async def extract_relations(
    concepts: list[dict], chapter_text: str
) -> list[dict]:
    """Вызов 2: связи между уже извлечёнными понятиями."""
    if len(concepts) < 2:
        return []
    concepts_json = json.dumps(
        [{"name": c["name"]} for c in concepts], ensure_ascii=False
    )
    data = await llm.generate_json(
        prompts.EXTRACT_RELATIONS_SYSTEM,
        prompts.extract_relations_user(concepts_json, chapter_text),
    )
    return data.get("relations", [])
