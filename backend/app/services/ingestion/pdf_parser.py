"""Шаг 1: парсинг PDF в главы.

pymupdf4llm сохраняет LaTeX-формулы. Текст разбивается по заголовкам H1/H2;
если структура не распознана — фиксированными чанками.
"""
import re

import pymupdf4llm

_HEADING_RE = re.compile(r"^(#{1,2})\s+(.+)$", re.MULTILINE)
# Грубая оценка: ~4 символа на токен
_CHARS_PER_CHUNK = 4000 * 4


def extract_chapters(pdf_path: str) -> list[dict]:
    """Возвращает список глав: [{"title", "order_num", "raw_text"}]."""
    md_text = pymupdf4llm.to_markdown(pdf_path)
    chapters = split_by_headings(md_text)
    if not chapters:
        chapters = _split_by_size(md_text)
    return chapters


def split_by_headings(md_text: str) -> list[dict]:
    """Разбивает Markdown по заголовкам H1/H2."""
    matches = list(_HEADING_RE.finditer(md_text))
    if not matches:
        return []

    chapters: list[dict] = []
    for idx, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(md_text)
        body = md_text[start:end].strip()
        if not body:
            continue
        chapters.append(
            {"title": title, "order_num": len(chapters), "raw_text": body}
        )
    return chapters


def _split_by_size(md_text: str) -> list[dict]:
    """Фолбэк: разбивка фиксированными чанками, если заголовков нет."""
    chunks = [
        md_text[i : i + _CHARS_PER_CHUNK]
        for i in range(0, len(md_text), _CHARS_PER_CHUNK)
    ]
    return [
        {"title": f"Часть {i + 1}", "order_num": i, "raw_text": chunk.strip()}
        for i, chunk in enumerate(chunks)
        if chunk.strip()
    ]
