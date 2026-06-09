"""Gemini API клиент (google-genai): генерация, retry, парсинг JSON.

Единая точка вызова LLM. Промпты сюда передаются извне (из app.prompts),
здесь — только транспорт, повторные попытки и разбор ответа.
"""
import json
import re
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Ленивая инициализация клиента — не падаем на импорте без ключа."""
    return genai.Client(api_key=settings.gemini_api_key)


# Снимает обёртку ```json ... ``` если модель её добавила
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class LLMError(Exception):
    """Ошибка вызова LLM или разбора ответа."""


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = _FENCE_RE.sub("", text)
    return text.strip()


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    reraise=True,
)
async def _generate(system: str, user: str, json_mode: bool) -> str:
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json" if json_mode else "text/plain",
    )
    response = await _get_client().aio.models.generate_content(
        model=settings.model,
        contents=user,
        config=config,
    )
    if not response.text:
        raise LLMError("Пустой ответ от LLM")
    return response.text


async def generate_text(system: str, user: str) -> str:
    """Свободный текстовый ответ (используется в QA)."""
    return await _generate(system, user, json_mode=False)


async def generate_json(system: str, user: str) -> dict[str, Any]:
    """JSON-ответ с разбором. Бросает LLMError при невалидном JSON."""
    raw = await _generate(system, user, json_mode=True)
    try:
        return json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise LLMError(f"Невалидный JSON от LLM: {exc}\n{raw[:500]}") from exc
