"""Сервис эмбеддингов: sentence-transformers для merge и векторного поиска.

Многоязычная модель (важно для русских учебников). Модель грузится лениво
при первом вызове, чтобы не замедлять импорт и старт приложения.
"""
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(settings.embeddings_model)


def encode(text: str) -> list[float]:
    """Эмбеддинг одного текста."""
    vec = _model().encode(text, normalize_embeddings=True)
    return vec.tolist()


def encode_batch(texts: list[str]) -> list[list[float]]:
    """Эмбеддинги списка текстов (батч — быстрее, чем по одному)."""
    if not texts:
        return []
    vecs = _model().encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Косинусная близость двух нормализованных векторов."""
    va, vb = np.asarray(a), np.asarray(b)
    return float(np.dot(va, vb))
