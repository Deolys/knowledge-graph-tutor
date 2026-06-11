# Knowledge Graph Tutor

Веб-приложение, которое строит граф знаний из PDF-учебника с помощью LLM
(Google Gemini), а затем даёт адаптивное тестирование и QA по графу.

- Студент загружает PDF-учебник.
- Система извлекает понятия и связи по главам, объединяет дубли через эмбеддинги.
- Граф визуализируется; усвоенные узлы меняют цвет (каскадная логика).
- Тесты по узлам и QA-режим с ответами строго по контексту графа.

Подробная аналитика — в [knowledge_graph_analytics.md](knowledge_graph_analytics.md),
структура — в [ARCHITECTURE.md](ARCHITECTURE.md), гайд для Claude Code — в
[CLAUDE.md](CLAUDE.md).

## Стек

- **Backend:** Python 3.12, FastAPI, async SQLAlchemy, PostgreSQL 16 + pgvector
- **LLM:** Google Gemini (`google-genai`)
- **Эмбеддинги:** sentence-transformers (multilingual)
- **PDF:** pymupdf4llm (сохраняет LaTeX-формулы)
- **Frontend:** React 19 + TypeScript + Vite, react-force-graph-2d, Zustand

## Запуск

1. Скопируйте `.env.example` в `.env` и заполните `GEMINI_API_KEY`, `MODEL`,
   `POSTGRES_PASSWORD`.
   ```bash
   cp .env.example .env
   ```
2. Поднимите весь стек:

   ```bash
   docker-compose up -d
   ```

Логи (backend):
   ```bash
   docker-compose logs -f backend
   ```
Пересобрать:
   ```bash
   docker-compose up -d --build backend 2>&1 | tail -4
   ```
3. Примените миграции (один раз):

   ```bash
   docker-compose exec backend alembic upgrade head
   ```

- Backend: http://localhost:8000 (Swagger: `/docs`)
- Frontend: http://localhost:3000

## Локальная разработка

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Скрипты для эксперимента (диссертация)

```bash
# Загрузить учебник в БД (синхронный прогон пайплайна)
python scripts/seed_test_book.py path/to/book.pdf "Название"

# Оценить качество графа против эталона (precision/recall/F1)
python scripts/eval_graph_quality.py <book_id> path/to/gold.json
```
