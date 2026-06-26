import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  FlaskConical,
  Plus,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSession } from "../../hooks/useSession";
import { listTests, deleteTest } from "../../api/tests";
import type { TestListItem } from "../../types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CreateTestDialog } from "./CreateTestDialog";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function TestsListPage() {
  const sessionId = useSession();
  const [tests, setTests] = useState<TestListItem[] | null>(null);
  const [error, setError] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

  const load = async () => {
    setError(false);
    try {
      setTests(await listTests(sessionId));
    } catch {
      setError(true);
    }
  };

  useEffect(() => {
    load();
  }, [sessionId]);

  const handleDelete = async (id: string) => {
    setTests((prev) => prev?.filter((t) => t.id !== id) ?? null);
    try {
      await deleteTest(id);
    } catch {
      load();
    }
  };

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Тесты</h1>
          <p className="text-sm text-muted-foreground">
            Полноценные тесты по графам знаний — от 1 до 100 вопросов.
          </p>
        </div>
        <Button className="gap-2" onClick={() => setCreateOpen(true)}>
          <Plus className="size-4" />
          Новый тест
        </Button>
      </div>

      {error ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
            <AlertCircle className="size-10 text-destructive" />
            <p className="font-medium">Не удалось загрузить тесты</p>
            <Button variant="outline" onClick={load}>
              Повторить
            </Button>
          </CardContent>
        </Card>
      ) : tests === null ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} aria-hidden>
              <CardContent className="space-y-4 p-5">
                <div className="h-5 w-2/3 animate-pulse rounded bg-muted" />
                <div className="h-3 w-1/3 animate-pulse rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : tests.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
            <span className="flex size-12 items-center justify-center rounded-xl bg-muted text-muted-foreground">
              <FlaskConical className="size-6" />
            </span>
            <div className="space-y-1">
              <p className="font-medium">Пока нет ни одного теста</p>
              <p className="text-sm text-muted-foreground">
                Создайте тест по любому готовому графу знаний.
              </p>
            </div>
            <Button className="gap-2" onClick={() => setCreateOpen(true)}>
              <Plus className="size-4" />
              Новый тест
            </Button>
          </CardContent>
        </Card>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tests.map((test) => (
            <li key={test.id}>
              <TestCard test={test} onDelete={() => handleDelete(test.id)} />
            </li>
          ))}
        </ul>
      )}

      <CreateTestDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        sessionId={sessionId}
        onCreated={(t) => setTests((prev) => [t, ...(prev ?? [])])}
      />
    </div>
  );
}

function TestCard({
  test,
  onDelete,
}: {
  test: TestListItem;
  onDelete: () => void;
}) {
  const completed = test.status === "completed";
  const pct = test.score != null ? Math.round(test.score * 100) : null;

  return (
    <Card className="group/card h-full transition-all hover:border-primary/40 hover:shadow-sm">
      <CardContent className="flex h-full flex-col gap-3 p-5">
        <div className="flex items-start justify-between gap-2">
          <h2 className="line-clamp-2 font-semibold leading-snug" title={test.title}>
            {test.title}
          </h2>
          <Button
            variant="ghost"
            size="icon"
            className="size-7 shrink-0 text-muted-foreground hover:text-destructive"
            onClick={onDelete}
            title="Удалить тест"
          >
            <Trash2 className="size-4" />
          </Button>
        </div>

        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <BookOpen className="size-3.5" />
          <span className="line-clamp-1">{test.book_title}</span>
        </p>

        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span>{test.question_count} вопр.</span>
          <span>·</span>
          <span>{formatDate(test.created_at)}</span>
        </div>

        <div className="mt-auto flex items-center justify-between pt-2">
          {completed && pct != null ? (
            <Badge
              variant={pct >= 70 ? "default" : "secondary"}
              className="gap-1"
            >
              <CheckCircle2 className="size-3" />
              {pct}%
            </Badge>
          ) : (
            <Badge variant="outline">Не пройден</Badge>
          )}
          <Link
            to={`/tests/${test.id}`}
            className={cn(
              "flex items-center gap-1 text-sm font-medium text-primary",
            )}
          >
            {completed ? "Результат" : "Пройти"}
            <ArrowRight className="size-4 transition-transform group-hover/card:translate-x-0.5" />
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
