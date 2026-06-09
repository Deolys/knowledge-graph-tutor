```
knowledge-graph-tutor/
│
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial.py
│   │
│   └── app/
│       ├── main.py                  # FastAPI app, CORS, routers
│       ├── config.py                # pydantic-settings, все env vars
│       ├── database.py              # async engine, session factory
│       ├── prompts.py               # ВСЕ LLM промпты в одном месте
│       │
│       ├── models/                  # SQLAlchemy ORM модели
│       │   ├── __init__.py
│       │   ├── book.py
│       │   ├── chapter.py
│       │   ├── concept.py
│       │   ├── relation.py
│       │   ├── question.py
│       │   └── progress.py
│       │
│       ├── schemas/                 # Pydantic схемы (request/response)
│       │   ├── __init__.py
│       │   ├── book.py
│       │   ├── concept.py
│       │   ├── question.py
│       │   └── progress.py
│       │
│       ├── api/                     # FastAPI роутеры
│       │   ├── __init__.py
│       │   ├── books.py             # upload, status, graph
│       │   ├── concepts.py          # concept detail, questions
│       │   ├── progress.py          # update + get progress
│       │   └── qa.py                # QA endpoint
│       │
│       └── services/
│           ├── llm.py               # AI API клиент, retry, JSON parsing
│           ├── embeddings.py        # sentence-transformers, encode/search
│           ├── qa_service.py        # vector search + context + LLM answer
│           ├── test_service.py      # генерация вопросов, проверка теста
│           ├── progress_service.py  # каскадная логика "усвоен"
│           │
│           └── ingestion/
│               ├── __init__.py
│               ├── pipeline.py      # оркестратор: запускает все шаги
│               ├── pdf_parser.py    # pymupdf4llm, split by headings
│               ├── extractor.py     # вызовы LLM: понятия + связи
│               ├── validator.py     # валидация, confidence filter
│               └── merger.py        # merge дублей через эмбеддинги
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       │
│       ├── types/
│       │   └── index.ts             # все TypeScript типы
│       │
│       ├── api/
│       │   ├── client.ts            # axios instance, base URL
│       │   ├── books.ts
│       │   ├── concepts.ts
│       │   ├── progress.ts
│       │   └── qa.ts
│       │
│       ├── hooks/
│       │   ├── useGraph.ts          # загрузка и стейт графа
│       │   ├── useProgress.ts       # прогресс, обновление статусов
│       │   ├── useTest.ts           # логика теста, score, cascade
│       │   └── useSession.ts        # session_id в localStorage
│       │
│       ├── store/                   # Zustand стейт
│       │   ├── graphStore.ts
│       │   └── progressStore.ts
│       │
│       └── components/
│           │
│           ├── layout/
│           │   ├── Layout.tsx
│           │   └── Sidebar.tsx
│           │
│           ├── upload/
│           │   ├── UploadView.tsx   # drag-and-drop загрузка PDF
│           │   └── ProcessingStatus.tsx  # прогресс ingestion по главам
│           │
│           ├── graph/
│           │   ├── GraphView.tsx    # react-force-graph-2d, основной экран
│           │   ├── NodePanel.tsx    # боковая панель: определение + кнопки
│           │   ├── GraphLegend.tsx  # цвета статусов
│           │   ├── ChapterFilter.tsx
│           │   └── GraphControls.tsx  # zoom, reset, фильтры
│           │
│           ├── test/
│           │   ├── TestView.tsx     # экран теста
│           │   ├── QuestionCard.tsx # один вопрос + варианты
│           │   ├── TestResult.tsx   # итог теста + анимация unlock
│           │   └── ProgressBar.tsx
│           │
│           └── qa/
│               ├── QAChat.tsx       # чат-интерфейс
│               ├── MessageBubble.tsx
│               └── SourceList.tsx   # источники из графа
│
├── shared/                          # общие типы если нужна синхронизация
│   └── types.ts                     # (опционально, для monorepo tooling)
│
└── scripts/
    ├── seed_test_book.py            # загрузить тестовый учебник в БД
    └── eval_graph_quality.py        # скрипт для измерения precision/recall
```

---

Три вещи на которые обрати внимание:

**`prompts.py` в одном файле** — все системные промпты централизованы, легко итерировать без поиска по кодовой базе.

**`scripts/`** — два скрипта которые нужны для экспериментального раздела диссертации: seed для загрузки тестового учебника и eval для измерения качества графа.

**`services/ingestion/pipeline.py`** — единая точка входа для всего пайплайна. Роутер вызывает только его, не отдельные шаги. Так проще заменить или переставить шаги не трогая API.