import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  BookOpen,
  Check,
  CheckCircle2,
  Loader2,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getTest, submitTest } from "../../api/tests";
import type { TestDetail } from "../../types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const DIFFICULTY_LABELS: Record<string, string> = {
  easy: "Лёгкий",
  medium: "Средний",
  hard: "Сложный",
};

export function GraphTestPage() {
  const { testId } = useParams<{ testId: string }>();
  const [test, setTest] = useState<TestDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!testId) return;
    getTest(testId)
      .then(setTest)
      .catch(() => setNotFound(true));
  }, [testId]);

  const completed = test?.status === "completed";

  const answeredCount = Object.keys(answers).length;
  const allAnswered = useMemo(
    () => !!test && answeredCount === test.questions.length,
    [test, answeredCount],
  );

  const submit = async () => {
    if (!testId || !test) return;
    setSubmitting(true);
    try {
      const result = await submitTest(testId, answers);
      setTest({ ...test, status: "completed", score: result.score, questions: result.questions });
    } finally {
      setSubmitting(false);
    }
  };

  if (notFound) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-16 text-center">
        <p className="font-medium">Тест не найден</p>
        <Button asChild variant="outline" className="mt-4 gap-2">
          <Link to="/tests">
            <ArrowLeft className="size-4" />К списку тестов
          </Link>
        </Button>
      </div>
    );
  }

  if (!test) {
    return (
      <div className="flex flex-1 items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="mr-2 size-5 animate-spin" />
        Загрузка теста…
      </div>
    );
  }

  const scorePct = test.score != null ? Math.round(test.score * 100) : 0;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
      <Button asChild variant="ghost" size="sm" className="mb-4 gap-2 -ml-2">
        <Link to="/tests">
          <ArrowLeft className="size-4" />К списку тестов
        </Link>
      </Button>

      <div className="mb-6 space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">{test.title}</h1>
        <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <BookOpen className="size-4" />
          {test.book_title}
          <span>·</span>
          {test.question_count} вопросов
        </p>
      </div>

      {completed && (
        <Card className="mb-6 border-primary/30">
          <CardContent className="flex items-center gap-4 p-5">
            <CheckCircle2
              className={cn(
                "size-10 shrink-0",
                scorePct >= 70 ? "text-green-500" : "text-muted-foreground",
              )}
            />
            <div>
              <p className="text-2xl font-bold">{scorePct}%</p>
              <p className="text-sm text-muted-foreground">
                Тест пройден. Правильные ответы отмечены ниже.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {!completed && (
        <div className="mb-6 space-y-1">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>
              {answeredCount} из {test.questions.length}
            </span>
            <span>
              {Math.round((answeredCount / test.questions.length) * 100)}%
            </span>
          </div>
          <Progress
            value={(answeredCount / test.questions.length) * 100}
            className="h-1.5"
          />
        </div>
      )}

      <ol className="space-y-6">
        {test.questions.map((q, i) => (
          <li key={q.id} className="space-y-3">
            <div className="flex items-start gap-2">
              <span className="font-semibold text-muted-foreground">
                {i + 1}.
              </span>
              <div className="flex-1 space-y-1">
                <p className="font-medium leading-snug">{q.text}</p>
                <div className="flex flex-wrap items-center gap-2">
                  {q.entity_name && (
                    <Badge variant="secondary" className="font-normal">
                      {q.entity_name}
                    </Badge>
                  )}
                  <span className="text-xs text-muted-foreground">
                    {DIFFICULTY_LABELS[q.difficulty] ?? q.difficulty}
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-1.5 pl-6">
              {q.options.map((opt, idx) => {
                const selected = completed
                  ? q.selected_idx === idx
                  : answers[q.id] === idx;
                const isCorrect = completed && q.correct_idx === idx;
                const isWrongPick =
                  completed && q.selected_idx === idx && q.correct_idx !== idx;

                return (
                  <label
                    key={idx}
                    className={cn(
                      "flex items-start gap-2 rounded-md border px-3 py-2 text-sm transition-colors",
                      completed
                        ? "cursor-default"
                        : "cursor-pointer hover:bg-accent",
                      isCorrect && "border-green-500 bg-green-500/10",
                      isWrongPick && "border-destructive bg-destructive/10",
                      !completed && selected && "border-primary bg-primary/5",
                      !completed &&
                        !selected &&
                        "border-border",
                      completed &&
                        !isCorrect &&
                        !isWrongPick &&
                        "border-border",
                    )}
                  >
                    {!completed && (
                      <input
                        type="radio"
                        name={q.id}
                        checked={selected}
                        onChange={() =>
                          setAnswers((a) => ({ ...a, [q.id]: idx }))
                        }
                        className="mt-0.5 accent-primary shrink-0"
                      />
                    )}
                    <span className="flex-1">{opt}</span>
                    {isCorrect && (
                      <Check className="mt-0.5 size-4 shrink-0 text-green-600" />
                    )}
                    {isWrongPick && (
                      <X className="mt-0.5 size-4 shrink-0 text-destructive" />
                    )}
                  </label>
                );
              })}
            </div>
          </li>
        ))}
      </ol>

      {!completed && (
        <div className="mt-8">
          <Button
            className="w-full gap-2"
            disabled={!allAnswered || submitting}
            onClick={submit}
          >
            {submitting && <Loader2 className="size-4 animate-spin" />}
            {submitting ? "Проверка…" : "Завершить тест"}
          </Button>
          {!allAnswered && (
            <p className="mt-2 text-center text-xs text-muted-foreground">
              Ответьте на все вопросы, чтобы завершить.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
