"""Роутер книг: upload, статус обработки, граф."""
import logging
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

logger = logging.getLogger(__name__)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_maker, get_session
from app.models import Book, Chapter, Concept, Progress, Relation
from app.schemas.book import (
    BookListItem,
    BookOut,
    BookStatusOut,
    ChapterStatusOut,
    GraphEdge,
    GraphNode,
    GraphOut,
)
from app.services.ingestion import pipeline

router = APIRouter(prefix="/api/books", tags=["books"])


async def _run_ingestion_bg(book_id: uuid.UUID, pdf_path: str) -> None:
    """Фоновая задача: своя сессия, т.к. запросная уже закрыта."""
    logger.info("Ingestion started: book_id=%s pdf=%s", book_id, pdf_path)
    try:
        async with async_session_maker() as session:
            await pipeline.run_ingestion(session, book_id, pdf_path)
        logger.info("Ingestion done: book_id=%s", book_id)
    except Exception:
        logger.exception("Ingestion FAILED: book_id=%s", book_id)


@router.post("/upload", response_model=BookOut)
async def upload_book(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> Book:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Ожидается PDF-файл")

    os.makedirs(settings.upload_dir, exist_ok=True)
    book = Book(title=file.filename.rsplit(".", 1)[0], filename=file.filename)
    session.add(book)
    await session.flush()

    dest = os.path.join(settings.upload_dir, f"{book.id}.pdf")
    with open(dest, "wb") as f:
        f.write(await file.read())
    await session.commit()

    # Ingestion запускается отдельной фоновой задачей с собственной сессией.
    import asyncio

    asyncio.create_task(_run_ingestion_bg(book.id, dest))
    return book


@router.get("", response_model=list[BookListItem])
async def list_books(
    session: AsyncSession = Depends(get_session),
) -> list[BookListItem]:
    """Список всех книг с агрегатом обработки — для страницы выбора графа."""
    books = (
        await session.execute(select(Book).order_by(Book.created_at.desc()))
    ).scalars().all()
    if not books:
        return []

    book_ids = [b.id for b in books]

    # Агрегаты по главам: всего и по статусам — одним запросом на каждую группу.
    ch_rows = (
        await session.execute(
            select(Chapter.book_id, Chapter.status, func.count())
            .where(Chapter.book_id.in_(book_ids))
            .group_by(Chapter.book_id, Chapter.status)
        )
    ).all()
    total_by_book: dict[uuid.UUID, int] = {}
    done_by_book: dict[uuid.UUID, int] = {}
    error_by_book: dict[uuid.UUID, int] = {}
    for bid, st, cnt in ch_rows:
        total_by_book[bid] = total_by_book.get(bid, 0) + cnt
        if st == "done":
            done_by_book[bid] = done_by_book.get(bid, 0) + cnt
        elif st == "error":
            error_by_book[bid] = error_by_book.get(bid, 0) + cnt

    concept_rows = (
        await session.execute(
            select(Concept.book_id, func.count())
            .where(Concept.book_id.in_(book_ids))
            .group_by(Concept.book_id)
        )
    ).all()
    concepts_by_book = {bid: cnt for bid, cnt in concept_rows}

    items: list[BookListItem] = []
    for b in books:
        total = total_by_book.get(b.id, 0)
        done = done_by_book.get(b.id, 0)
        errors = error_by_book.get(b.id, 0)
        if total > 0 and done + errors >= total:
            status = "error" if errors and done == 0 else "done"
        else:
            status = "processing"
        items.append(
            BookListItem(
                id=b.id,
                title=b.title,
                filename=b.filename,
                created_at=b.created_at,
                chapters_total=total,
                chapters_done=done,
                concepts_count=concepts_by_book.get(b.id, 0),
                status=status,
            )
        )
    return items


@router.get("/{book_id}", response_model=BookStatusOut)
async def book_status(
    book_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> BookStatusOut:
    book = await session.get(Book, book_id)
    if not book:
        raise HTTPException(404, "Книга не найдена")

    rows = (
        await session.execute(
            select(Chapter)
            .where(Chapter.book_id == book_id)
            .order_by(Chapter.order_num)
        )
    ).scalars().all()
    chapters = [ChapterStatusOut.model_validate(c) for c in rows]
    done = bool(chapters) and all(
        c.status in ("done", "error") for c in chapters
    )
    return BookStatusOut(
        id=book.id, title=book.title, chapters=chapters, done=done
    )


@router.get("/{book_id}/graph", response_model=GraphOut)
async def book_graph(
    book_id: uuid.UUID,
    session_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> GraphOut:
    concepts = (
        await session.execute(
            select(Concept).where(Concept.book_id == book_id)
        )
    ).scalars().all()
    concept_ids = [c.id for c in concepts]

    # Статусы прогресса для сессии (если передана)
    status_by_concept: dict[uuid.UUID, str] = {}
    if session_id and concept_ids:
        prog = (
            await session.execute(
                select(Progress).where(
                    Progress.session_id == session_id,
                    Progress.concept_id.in_(concept_ids),
                )
            )
        ).scalars().all()
        status_by_concept = {p.concept_id: p.status for p in prog}

    nodes = [
        GraphNode(
            id=c.id,
            name=c.name,
            chapter_id=c.chapter_id,
            status=status_by_concept.get(c.id, "not_started"),
        )
        for c in concepts
    ]

    if concept_ids:
        relations = (
            await session.execute(
                select(Relation).where(
                    Relation.from_id.in_(concept_ids),
                    Relation.to_id.in_(concept_ids),
                )
            )
        ).scalars().all()
    else:
        relations = []

    edges = [
        GraphEdge(
            source=r.from_id,
            target=r.to_id,
            type=r.type,
            confidence=r.confidence,
        )
        for r in relations
    ]
    return GraphOut(nodes=nodes, edges=edges)
