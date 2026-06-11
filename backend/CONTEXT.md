# Backend Context (v2 — ontology-driven)

## Stack

- **Python 3.12**, FastAPI, async SQLAlchemy 2 (asyncpg driver)
- **PostgreSQL 16 + pgvector** — типизированный граф, эмбеддинги, прогресс
- **LLM** — httpx → OpenAI-совместимый endpoint (без SDK). Сейчас за ним Gemini.
- **sentence-transformers** — многоязычные эмбеддинги (`paraphrase-multilingual-MiniLM-L12-v2`)
- **pymupdf4llm** — парсинг PDF с сохранением LaTeX-формул
- **PyYAML** — загрузка онтологии

## Главный принцип: онтология — это данные, а не код

Классы сущностей и типы отношений описаны в `app/ontology/ontology.yaml`.
Промпты извлечения генерируются динамически из активного профиля, валидация
читает схему из онтологии. Добавление нового класса = строка в YAML +
`python scripts/sync_ontology.py`, ноль изменений в коде.

## Структура `app/`

```
app/
├── main.py          # FastAPI app, CORS, роутеры
├── config.py        # pydantic-settings (LLM_*, пороги, GraphRAG)
├── database.py      # async engine, async_session_maker, Base, get_session()
├── prompts.py       # СТАТИЧЕСКИЕ промпты: классификация вопроса, QA, генерация тестов
│
├── ontology/
│   ├── ontology.yaml             # источник правды о типах
│   ├── traversal_templates.yaml  # шаблоны обхода для GraphRAG
│   └── loader.py                 # Pydantic Ontology/Profile/Relation, lru_cache
│
├── models/          # SQLAlchemy ORM
│   ├── ontology.py  # EntityTypeRow, RelationTypeRow, ProfileRow (отражение YAML)
│   ├── book.py      # + profile (FK profiles)
│   ├── chapter.py   # status: pending|processing|done|error
│   ├── entity.py    # типизированный узел: entity_type, attrs JSONB, source_quote, embedding
│   ├── relation.py  # типизированное ребро: relation_type, source_quote, UNIQUE(from,to,type)
│   ├── question.py  # entity_id, options JSONB
│   └── progress.py  # session_id, entity_id, status (+locked)
│
├── schemas/         # Pydantic request/response
│   ├── ontology.py  # OntologyOut, ProfileOut — для UI
│   ├── book.py      # BookOut(+profile), типизированные GraphNode/GraphEdge
│   ├── entity.py    # EntityOut (attrs), QuestionOut (без correct_idx)
│   ├── progress.py  # TestSubmit/TestResult/ProgressOut (entity_id)
│   └── qa.py        # QAResponse (+traversal_nodes/edges, mode)
│
├── api/             # тонкие роутеры
│   ├── ontology.py  # GET /api/ontology, /api/ontology/profiles
│   ├── books.py     # upload(+profile), list, status, graph (типизированный)
│   ├── entities.py  # GET /{id}, GET /{id}/questions
│   ├── progress.py  # POST /, GET /{session_id}
│   └── qa.py        # POST /
│
└── services/
    ├── llm.py            # httpx OpenAI-compatible, retry на 5xx/429, JSON-парсер
    ├── embeddings.py     # sentence-transformers (ленивый)
    ├── graphrag.py       # классификация вопроса → entity linking → обход → контекст
    ├── qa_service.py     # тонкая обёртка над graphrag
    ├── test_service.py   # генерация MCQ по сущности (entity_id)
    ├── progress_service.py  # каскад learned по транзитивному REQUIRES
    └── ingestion/
        ├── pipeline.py        # единая точка входа; читает profile книги
        ├── pdf_parser.py      # pymupdf4llm → split by headings
        ├── prompt_builder.py  # промпты извлечения ИЗ онтологии
        ├── extractor.py       # 2 LLM-вызова: сущности, затем отношения
        ├── validator.py       # онтологическая валидация + quote_in_text
        └── merger.py          # merge ТОЛЬКО внутри одного entity_type
```

## Правила разработки

**Онтология** — единственный источник правды о типах. Меняется YAML → меняется
поведение без правок кода. Новый класс/отношение: правка YAML + `sync_ontology.py`.

**Промпты** — статические в `app/prompts.py`, динамические (извлечение) генерируются
в `prompt_builder.py` из активного профиля. Не хардкодить списки типов в сервисах.

**Ingestion** — роутеры вызывают только `pipeline.run_ingestion()`.

**Merge** — никогда не мержить сущности разных типов, даже при сходстве 0.99.

**Сессии БД** — фоновые задачи создают свою сессию через `async_session_maker()`.

**LLM-клиент** — httpx, ленивый (`@lru_cache`), Bearer-авторизация, retry (tenacity)
на 5xx/429/сетевые ошибки.

## REST API

| Метод | URL | Описание |
|---|---|---|
| `GET`  | `/api/ontology` | Активная онтология (типы, цвета, профили) |
| `GET`  | `/api/ontology/profiles` | Список профилей |
| `POST` | `/api/books/upload` | PDF (multipart) + `profile`, ingestion в фоне |
| `GET`  | `/api/books/{id}` | Статус обработки + главы |
| `GET`  | `/api/books/{id}/graph` | Типизированный граф; `?session_id=` добавляет статусы |
| `GET`  | `/api/entities/{id}` | Детали сущности (attrs) |
| `GET`  | `/api/entities/{id}/questions` | MCQ (ленивая генерация, кэш в БД) |
| `POST` | `/api/progress` | Тест → `{score, status, unlocked[]}` |
| `GET`  | `/api/progress/{session_id}` | Прогресс сессии |
| `POST` | `/api/qa` | Вопрос → ответ + `traversal_nodes/edges` + `mode` |
| `GET`  | `/health` | `{"status": "ok"}` |

## Модель данных

```
entity_types ─┐   relation_types ─┐   profiles ─┐
              │ (FK)              │ (FK)         │ (FK)
books(profile) ──< chapters ──< entities >── relations (from_id → to_id, типизированы)
                                    │
                                    └──< questions
                                    └──< progress (session_id + entity_id)
```

- **Entity.attrs** — JSONB по схеме класса (definition, latex, steps, …)
- **Entity.source_quote** — цитата из текста (обязательна при извлечении)
- **Relation.relation_type** — из онтологии; `source_quote` обязателен
- **Progress.status** — `not_started | in_progress | learned | locked`

## Каскадная логика "learned"

Узел `learned` ⇔ `score >= LEARNED_SCORE_THRESHOLD` И все его пререквизиты
(сущности, на которые он указывает связью `REQUIRES`) тоже `learned`. После
перехода в learned — переоценка прямых зависимых вверх по графу REQUIRES;
список разблокированных в `TestResult.unlocked`.

## GraphRAG (services/graphrag.py)

1. Классификация типа вопроса (дешёвая модель) → шаблон из `traversal_templates.yaml`
2. Entity linking: эмбеддинг вопроса → top-3 сущности книги (порог `ENTITY_LINK_THRESHOLD`)
3. Типизированный BFS по шаблону; ранжирование `traversal_weight × confidence`,
   бюджет `GRAPHRAG_MAX_ENTITIES`
4. Сборка контекста (группировка по типам, цитаты) → LLM-ответ строго из контекста
5. Fallback: если привязка < порога — векторный top-5 без обхода, `mode=vector_fallback`
6. Ответ содержит `traversal_nodes/edges` для подсветки на графе

## Порядок первого запуска

```bash
alembic upgrade head            # схема (включая таблицы онтологии)
python scripts/sync_ontology.py # YAML → БД (до ingestion: entities FK → entity_types)
```
