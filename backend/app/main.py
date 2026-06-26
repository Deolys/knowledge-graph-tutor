"""FastAPI-приложение: CORS, регистрация роутеров, health-check."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from app.api import books, entities, ontology, progress, qa, tests
from app.ontology.sync import sync_on_startup


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Авто-синхронизация онтологии в БД (FK entities → entity_types).
    await sync_on_startup()
    yield


app = FastAPI(title="Knowledge Graph Tutor", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(ontology.router)
app.include_router(books.router)
app.include_router(entities.router)
app.include_router(progress.router)
app.include_router(qa.router)
app.include_router(tests.router)
