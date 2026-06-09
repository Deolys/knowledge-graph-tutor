"""FastAPI-приложение: CORS, регистрация роутеров, health-check."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import books, concepts, progress, qa

app = FastAPI(title="Knowledge Graph Tutor", version="0.1.0")

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


app.include_router(books.router)
app.include_router(concepts.router)
app.include_router(progress.router)
app.include_router(qa.router)
