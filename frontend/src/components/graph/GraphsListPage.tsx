import { useEffect, useState, type MouseEvent } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Coins,
  Loader2,
  Network,
  RefreshCw,
  Trash2,
  Upload,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { listBooks, deleteBook } from "../../api/books";
import type { BookListItem } from "../../types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const STATUS_CONFIG = {
  processing: { label: "Обработка", icon: Loader2, variant: "default" } as const,
  done: { label: "Готово", icon: CheckCircle2, variant: "outline" } as const,
  error: { label: "Ошибка", icon: AlertCircle, variant: "destructive" } as const,
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function GraphsListPage() {
  const [books, setBooks] = useState<BookListItem[] | null>(null);
  const [error, setError] = useState(false);

  const load = async () => {
    setError(false);
    try {
      setBooks(await listBooks());
    } catch {
      setError(true);
    }
  };

  const handleDelete = async (id: string) => {
    setBooks((prev) => prev?.filter((b) => b.id !== id) ?? null);
    try {
      await deleteBook(id);
    } catch {
      load();
    }
  };

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const data = await listBooks();
        if (!active) return;
        setBooks(data);
        setError(false);
        if (data.some((b) => b.status === "processing")) {
          timer = setTimeout(poll, 3000);
        }
      } catch {
        if (active) setError(true);
      }
    };
    poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, []);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Графы знаний
          </h1>
          <p className="text-sm text-muted-foreground">
            Выберите ранее загруженный учебник или добавьте новый.
          </p>
        </div>
        <Button asChild className="gap-2">
          <Link to="/upload">
            <Upload className="size-4" />
            Загрузить книгу
          </Link>
        </Button>
      </div>

      {error ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
            <AlertCircle className="size-10 text-destructive" />
            <div className="space-y-1">
              <p className="font-medium">Не удалось загрузить список</p>
              <p className="text-sm text-muted-foreground">
                Проверьте, запущен ли сервер, и попробуйте снова.
              </p>
            </div>
            <Button variant="outline" className="gap-2" onClick={load}>
              <RefreshCw className="size-4" />
              Повторить
            </Button>
          </CardContent>
        </Card>
      ) : books === null ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} aria-hidden>
              <CardContent className="space-y-4 p-5">
                <div className="h-5 w-2/3 animate-pulse rounded bg-muted" />
                <div className="h-3 w-1/3 animate-pulse rounded bg-muted" />
                <div className="h-2 w-full animate-pulse rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : books.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
            <span className="flex size-12 items-center justify-center rounded-xl bg-muted text-muted-foreground">
              <Network className="size-6" />
            </span>
            <div className="space-y-1">
              <p className="font-medium">Пока нет ни одного графа</p>
              <p className="text-sm text-muted-foreground">
                Загрузите PDF-учебник, чтобы построить первый граф знаний.
              </p>
            </div>
            <Button asChild className="gap-2">
              <Link to="/upload">
                <Upload className="size-4" />
                Загрузить книгу
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {books.map((book) => (
            <li key={book.id}>
              <GraphCard book={book} onDelete={() => handleDelete(book.id)} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function GraphCard({
  book,
  onDelete,
}: {
  book: BookListItem;
  onDelete: () => void;
}) {
  const cfg = STATUS_CONFIG[book.status] ?? STATUS_CONFIG.processing;
  const Icon = cfg.icon;
  const ready = book.status === "done";
  const pct =
    book.chapters_total > 0
      ? Math.round((book.chapters_done / book.chapters_total) * 100)
      : 0;

  const handleDeleteClick = (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (confirm(`Удалить граф «${book.title}»? Действие необратимо.`)) {
      onDelete();
    }
  };

  const deleteButton = (
    <Button
      variant="ghost"
      size="icon"
      className="absolute right-2 top-2 z-10 size-7 text-muted-foreground hover:text-destructive"
      onClick={handleDeleteClick}
      title="Удалить граф"
    >
      <Trash2 className="size-4" />
    </Button>
  );

  const card = (
    <Card
      className={cn(
        "relative h-full transition-all",
        ready
          ? "hover:border-primary/40 hover:shadow-sm"
          : "opacity-95",
      )}
    >
      {deleteButton}
      <CardContent className="flex h-full flex-col gap-3 p-5">
        <div className="flex items-start justify-between gap-3 pr-8">
          <h2 className="line-clamp-2 font-semibold leading-snug" title={book.title}>
            {book.title}
          </h2>
          <Badge variant={cfg.variant} className="shrink-0 gap-1">
            <Icon
              className={cn("size-3", book.status === "processing" && "animate-spin")}
            />
            {cfg.label}
          </Badge>
        </div>

        <p className="text-xs text-muted-foreground">
          {formatDate(book.created_at)}
          {ready && book.entities_count > 0 && (
            <> · {book.entities_count} сущностей</>
          )}
        </p>

        {ready && book.total_tokens > 0 && (
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Coins className="size-3.5" />
            {book.total_tokens.toLocaleString("ru-RU")} токенов
            {book.llm_calls > 0 && <> · {book.llm_calls} вызовов LLM</>}
          </p>
        )}

        {book.status === "processing" && (
          <div className="mt-auto space-y-1.5">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>
                {book.chapters_done} из {book.chapters_total || "?"} глав
              </span>
              <span className="tabular-nums">{pct}%</span>
            </div>
            <Progress value={pct} />
          </div>
        )}

        {ready && (
          <div className="mt-auto flex items-center gap-1 pt-1 text-sm font-medium text-primary">
            Открыть граф
            <ArrowRight className="size-4 transition-transform group-hover/card:translate-x-0.5" />
          </div>
        )}

        {book.status === "error" && (
          <p className="mt-auto text-xs text-destructive">
            Обработка завершилась с ошибкой.
          </p>
        )}
      </CardContent>
    </Card>
  );

  if (!ready) {
    return <div aria-disabled className="group/card block">{card}</div>;
  }

  return (
    <Link
      to={`/graphs/${book.id}`}
      className="group/card block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      aria-label={`Открыть граф: ${book.title}`}
    >
      {card}
    </Link>
  );
}
