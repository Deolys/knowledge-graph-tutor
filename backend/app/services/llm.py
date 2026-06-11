"""LLM-клиент: httpx → OpenAI-совместимый endpoint (без SDK).

Единая точка вызова LLM. Промпты передаются извне (app.prompts / prompt_builder),
здесь — только транспорт, повторные попытки и разбор ответа. Сейчас за endpoint
стоит Gemini (OpenAI-compatible), позже можно подменить на Anthropic.
"""
import json
import logging
import re
from functools import lru_cache
from typing import Any

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = logging.getLogger(__name__)

# Снимает обёртку ```json ... ``` если модель её добавила
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class LLMError(Exception):
    """Ошибка вызова LLM или разбора ответа."""


class RetryableLLMError(LLMError):
    """Временная ошибка (5xx / 429 / сеть) — имеет смысл повторить."""


@lru_cache(maxsize=1)
def _client() -> httpx.AsyncClient:
    """Ленивый httpx-клиент с авторизацией Bearer и базовым URL."""
    return httpx.AsyncClient(
        base_url=settings.llm_base_url.rstrip("/"),
        headers={"Authorization": f"Bearer {settings.gemini_api_key}"},
        timeout=httpx.Timeout(120.0),
    )


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = _FENCE_RE.sub("", text)
    return text.strip()


@retry(
    retry=retry_if_exception_type(RetryableLLMError),
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _chat(
    system: str, user: str, *, model: str, json_mode: bool
) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        resp = await _client().post("/chat/completions", json=payload)
    except httpx.HTTPError as exc:
        raise RetryableLLMError(f"Сетевая ошибка LLM: {exc}") from exc

    if resp.status_code >= 500 or resp.status_code == 429:
        raise RetryableLLMError(
            f"LLM {resp.status_code}: {resp.text[:300]}"
        )
    if resp.status_code >= 400:
        raise LLMError(f"LLM {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LLMError(f"Неожиданный формат ответа LLM: {data}") from exc
    if not content:
        raise LLMError("Пустой ответ от LLM")
    return content


async def generate_text(
    system: str, user: str, *, model: str | None = None
) -> str:
    """Свободный текстовый ответ (используется в QA)."""
    return await _chat(
        system, user, model=model or settings.llm_model, json_mode=False
    )


async def generate_json(
    system: str, user: str, *, model: str | None = None
) -> dict[str, Any]:
    """JSON-ответ с разбором. Бросает LLMError при невалидном JSON."""
    raw = await _chat(
        system, user, model=model or settings.llm_model, json_mode=True
    )
    try:
        return json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise LLMError(f"Невалидный JSON от LLM: {exc}\n{raw[:500]}") from exc
