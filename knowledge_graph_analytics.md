# Knowledge Graph Tutor — Полная аналитика проекта
> Документ для генерации проекта и промптов с помощью ИИ.  
> Версия: 1.0 | Язык реализации: Python + TypeScript/React

---

## 1. Контекст и цель

### Что это
Веб-приложение для построения графа знаний из учебника (PDF) с последующим адаптивным тестированием студентов. LLM используется для извлечения понятий и связей. Граф хранится в PostgreSQL. Прогресс студента отображается визуально — усвоенные узлы меняют цвет.

### Зачем это нужно
- Традиционный учебник — линейная структура. Граф знаний — нелинейная, отражает реальные зависимости между понятиями.
- LLM без контекста галлюцинирует. Граф знаний из учебника даёт верифицированный контекст для ответов.
- Студент не видит какие понятия он не знает. Визуальный граф делает пробелы явными.

### Целевая аудитория
Студенты и преподаватели вузов. Первый прототип — для одного конкретного учебника (не универсальный загрузчик).

---

## 2. Функциональные требования

### MVP (обязательно)
- [ ] Загрузка PDF учебника через интерфейс
- [ ] Автоматическое извлечение глав из PDF
- [ ] Построение графа понятий по каждой главе через LLM
- [ ] Merge понятий между главами через эмбеддинги
- [ ] Визуализация графа с цветовым статусом узлов
- [ ] Генерация теста по выбранному узлу/главе
- [ ] Отметка узлов как усвоенных по результату теста (каскадная логика)
- [ ] QA-режим: вопрос → LLM отвечает на основе графа (без галлюцинаций)

### Второй приоритет
- [ ] Сравнение двух учебников (diff графов)
- [ ] Экспорт графа в JSON/CSV
- [ ] История попыток тестирования
- [ ] Межглавные связи с подтверждением пользователем

### За пределами MVP (упомянуть в диссертации как future work)
- [ ] Мультипользовательность и авторизация
- [ ] Поддержка произвольного PDF (не одного учебника)
- [ ] Мобильная версия
- [ ] Интеграция с LMS (Moodle, Canvas)

---

## 3. Архитектура системы

### Общая схема
```
[PDF Учебник]
      │
      ▼
[Ingestion Pipeline]  ←── Python, pymupdf4llm, google-genai
      │
      ├── Извлечение текста + LaTeX формул по главам
      ├── Вызов LLM: извлечение понятий (Вызов 1)
      ├── Вызов LLM: извлечение связей (Вызов 2)
      ├── Валидация и фильтрация по confidence
      └── Merge понятий между главами (sentence-transformers)
      │
      ▼
[PostgreSQL + pgvector]  ←── Docker
      │
      ▼
[FastAPI Backend]  ←── Python
      │
      ▼
[React Frontend]  ←── TypeScript, react-force-graph-2d
```

### Компоненты и ответственность

| Компонент | Технология | Ответственность |
|---|---|---|
| PDF Parser | pymupdf4llm | Извлечение текста + LaTeX из PDF |
| Ingestion Pipeline | google-genai (Gemini) | Построение графа из текста |
| Embeddings | sentence-transformers | Merge дублирующихся понятий |
| Storage | PostgreSQL + pgvector | Хранение графа, прогресса, вопросов |
| Backend API | FastAPI | REST API для фронтенда |
| Frontend | React + TypeScript | Визуализация графа, тест, QA |
| LLM | AI API | Извлечение, генерация вопросов, QA |

---

## 4. Модель данных (PostgreSQL)

### Таблицы

```sql
-- Загруженные учебники
CREATE TABLE books (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT NOT NULL,
    filename    TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Главы учебника
CREATE TABLE chapters (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id     UUID REFERENCES books(id),
    title       TEXT NOT NULL,
    order_num   INTEGER NOT NULL,
    raw_text    TEXT,
    status      TEXT DEFAULT 'pending' -- pending | processing | done | error
);

-- Понятия (узлы графа)
CREATE TABLE concepts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id     UUID REFERENCES books(id),
    chapter_id  UUID REFERENCES chapters(id),
    name        TEXT NOT NULL,
    definition  TEXT NOT NULL,
    formula     TEXT,           -- LaTeX формула если есть
    quote       TEXT,           -- цитата из текста
    embedding   vector(384),    -- для merge и векторного поиска
    canonical_id UUID,          -- ссылка на канонический узел после merge
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Связи между понятиями (рёбра графа)
CREATE TABLE relations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_id     UUID REFERENCES concepts(id),
    to_id       UUID REFERENCES concepts(id),
    type        TEXT NOT NULL,  -- depends_on | part_of | example_of | related_to
    confidence  FLOAT NOT NULL,
    is_cross_chapter BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Вопросы для тестирования
CREATE TABLE questions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id  UUID REFERENCES concepts(id),
    text        TEXT NOT NULL,
    options     JSONB NOT NULL,  -- ["вариант A", "вариант B", ...]
    correct_idx INTEGER NOT NULL,
    difficulty  TEXT DEFAULT 'medium' -- easy | medium | hard
);

-- Прогресс пользователя (без авторизации — session_id)
CREATE TABLE progress (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  TEXT NOT NULL,
    concept_id  UUID REFERENCES concepts(id),
    status      TEXT DEFAULT 'not_started', -- not_started | in_progress | learned
    score       FLOAT,          -- последний результат теста (0.0 - 1.0)
    attempts    INTEGER DEFAULT 0,
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- Индексы
CREATE INDEX ON concepts USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON progress (session_id, concept_id);
CREATE INDEX ON relations (from_id, to_id);
```

### Логика "усвоен" (каскадная)
Узел считается усвоенным если:
1. score >= 0.7 на тесте по данному узлу
2. ВСЕ узлы на которые указывает depends_on у данного узла тоже имеют status = 'learned'

```sql
-- Рекурсивный запрос: все предшественники узла
WITH RECURSIVE predecessors AS (
    SELECT from_id as concept_id
    FROM relations
    WHERE to_id = $concept_id AND type = 'depends_on'
    UNION ALL
    SELECT r.from_id
    FROM relations r
    JOIN predecessors p ON r.to_id = p.concept_id
    WHERE r.type = 'depends_on'
)
SELECT c.id, c.name, p.status
FROM predecessors pr
JOIN concepts c ON c.id = pr.concept_id
LEFT JOIN progress p ON p.concept_id = c.id AND p.session_id = $session_id;
```

---

## 5. Ingestion Pipeline — детальная логика

### Шаг 1: Парсинг PDF

```python
# Используем pymupdf4llm для сохранения LaTeX формул
import pymupdf4llm

def extract_chapters(pdf_path: str) -> list[dict]:
    """
    Возвращает список глав с текстом в Markdown формате.
    Формулы сохраняются как LaTeX: $формула$ или $$формула$$
    """
    md_text = pymupdf4llm.to_markdown(pdf_path)
    chapters = split_by_headings(md_text)  # см. ниже
    return chapters

def split_by_headings(md_text: str) -> list[dict]:
    """
    Разбивает Markdown по заголовкам H1/H2.
    Если структура не распознана — разбивает по фиксированному размеру чанков.
    """
    import re
    pattern = r'^#{1,2}\s+(.+)$'
    # ... логика разбивки
```

### Шаг 2: Извлечение понятий (Вызов 1 к LLM)

**System prompt:**
```
Ты — система извлечения знаний из учебных текстов.
Извлекай ключевые понятия из текста главы учебника.

ПРАВИЛА:
1. Извлекай ТОЛЬКО понятия которые явно определены в тексте
2. Не добавляй знания из своей памяти — только из предоставленного текста
3. name: минимальная каноническая форма термина (не "методы X", а "X")
4. definition: определение из текста, близкий пересказ или цитата
5. formula: LaTeX формула если есть в тексте, иначе не включай поле
6. quote: точная цитата из текста где впервые определяется понятие

ФОРМАТ ОТВЕТА — только валидный JSON без пояснений:
{
  "concepts": [
    {
      "name": "название понятия",
      "definition": "определение из текста",
      "formula": "LaTeX формула или null",
      "quote": "цитата из текста"
    }
  ]
}
```

**User prompt:**
```
Текст главы "{chapter_title}":

{chapter_text}
```

### Шаг 3: Извлечение связей (Вызов 2 к LLM)

**System prompt:**
```
Ты — система построения графа знаний.
Найди смысловые связи между понятиями на основе текста.

ТИПЫ СВЯЗЕЙ:
- depends_on   : понятие A невозможно понять без понятия B (A зависит от B)
- part_of      : A является частью, подвидом или разновидностью B
- example_of   : A является конкретным примером абстрактного B
- related_to   : A и B тесно связаны но тип связи не подходит под другие

ПРАВИЛА:
1. Используй ТОЛЬКО понятия из предоставленного списка
2. Не добавляй связи которых нет в тексте
3. confidence: твоя уверенность от 0.0 до 1.0 (только >= 0.7 будут сохранены)
4. Одна пара понятий — максимум одна связь
5. Связь не может быть с самим собой (from != to)

ФОРМАТ ОТВЕТА — только валидный JSON без пояснений:
{
  "relations": [
    {
      "from": "название понятия A",
      "to": "название понятия B",
      "type": "depends_on | part_of | example_of | related_to",
      "confidence": 0.85
    }
  ]
}
```

**User prompt:**
```
Список понятий из главы:
{concepts_json}

Текст главы:
{chapter_text}
```

### Шаг 4: Валидация

```python
def validate_concepts(raw: list[dict]) -> list[dict]:
    valid = []
    for c in raw:
        if not c.get("name") or not c.get("definition"):
            continue
        if len(c["name"]) < 2 or len(c["name"]) > 100:
            continue
        if len(c["definition"]) < 10:
            continue
        valid.append(c)
    return valid

def validate_relations(concepts: list[dict], relations: list[dict]) -> list[dict]:
    names = {c["name"].lower() for c in concepts}
    valid = []
    for r in relations:
        if r["confidence"] < 0.7:
            continue
        if r["from"].lower() not in names or r["to"].lower() not in names:
            continue  # галлюцинированная связь
        if r["from"] == r["to"]:
            continue
        valid.append(r)
    return valid
```

### Шаг 5: Merge понятий между главами

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Многоязычная модель — важно для русских учебников
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

MERGE_THRESHOLD = 0.85  # порог сходства для объединения

def merge_concepts(all_concepts: list[dict]) -> list[dict]:
    """
    Объединяет дублирующиеся понятия из разных глав.
    Возвращает список канонических понятий с canonical_id.
    """
    names = [c["name"] for c in all_concepts]
    embeddings = model.encode(names, normalize_embeddings=True)
    
    merged_groups = []
    visited = set()
    
    for i in range(len(all_concepts)):
        if i in visited:
            continue
        group = [i]
        for j in range(i + 1, len(all_concepts)):
            if j in visited:
                continue
            sim = float(np.dot(embeddings[i], embeddings[j]))
            if sim >= MERGE_THRESHOLD:
                group.append(j)
                visited.add(j)
        visited.add(i)
        merged_groups.append(group)
    
    result = []
    for group in merged_groups:
        # Канонический — с самым длинным определением
        canonical_idx = max(group, key=lambda i: len(all_concepts[i]["definition"]))
        canonical = all_concepts[canonical_idx].copy()
        canonical["aliases"] = [all_concepts[i]["name"] for i in group if i != canonical_idx]
        result.append(canonical)
    
    return result
```

---

## 6. Backend API (FastAPI)

### Эндпоинты

```
POST   /api/books/upload          Загрузить PDF
GET    /api/books/{book_id}       Статус обработки книги
GET    /api/books/{book_id}/graph Получить граф (узлы + рёбра)
GET    /api/chapters/{id}/status  Статус обработки главы

GET    /api/concepts/{id}         Детали понятия
GET    /api/concepts/{id}/questions  Вопросы для теста

POST   /api/progress              Обновить прогресс после теста
GET    /api/progress/{session_id} Весь прогресс сессии

POST   /api/qa                    QA-запрос с контекстом из графа
```

### QA endpoint — логика

```python
@router.post("/qa")
async def answer_question(query: str, book_id: str, session_id: str):
    # 1. Найти релевантные узлы через векторный поиск
    query_embedding = model.encode(query)
    relevant_concepts = await db.search_concepts(
        book_id=book_id,
        embedding=query_embedding,
        top_k=5
    )
    
    # 2. Расширить контекст через граф (соседние узлы)
    context_concepts = await db.get_neighborhood(
        concept_ids=[c.id for c in relevant_concepts],
        depth=1
    )
    
    # 3. Сформировать контекст для LLM
    context = format_context(context_concepts)
    
    # 4. Вызов LLM с контекстом
    answer = await llm.answer_with_context(
        query=query,
        context=context
    )
    
    return {"answer": answer, "sources": relevant_concepts}
```

### System prompt для QA

```
Ты — образовательный ассистент.
Отвечай на вопросы студентов ТОЛЬКО на основе предоставленного контекста из учебника.

ПРАВИЛА:
1. Используй ТОЛЬКО информацию из блока КОНТЕКСТ
2. Если ответа нет в контексте — скажи "В данной главе это не рассматривается"
3. При наличии формул — включай их в ответ в LaTeX формате
4. Ссылайся на понятия из контекста по их точным названиям
5. Не добавляй информацию из своей памяти

КОНТЕКСТ ИЗ УЧЕБНИКА:
{context}
```

---

## 7. Frontend — экраны и компоненты

### Экран 1: Граф знаний (главный)

**Компонент:** `GraphView.tsx`

**Библиотека:** `react-force-graph-2d`

**Состояния узлов и цвета:**
```typescript
type ConceptStatus = 'not_started' | 'in_progress' | 'learned' | 'locked'

const NODE_COLORS: Record<ConceptStatus, string> = {
  not_started: '#94a3b8',  // серый
  in_progress: '#3b82f6',  // синий
  learned:     '#22c55e',  // зелёный
  locked:      '#e2e8f0',  // светло-серый (зависимости не выполнены)
}
```

**Взаимодействие:**
- Клик на узел → боковая панель с определением + кнопка "Пройти тест"
- Hover → tooltip с кратким определением
- Клик на ребро → тип связи
- Кнопка "Фильтр по главе" → показывает только узлы выбранной главы

### Экран 2: Тест

**Компонент:** `TestView.tsx`

**Логика:**
```typescript
interface TestSession {
  concept_id: string
  questions: Question[]
  current_index: number
  answers: number[]
  completed: boolean
}

// После завершения теста
const handleTestComplete = async (session: TestSession) => {
  const score = calculateScore(session)
  await updateProgress(concept_id, score)
  
  if (score >= 0.7) {
    await checkCascadeUnlock(concept_id, session_id)
    // Обновить статусы зависимых узлов
  }
}
```

### Экран 3: QA-чат

**Компонент:** `QAChat.tsx`

Простой чат-интерфейс. Рядом с ответом — список источников (узлов графа), на которые опирался ответ. Клик на источник — переход в GraphView с выделенным узлом.

---

## 8. Генерация вопросов

### System prompt для генерации вопросов

```
Ты — создатель образовательных тестов.
Создай {n} вопросов для проверки знания понятия из учебника.

ПОНЯТИЕ:
Название: {concept_name}
Определение: {concept_definition}
{formula_block}
Цитата из учебника: {quote}

ПРАВИЛА:
1. Вопросы должны проверять ПОНИМАНИЕ, а не запоминание формулировок
2. Каждый вопрос — 4 варианта ответа, один правильный
3. Неправильные варианты должны быть правдоподобными, не очевидными
4. Сложность: easy (определение), medium (применение), hard (связи с другими понятиями)
5. Не используй в вопросе точные слова из определения

ФОРМАТ — только валидный JSON:
{
  "questions": [
    {
      "text": "текст вопроса",
      "options": ["вариант A", "вариант B", "вариант C", "вариант D"],
      "correct_idx": 0,
      "difficulty": "easy | medium | hard"
    }
  ]
}
```

---

## 9. Структура проекта

```
knowledge-graph-tutor/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py               # env vars, settings
│   │   ├── database.py             # PostgreSQL connection, pgvector
│   │   ├── models/
│   │   │   ├── book.py
│   │   │   ├── concept.py
│   │   │   ├── relation.py
│   │   │   ├── question.py
│   │   │   └── progress.py
│   │   ├── api/
│   │   │   ├── books.py
│   │   │   ├── concepts.py
│   │   │   ├── progress.py
│   │   │   └── qa.py
│   │   └── services/
│   │       ├── ingestion/
│   │       │   ├── pdf_parser.py   # pymupdf4llm, chapter splitting
│   │       │   ├── extractor.py    # LLM calls: concepts + relations
│   │       │   ├── validator.py    # validation + confidence filter
│   │       │   └── merger.py       # embeddings-based concept merge
│   │       ├── qa_service.py       # vector search + LLM answer
│   │       └── test_service.py     # question generation
│   ├── migrations/
│   │   └── 001_initial.sql
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── GraphView/
│   │   │   │   ├── GraphView.tsx
│   │   │   │   ├── NodePanel.tsx   # боковая панель узла
│   │   │   │   └── GraphControls.tsx
│   │   │   ├── TestView/
│   │   │   │   ├── TestView.tsx
│   │   │   │   └── QuestionCard.tsx
│   │   │   └── QAChat/
│   │   │       ├── QAChat.tsx
│   │   │       └── SourceList.tsx
│   │   ├── hooks/
│   │   │   ├── useGraph.ts
│   │   │   ├── useProgress.ts
│   │   │   └── useSession.ts
│   │   ├── api/
│   │   │   └── client.ts           # axios + типы
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 10. Docker Compose

```yaml
version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: kgtutor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./backend/migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/kgtutor
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      MODEL: ${MODEL}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    volumes:
      - ./uploads:/app/uploads

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  pgdata:
```

---

## 11. Переменные окружения (.env.example)

```bash
# LLM
GEMINI_API_KEY=...
MODEL=...

# Database
POSTGRES_PASSWORD=your_password

# Ingestion
CONFIDENCE_THRESHOLD=0.7          # минимальный confidence для связей
MERGE_THRESHOLD=0.85               # порог сходства для merge понятий
EMBEDDINGS_MODEL=paraphrase-multilingual-MiniLM-L12-v2
MAX_CHAPTER_TOKENS=4000            # максимум токенов на главу для LLM

# Test generation
QUESTIONS_PER_CONCEPT=3
LEARNED_SCORE_THRESHOLD=0.7        # минимальный score для статуса "learned"
```

---

## 12. Экспериментальный раздел диссертации

### Измерение 1: Качество графа (NLP метрики)

**Процедура:**
1. Взять одну главу учебника
2. Вручную составить эталонный список понятий и связей
3. Запустить ingestion pipeline
4. Сравнить результат с эталоном

**Метрики:**
```
Precision = TP / (TP + FP)   — сколько извлечённых понятий корректны
Recall    = TP / (TP + FN)   — сколько реальных понятий найдено
F1        = 2 * P * R / (P + R)
```

**Сравниваемые конфигурации:**
- Zero-shot промпт (без примеров)
- Few-shot промпт (2 примера из того же учебника)
- Zero-shot + валидация по confidence 0.7
- Few-shot + валидация по confidence 0.7

### Измерение 2: Качество QA без галлюцинаций

**Процедура:**
1. Составить 20 вопросов по учебнику с эталонными ответами
2. Получить ответы от LLM в двух режимах:
   - Обычный режим (без контекста из графа)
   - Режим с контекстом из графа (KG-RAG)
3. Оценить ответы по критериям

**Метрики:**
```
Factual accuracy  — соответствие эталонному ответу (0/1)
Hallucination rate — доля ответов с информацией не из учебника
```

### Измерение 3: Пользовательское тестирование

**Процедура:**
1. 2 группы по 5 студентов, одна тема
2. Группа А — изучает тему по учебнику обычно
3. Группа Б — изучает тему через граф + тест в приложении
4. Обе группы проходят одинаковый финальный тест

**Метрики:**
- Средний балл финального теста
- Субъективная оценка удобства (SUS-анкета, 10 вопросов)
- Время до достижения порога "усвоено"

---

## 13. Ограничения и риски

| Риск | Вероятность | Митигация |
|---|---|---|
| Плохое качество PDF парсинга | Средняя | Зафиксировать один учебник, проверить вручную до старта |
| LLM добавляет понятия не из текста | Высокая | Валидация по confidence + правило "только из текста" в промпте |
| Дублирующиеся понятия после merge | Средняя | Ручная проверка после merge, порог 0.85 |
| Формулы не распознаются pymupdf4llm | Низкая | Fallback: страница как изображение через Vision |
| Сроки: пайплайн займёт больше времени | Средняя | MVP без автогенерации вопросов — вопросы предгенерируются |

---

## 14. Промпт для генерации проекта ИИ-агентом

```
Создай полноценный проект knowledge-graph-tutor согласно следующей спецификации.

КОНТЕКСТ: Веб-приложение для построения графа знаний из учебника (PDF) 
с адаптивным тестированием. Студент загружает PDF, система строит граф 
понятий через LLM, студент изучает темы и проходит тесты, усвоенные узлы 
отмечаются на графе.

СТЕК:
- Backend: Python 3.12, FastAPI, SQLAlchemy async, asyncpg
- LLM: Gemini AI API (gemini-2.0-flash)
- Embeddings: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- PDF: pymupdf4llm (сохраняет LaTeX формулы)
- Storage: PostgreSQL 16 + pgvector extension
- Frontend: React 19 + TypeScript + Vite
- Visualization: react-force-graph-2d
- Infrastructure: Docker Compose

СТРУКТУРА ПРОЕКТА: [вставить раздел 9]

МОДЕЛЬ ДАННЫХ: [вставить раздел 4]

INGESTION PIPELINE: [вставить раздел 5]

API ENDPOINTS: [вставить раздел 6]

FRONTEND ЭКРАНЫ: [вставить раздел 7]

ТРЕБОВАНИЯ К КОДУ:
1. Полный рабочий код, не заглушки
2. Async/await везде в backend
3. TypeScript strict mode во frontend
4. Обработка ошибок на каждом шаге ingestion
5. Логирование через structlog
6. Все промпты вынести в отдельный файл prompts.py
7. Все пороговые значения — через переменные окружения
8. docker-compose.yml поднимает весь стек одной командой

НАЧНИ С: docker-compose.yml → migrations/001_initial.sql → 
backend/app/services/ingestion/ → backend/app/api/ → frontend/src/
```
