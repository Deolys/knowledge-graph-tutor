"""Gemini API клиент (google-genai): генерация, retry, парсинг JSON.

Единая точка вызова LLM. Промпты сюда передаются извне (из app.prompts),
здесь — только транспорт, повторные попытки и разбор ответа.
"""
import json
import logging
import re
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = logging.getLogger(__name__)


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


def _is_retryable(exc: BaseException) -> bool:
    """503 (перегрузка) и 429 (rate limit) — ретраим. Остальное — нет."""
    if isinstance(exc, genai_errors.ServerError):
        return True
    if isinstance(exc, genai_errors.ClientError) and "429" in str(exc):
        return True
    return False


@retry(
    retry=retry_if_exception_type(genai_errors.ServerError),
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    before_sleep=before_sleep_log(logger, logging.WARNING),
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
