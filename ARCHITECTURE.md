# Архитектура (v2 — ontology-driven)

> Онтология — единственный источник правды о типах сущностей и отношений
> (`backend/app/ontology/ontology.yaml`). Промпты, валидация и обход графа
> читают её; добавление класса = строка в YAML + `scripts/sync_ontology.py`.

```
knowledge-graph-tutor/
│
├── docker-compose.yml
├── .env.example
├── README.md
├── CLAUDE.md
├── knowledge_graph_analytics.md       # спецификация v2
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt               # httpx (LLM), pyyaml, pgvector, …
│   ├── CONTEXT.md                     # детальный контекст backend
│   ├── alembic/
│   │   └── versions/001_initial.py    # схема v2 (онтология + типизированный граф)
│   │
│   └── app/
│       ├── main.py                    # FastAPI app, роутеры
│       ├── config.py                  # pydantic-settings (LLM_*, GraphRAG, пороги)
│       ├── database.py                # async engine, session factory
│       ├── prompts.py                 # СТАТИЧЕСКИЕ промпты (классификация, QA, тесты)
│       │
│       ├── ontology/
│       │   ├── ontology.yaml          # типы сущностей/отношений, профили
│       │   ├── traversal_templates.yaml  # шаблоны обхода для GraphRAG
│       │   └── loader.py              # Pydantic Ontology/Profile/Relation (lru_cache)
│       │
│       ├── models/
│       │   ├── ontology.py            # EntityTypeRow, RelationTypeRow, ProfileRow
│       │   ├── book.py                # + profile (FK)
│       │   ├── chapter.py
│       │   ├── entity.py              # типизированный узел (entity_type, attrs, embedding)
│       │   ├── relation.py            # типизированное ребро (relation_type, source_quote)
│       │   ├── question.py            # entity_id
│       │   └── progress.py            # entity_id, status (+locked)
│       │
│       ├── schemas/
│       │   ├── ontology.py            # OntologyOut, ProfileOut
│       │   ├── book.py                # BookOut(+profile), типизированный граф
│       │   ├── entity.py              # EntityOut (attrs), QuestionOut
│       │   ├── progress.py            # TestSubmit/Result/ProgressOut (entity_id)
│       │   └── qa.py                  # QAResponse (+traversal, mode)
│       │
│       ├── api/
│       │   ├── ontology.py            # GET /api/ontology(/profiles)
│       │   ├── books.py               # upload(+profile), list, status, graph
│       │   ├── entities.py            # GET /{id}, /{id}/questions
│       │   ├── progress.py            # POST /, GET /{session_id}
│       │   └── qa.py                  # POST /
│       │
│       └── services/
│           ├── llm.py                 # httpx OpenAI-compatible, retry, JSON-парсер
│           ├── embeddings.py          # sentence-transformers
│           ├── graphrag.py            # классификация → linking → обход → контекст
│           ├── qa_service.py          # обёртка над graphrag
│           ├── test_service.py        # генерация MCQ по сущности
│           ├── progress_service.py    # каскад learned по транзитивному REQUIRES
│           └── ingestion/
│               ├── pipeline.py        # единая точка входа; читает profile книги
│               ├── pdf_parser.py
│               ├── prompt_builder.py  # промпты извлечения ИЗ онтологии
│               ├── extractor.py       # 2 LLM-вызова (сущности, отношения)
│               ├── validator.py       # онтологическая валидация + quote_in_text
│               ├── merger.py          # merge только внутри одного entity_type
│               └── cycle_breaker.py   # транзитивные отношения → DAG
│
├── frontend/                          # React 19 + TS + Vite + Tailwind + shadcn
│   └── src/
│       ├── types/index.ts             # Ontology, Entity, типизированный Graph, QA
│       ├── api/                       # ontology, books, entities, progress, qa
│       ├── store/                     # ontologyStore, graphStore, progressStore, …
│       ├── hooks/                     # useOntology, useGraph, useProgress, useTest
│       └── components/
│           ├── graph/                 # GraphView (цвета/легенда/фильтры/кольца),
│           │                          # GraphFilters, NodePanel (+KaTeX)
│           ├── qa/QAChat.tsx          # GraphRAG-чат, подсветка traversal, KaTeX
│           ├── test/TestView.tsx
│           └── upload/UploadView.tsx  # выбор профиля + загрузка
│
└── scripts/
    ├── sync_ontology.py               # YAML → таблицы онтологии
    ├── seed_test_book.py              # загрузка книги (с профилем)
    ├── eval_graph_quality.py          # precision/recall/F1 по типам
    ├── eval_qa_modes.py               # сравнение режимов QA (+LLM-судья)
    └── check_graph_cycles.py          # циклы REQUIRES/PART_OF у книги [--fix]
```

## Порядок первого запуска

```bash
alembic upgrade head            # схема (включая пустые таблицы онтологии)
python scripts/sync_ontology.py # YAML → БД (ДО ingestion: entities FK → entity_types)
```

## Ключевые потоки

- **Ingestion:** PDF → главы → типизированное извлечение (промпт из профиля) →
  онтологическая валидация (+ проверка цитат) → merge внутри типа →
  разрыв циклов в транзитивных отношениях (DAG) → запись.
- **GraphRAG:** вопрос → классификация → entity linking → BFS по шаблону
  с затуханием скора вдоль пути (`score(узла) = score(родителя) ×
  traversal_weight × confidence`) → контекст → LLM-ответ + `traversal_path`.
  Fallback на векторный поиск при низкой привязке.
- **Прогресс:** узел `learned` ⇔ `score ≥ порог` И все `REQUIRES`-пререквизиты
  усвоены; каскадная разблокировка зависимых.
