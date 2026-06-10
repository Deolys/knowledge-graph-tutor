import { useEffect } from "react";
import { useTest } from "../../hooks/useTest";
import { useProgressStore } from "../../store/progressStore";

interface Props {
  conceptId: string;
  sessionId: string;
  onDone: () => void;
}

/** Экран теста по понятию: вопросы, отправка, результат с каскадом. */
export function TestView({ conceptId, sessionId, onDone }: Props) {
  const { questions, loading, answers, result, answer, submit } = useTest(
    conceptId,
    sessionId,
  );
  const setStatus = useProgressStore((s) => s.setStatus);

  useEffect(() => {
    if (!result) return;
    setStatus(result.concept_id, result.status);
    for (const id of result.unlocked) setStatus(id, "learned");
  }, [result, setStatus]);

  if (loading) return <p>Генерация вопросов…</p>;
  if (questions.length === 0) return <p>Вопросы недоступны.</p>;

  if (result) {
    return (
      <div>
        <h4>Результат: {Math.round(result.score * 100)}%</h4>
        <p>
          Статус:{" "}
          {result.status === "learned" ? "усвоено ✅" : "в процессе"}
        </p>
        {result.unlocked.length > 0 && (
          <p>Разблокировано узлов: {result.unlocked.length}</p>
        )}
        <button onClick={onDone}>Назад</button>
      </div>
    );
  }

  const allAnswered = questions.every((q) => answers[q.id] !== undefined);

  return (
    <div>
      {questions.map((q, i) => (
        <div key={q.id} style={{ marginBottom: 16 }}>
          <p>
            <b>
              {i + 1}. {q.text}
            </b>
          </p>
          {q.options.map((opt, idx) => (
            <label key={idx} style={{ display: "block" }}>
              <input
                type="radio"
                name={q.id}
                checked={answers[q.id] === idx}
                onChange={() => answer(q.id, idx)}
              />{" "}
              {opt}
            </label>
          ))}
        </div>
      ))}
      <button disabled={!allAnswered} onClick={() => submit()}>
        Завершить тест
      </button>
    </div>
  );
}
