import { useEffect } from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, ChevronLeft } from "lucide-react";
import { useTest } from "../../hooks/useTest";
import { useProgressStore } from "../../store/progressStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface Props {
  conceptId: string;
  sessionId: string;
  onDone: () => void;
}

export function TestView({ conceptId, sessionId, onDone }: Props) {
  const { questions, loading, answers, result, answer, submit } = useTest(conceptId, sessionId);
  const setStatus = useProgressStore((s) => s.setStatus);

  useEffect(() => {
    if (!result) return;
    setStatus(result.concept_id, result.status);
    for (const id of result.unlocked) setStatus(id, "learned");
  }, [result, setStatus]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground text-sm py-4">
        <div className="size-4 rounded-full border-2 border-muted-foreground border-t-transparent animate-spin" />
        Генерация вопросов…
      </div>
    );
  }

  if (questions.length === 0) {
    return <p className="text-sm text-muted-foreground py-4">Вопросы недоступны.</p>;
  }

  if (result) {
    const pct = Math.round(result.score * 100);
    const learned = result.status === "learned";
    return (
      <div className="space-y-4">
        <div className="text-center space-y-2 py-2">
          <CheckCircle2 className={cn("size-10 mx-auto", learned ? "text-green-500" : "text-muted-foreground")} />
          <p className="text-2xl font-bold">{pct}%</p>
          <Badge variant={learned ? "default" : "secondary"}>
            {learned ? "Усвоено ✓" : "В процессе"}
          </Badge>
          {result.unlocked.length > 0 && (
            <p className="text-xs text-muted-foreground">
              Разблокировано узлов: {result.unlocked.length}
            </p>
          )}
        </div>
        <Button variant="outline" className="w-full gap-2" onClick={onDone}>
          <ChevronLeft className="size-4" />
          Назад
        </Button>
      </div>
    );
  }

  const answeredCount = Object.keys(answers).length;
  const allAnswered = answeredCount === questions.length;
  const progressPct = Math.round((answeredCount / questions.length) * 100);

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{answeredCount} из {questions.length}</span>
          <span>{progressPct}%</span>
        </div>
        <Progress value={progressPct} className="h-1.5" />
      </div>

      {questions.map((q, i) => (
        <div key={q.id} className="space-y-2">
          <p className="text-sm font-medium leading-snug">
            {i + 1}. {q.text}
          </p>
          <div className="space-y-1">
            {q.options.map((opt, idx) => {
              const checked = answers[q.id] === idx;
              return (
                <label
                  key={idx}
                  className={cn(
                    "flex items-start gap-2 rounded-md border px-3 py-2 text-sm cursor-pointer transition-colors",
                    checked ? "border-primary bg-primary/5" : "border-border hover:bg-accent",
                  )}
                >
                  <input
                    type="radio"
                    name={q.id}
                    checked={checked}
                    onChange={() => answer(q.id, idx)}
                    className="mt-0.5 accent-primary shrink-0"
                  />
                  {opt}
                </label>
              );
            })}
          </div>
        </div>
      ))}

      <Button
        className="w-full"
        disabled={!allAnswered}
        onClick={() => submit()}
      >
        Завершить тест
      </Button>
    </div>
  );
}
