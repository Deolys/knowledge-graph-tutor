# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Knowledge Graph Tutor** — a web application that builds knowledge graphs from PDF textbooks using LLMs, then enables adaptive testing and Q&A. Thesis project for KFU (Kazan Federal University).

Core flow: PDF upload → chapter extraction → LLM concept/relation extraction → embedding-based merge → PostgreSQL graph storage → React visualization + testing + Q&A.

## Commands

Once implemented, the standard commands will be:

```bash
# Full stack (recommended for development)
docker-compose up -d

# Backend only
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend only
cd frontend
npm install
npm run dev        # starts Vite dev server
npm run build      # production build
npm run lint       # ESLint

# Database migrations
cd backend
alembic upgrade head
alembic revision --autogenerate -m "description"

# Utility scripts
python scripts/seed_test_book.py     # load test textbook into DB
python scripts/eval_graph_quality.py # measure graph precision/recall
```

## Environment Variables

Required in `.env` (see `.env.example`):

```
GEMINI_API_KEY=...
MODEL=...
POSTGRES_PASSWORD=...
CONFIDENCE_THRESHOLD=0.7
MERGE_THRESHOLD=0.85
EMBEDDINGS_MODEL=paraphrase-multilingual-MiniLM-L12-v2
MAX_CHAPTER_TOKENS=4000
QUESTIONS_PER_CONCEPT=3
LEARNED_SCORE_THRESHOLD=0.7
```

## Architecture

### Backend (`backend/app/`)

**Entry points:**
- `main.py` — FastAPI app, CORS, router registration
- `config.py` — pydantic-settings loading all env vars
- `database.py` — async SQLAlchemy engine + session factory (asyncpg driver)
- `prompts.py` — **all LLM system prompts centralized here**; iterate prompts without touching service code

**API layer** (`api/`): thin routers — `books.py` (upload/status/graph), `concepts.py`, `progress.py`, `qa.py`

**Services:**
- `services/llm.py` — Gemini API client (google-genai) with retry logic and JSON parsing
- `services/embeddings.py` — sentence-transformers encode/search
- `services/qa_service.py` — vector search → context expansion via graph neighborhood → LLM answer
- `services/test_service.py` — MCQ question generation and answer checking
- `services/progress_service.py` — cascade "learned" logic (see below)
- `services/ingestion/pipeline.py` — **single orchestration entry point** for the full ingestion flow; routers call only this, not individual steps

**Ingestion pipeline steps** (`services/ingestion/`):
1. `pdf_parser.py` — pymupdf4llm, splits by chapter headings, preserves LaTeX formulas
2. `extractor.py` — two separate LLM calls per chapter: Call 1 extracts concepts, Call 2 extracts relations
3. `validator.py` — filters relations by `confidence >= 0.7`
4. `merger.py` — deduplicates concepts across chapters using embedding similarity `>= 0.85`

### Frontend (`frontend/src/`)

**State:** Zustand stores in `store/graphStore.ts` and `store/progressStore.ts`

**API layer** (`api/`): axios instance in `client.ts`, separate modules per domain

**Key hooks:** `useGraph.ts`, `useProgress.ts`, `useTest.ts`, `useSession.ts` (session_id in localStorage — no auth in MVP)

**Main views:**
- `components/upload/` — drag-and-drop PDF upload + chapter processing status polling
- `components/graph/GraphView.tsx` — react-force-graph-2d visualization, node color = progress status
- `components/test/` — MCQ test flow per concept/chapter
- `components/qa/QAChat.tsx` — chat interface, shows source concepts from graph

### Database (PostgreSQL 16 + pgvector)

Tables: `books`, `chapters` (status: pending|processing|done|error), `concepts` (embedding: vector(384), canonical_id for merged dupes), `relations` (type: depends_on|part_of|example_of|related_to), `questions` (options: JSONB), `progress` (status: not_started|in_progress|learned)

### Cascade Learning Logic

A concept is marked `learned` when: `score >= 0.7` AND all concepts with `depends_on` relations pointing TO this concept have `status = 'learned'`. Implemented in `progress_service.py`.

## Key Design Decisions

- **No auth in MVP** — `session_id` stored in localStorage identifies a student session
- **Centralized prompts** — all LLM prompts live in `prompts.py`; never embed prompts in service files
- **Two-call extraction** — concepts and relations extracted in separate LLM calls per chapter (not one large call)
- **Multilingual embeddings** — `paraphrase-multilingual-MiniLM-L12-v2` supports Russian-language textbooks
- **pipeline.py as single entry point** — API routers never call individual ingestion steps directly, only `pipeline.py`; this makes step reordering/replacement safe
- **pgvector for QA** — concept embeddings stored in PostgreSQL enable vector search without a separate vector DB
