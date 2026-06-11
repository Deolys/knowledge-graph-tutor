"""Шаг 1: парсинг PDF в главы.

pymupdf4llm сохраняет LaTeX-формулы. Текст разбивается по заголовкам H1/H2;
если структура не распознана — фиксированными чанками.
Для старых PDF с CP1251-шрифтами применяется побайтовое перекодирование.
"""
import re

import fitz
import pymupdf4llm

_HEADING_RE = re.compile(r"^(#{1,2})\s+(.+)$", re.MULTILINE)
_CHARS_PER_CHUNK = 4000 * 4

_GARBLED_RE = re.compile(r"[À-ÿ]{4,}")


def _is_garbled(text: str) -> bool:
    """True если текст содержит латинские символы в диапазоне CP1251-кириллицы."""
    matches = _GARBLED_RE.findall(text)
    garbled_chars = sum(len(m) for m in matches)
    return garbled_chars > max(20, len(text) * 0.1)


def _decode_cp1251_pdf(pdf_path: str) -> str:
    """Побайтовое перекодирование символов 0x80-0xFF через CP1251."""
    doc = fitz.open(pdf_path)
    pages_text: list[str] = []
    for page in doc:
        d = page.get_text("rawdict")
        page_parts: list[str] = []
        for block in d.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                line_parts: list[str] = []
                for span in line["spans"]:
                    span_text = ""
                    for c in span.get("chars", []):
                        code = ord(c["c"])
                        if 0x80 <= code <= 0xFF:
                            try:
                                span_text += bytes([code]).decode("cp1251")
                            except (UnicodeDecodeError, ValueError):
                                span_text += c["c"]
                        else:
                            span_text += c["c"]
                    line_parts.append(span_text)
                page_parts.append(" ".join(line_parts))
        pages_text.append("\n".join(page_parts))
    return "\n\n".join(pages_text)


def extract_chapters(pdf_path: str) -> list[dict]:
    """Возвращает список глав: [{"title", "order_num", "raw_text"}]."""
    md_text = pymupdf4llm.to_markdown(pdf_path)

    if _is_garbled(md_text):
        md_text = _decode_cp1251_pdf(pdf_path)

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
