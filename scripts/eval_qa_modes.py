"""Сравнение режимов QA: graphrag vs vector vs none (без контекста).

Каждый вопрос прогоняется через все три режима; ответы опционально оценивает
LLM-судья (по эталону, если он задан). Результат — JSON с per-question данными
и сводная таблица по режимам. Для воспроизводимости включите LLM_CACHE_ENABLED.

Использование:
    python scripts/eval_qa_modes.py <book_id> questions.json [--judge] [--out results.json]

Формат questions.json:
    [
      {"query": "Что такое предел функции?",
       "reference": "эталонный ответ (опционально)"}
    ]
"""
import argparse
import asyncio
import json
import os
import statistics
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import async_session_maker  # noqa: E402
from app import prompts  # noqa: E402
from app.schemas.qa import QARequest  # noqa: E402
from app.services import llm, qa_service  # noqa: E402

MODES = ("graphrag", "vector", "none")


async def _run_one(book_id: uuid.UUID, query: str, mode: str) -> dict:
    async with async_session_maker() as session:
        started = time.perf_counter()
        resp = await qa_service.answer(
            session,
            QARequest(query=query, book_id=book_id, mode=mode),
        )
        latency = time.perf_counter() - started
    return {
        "forced_mode": mode,
        "actual_mode": resp.mode,
        "answer": resp.answer,
        "sources": [s.name for s in resp.sources],
        "traversal_nodes": len(resp.traversal_nodes),
        "traversal_edges": len(resp.traversal_edges),
        "latency_sec": round(latency, 2),
    }


async def _judge(query: str, answer: str, reference: str | None) -> dict:
    try:
        data = await llm.generate_json(
            prompts.judge_answer_system(),
            prompts.judge_answer_user(query, answer, reference),
        )
        return {
            "judge_score": int(data["score"]),
            "judge_explanation": data.get("explanation", ""),
        }
    except (llm.LLMError, KeyError, TypeError, ValueError) as exc:
        return {"judge_score": None, "judge_error": str(exc)}


async def evaluate(book_id: str, questions_path: str, judge: bool, out: str | None) -> None:
    with open(questions_path, encoding="utf-8") as f:
        questions = json.load(f)

    bid = uuid.UUID(book_id)
    results: list[dict] = []

    for i, q in enumerate(questions, 1):
        query = q["query"]
        reference = q.get("reference")
        row: dict = {"query": query, "reference": reference, "runs": []}
        for mode in MODES:
            run = await _run_one(bid, query, mode)
            if judge:
                run.update(await _judge(query, run["answer"], reference))
            row["runs"].append(run)
            print(f"[{i}/{len(questions)}] {mode:<8} "
                  f"actual={run['actual_mode']:<15} "
                  f"{run['latency_sec']}s"
                  + (f" score={run.get('judge_score')}" if judge else ""))
        results.append(row)

    _summary(results, judge)

    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nРезультаты сохранены: {out}")


def _summary(results: list[dict], judge: bool) -> None:
    print("\n=== Сводка по режимам ===")
    header = f"{'режим':<10} {'n':>3} {'latency':>8}"
    if judge:
        header += f" {'score':>6}"
    header += f" {'fallback%':>10}"
    print(header)

    for mode in MODES:
        runs = [r for row in results for r in row["runs"] if r["forced_mode"] == mode]
        if not runs:
            continue
        latencies = [r["latency_sec"] for r in runs]
        line = f"{mode:<10} {len(runs):>3} {statistics.mean(latencies):>7.2f}s"
        if judge:
            scores = [r["judge_score"] for r in runs if r.get("judge_score") is not None]
            line += f" {statistics.mean(scores):>6.2f}" if scores else f" {'—':>6}"
        fallbacks = sum(
            1 for r in runs if r["actual_mode"] != r["forced_mode"] and mode == "graphrag"
        )
        line += f" {100 * fallbacks / len(runs):>9.0f}%"
        print(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book_id")
    parser.add_argument("questions", help="путь к questions.json")
    parser.add_argument("--judge", action="store_true", help="оценка LLM-судьёй")
    parser.add_argument("--out", help="сохранить результаты в JSON")
    args = parser.parse_args()
    asyncio.run(evaluate(args.book_id, args.questions, args.judge, args.out))
