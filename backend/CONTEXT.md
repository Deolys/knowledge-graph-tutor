# Backend Context

## Stack

- **Python 3.12**, FastAPI, async SQLAlchemy 2 (asyncpg driver)
- **PostgreSQL 16 + pgvector** — хранение графа, эмбеддингов, прогресса
- **Google Gemini** (`google-genai`) — LLM для извлечения понятий, генерации вопросов, QA
- **sentence-transformers** — многоязычные эмбеддинги (`paraphrase-multilingual-MiniLM-L12-v2`)
- **pymupdf4llm** — парсинг PDF с сохранением LaTeX-формул

## Структура `app/`

```
app/
├── main.py          # FastAPI app, CORS, логирование, подключение роутеров
├── config.py        # Все настройки через pydantic-settings (Settings singleton)
├── database.py      # async engine, async_session_maker, Base, get_session()
├── prompts.py       # ВСЕ LLM-промпты — только здесь, не в сервисах
│
├── models/          # SQLAlchemy ORM (UUID PK, server_default)
│   ├── book.py
│   ├── chapter.py   # status: pending | processing | done | error
│   ├── concept.py   # embedding: Vector(384), canonical_id для merge
│   ├── relation.py  # type: depends_on | part_of | example_of | related_to
│   ├── question.py  # options: JSONB, correct_idx скрыт в API
│   └── progress.py  # session_id (без авторизации), status, score, attempts
│
├── schemas/         # Pydantic request/response (не ORM)
│   ├── book.py      # BookOut, BookStatusOut, GraphOut (nodes + edges)
│   ├── concept.py   # ConceptOut, QuestionOut (без correct_idx)
│   ├── progress.py  # TestSubmit, TestResult (с unlocked), ProgressOut
│   └── qa.py        # QARequest, QAResponse (с sources)
│
├── api/             # Тонкие роутеры — только HTTP-слой
│   ├── books.py     # POST /upload, GET /{id}, GET /{id}/graph
│   ├── concepts.py  # GET /{id}, GET /{id}/questions
│   ├── progress.py  # POST /, GET /{session_id}
│   └── qa.py        # POST /
│
└── services/
    ├── llm.py           # Gemini-клиент (ленивый), retry на ServerError, JSON-парсер
    ├── embeddings.py    # sentence-transformers (ленивый), encode / encode_batch / cosine
    ├── test_service.py  # Генерация MCQ (ленивая, кэш в БД), проверка ответов
    ├── progress_service.py  # submit_test, каскадная логика learned
    ├── qa_service.py    # pgvector поиск → расширение по графу → LLM
    └── ingestion/
        ├── pipeline.py  # Единая точка входа — роутеры вызывают только его
        ├── pdf_parser.py    # pymupdf4llm → split by headings → fallback by size
        ├── extractor.py     # 2 LLM-вызова: понятия, затем связи
        ├── validator.py     # confidence >= 0.7, структурная валидация
        └── merger.py        # cosine similarity >= 0.85 → canonical concept
```

## Правила разработки

**Промпты** — все системные промпты живут только в `app/prompts.py`. В сервисах вызываются как `prompts.EXTRACT_CONCEPTS_SYSTEM` или `prompts.qa_system(context)`. Никогда не встраивать промпты в код сервисов.

**Ingestion** — роутеры вызывают только `pipeline.run_ingestion()`, никогда отдельные шаги (`extractor`, `merger` и т.д.). Это позволяет безопасно менять порядок шагов.

**Сессии БД** — фоновые задачи (`asyncio.create_task`) создают собственную сессию через `async_session_maker()`, а не используют сессию запроса (она закрывается до завершения задачи).

**LLM-клиент** — инициализируется лениво при первом вызове (`@lru_cache`), чтобы не падать на импорте без API-ключа. Аналогично для модели эмбеддингов.

**Ретрай LLM** — `tenacity` с `retry_if_exception_type(ServerError)`, 6 попыток, экспоненциальное ожидание 5–60s. Логирует предупреждение перед каждой паузой.

## REST API

| Метод | URL | Описание |
|---|---|---|
| `POST` | `/api/books/upload` | Загрузить PDF (multipart), запускает ingestion в фоне |
| `GET`  | `/api/books/{book_id}` | Статус обработки книги + список глав с прогрессом |
| `GET`  | `/api/books/{book_id}/graph` | Граф: узлы + рёбра. `?session_id=` добавляет статусы прогресса |
| `GET`  | `/api/concepts/{id}` | Детали понятия |
| `GET`  | `/api/concepts/{id}/questions` | Вопросы MCQ (генерируются лениво, кэшируются в БД) |
| `POST` | `/api/progress` | Отправить ответы на тест → `{score, status, unlocked[]}` |
| `GET`  | `/api/progress/{session_id}` | Весь прогресс сессии |
| `POST` | `/api/qa` | Вопрос → ответ по контексту графа + источники |
| `GET`  | `/health` | `{"status": "ok"}` |

## Модель данных

```
books ──< chapters ──< concepts >── relations (from_id → to_id)
                           │
                           └──< questions
                           └──< progress (session_id + concept_id)
```

**Concept.canonical_id** — ссылка на канонический узел после merge. Если `NULL` — сам узел канонический.

**Relation.type** — `depends_on | part_of | example_of | related_to`

**Progress.status** — `not_started | in_progress | learned`

## Каскадная логика "learned"

Узел становится `learned` когда:
1. `score >= LEARNED_SCORE_THRESHOLD` (по умолчанию `0.7`)
2. Все узлы, на которые указывает его `depends_on`-рёбро (`Relation.from_id = concept, type = depends_on`), тоже `learned`

После перехода узла в `learned` — BFS вверх по графу: все потомки, у которых уже достаточный `score`, могут разблокироваться. Список разблокированных возвращается в `TestResult.unlocked`.

## QA-сервис

1. Эмбеддинг запроса → pgvector cosine search, top-5 понятий книги
2. Расширение контекста: соседи глубины 1 (все рёбра входящие/исходящие от top-5)
3. Контекст форматируется как `### Название\nОпределение\nФормула` и передаётся в system-промпт
4. LLM отвечает строго по контексту (`prompts.qa_system(context)`)
5. В ответе — `sources[]` из исходных top-5 узлов

## Конфигурация (`app/config.py`)

| Переменная | Назначение | Дефолт |
|---|---|---|
| `GEMINI_API_KEY` | Ключ Gemini API | — |
| `MODEL` | Имя модели Gemini | `gemini-2.0-flash` |
| `DATABASE_URL` | asyncpg URL | `localhost:5432/kgtutor` |
| `CONFIDENCE_THRESHOLD` | Минимальный confidence связи | `0.7` |
| `MERGE_THRESHOLD` | Порог cosine для merge понятий | `0.85` |
| `EMBEDDINGS_MODEL` | Модель sentence-transformers | `paraphrase-multilingual-MiniLM-L12-v2` |
| `QUESTIONS_PER_CONCEPT` | MCQ-вопросов на понятие | `3` |
| `LEARNED_SCORE_THRESHOLD` | Порог score для "learned" | `0.7` |
