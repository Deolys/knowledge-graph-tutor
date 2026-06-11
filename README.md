# Knowledge Graph Tutor (v2 — ontology-driven)

Веб-приложение, которое строит **типизированный** граф знаний из PDF-учебника
с помощью LLM, а затем даёт адаптивное тестирование и GraphRAG-ответы по графу.

- Студент выбирает профиль дисциплины и загружает PDF-учебник.
- Система извлекает типизированные сущности и отношения по активной онтологии,
  объединяет дубли через эмбеддинги (строго внутри типа).
- Граф визуализируется: цвет узла — тип сущности (из онтологии), кольцо —
  статус усвоения (каскадная логика по транзитивному `REQUIRES`).
- Тесты по узлам и GraphRAG-режим с ответами строго по контексту графа и
  подсветкой использованного пути обхода.

**Онтология — это данные, а не код:** классы и отношения описаны в
[`backend/app/ontology/ontology.yaml`](backend/app/ontology/ontology.yaml).
Добавление класса = строка в YAML + `python scripts/sync_ontology.py`.

Подробная аналитика — в [knowledge_graph_analytics.md](knowledge_graph_analytics.md),
структура backend — в [backend/CONTEXT.md](backend/CONTEXT.md).

## Стек

- **Backend:** Python 3.12, FastAPI, async SQLAlchemy, PostgreSQL 16 + pgvector
- **LLM:** httpx → OpenAI-совместимый endpoint (без SDK; сейчас за ним Gemini)
- **Онтология:** YAML → Pydantic; синхронизация в БД скриптом
- **Эмбеддинги:** sentence-transformers (multilingual)
- **PDF:** pymupdf4llm (сохраняет LaTeX-формулы)
- **Frontend:** React 19 + TypeScript + Vite, react-force-graph-2d, KaTeX, Zustand

## Запуск

1. Скопируйте `.env.example` в `.env` и заполните `GEMINI_API_KEY`, `LLM_MODEL`,
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
3. Примените миграции и перезапустите backend (один раз):

   ```bash
   docker-compose exec backend alembic upgrade head
   docker-compose restart backend
   ```
   Онтология синхронизируется в БД автоматически при старте backend
   (таблица `entities` ссылается на `entity_types` по внешнему ключу).
   Локально (без Docker) можно вместо этого выполнить
   `python scripts/sync_ontology.py`.

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
# Синхронизировать онтологию из YAML в БД (после правок ontology.yaml)
python scripts/sync_ontology.py

# Загрузить учебник в БД (синхронный прогон пайплайна; profile опционален)
python scripts/seed_test_book.py path/to/book.pdf "Название" math

# Оценить качество графа против эталона (precision/recall/F1 по типам)
python scripts/eval_graph_quality.py <book_id> path/to/gold.json
```
