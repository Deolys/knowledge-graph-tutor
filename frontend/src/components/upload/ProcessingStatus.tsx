import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import {
  CheckCircle2,
  Loader2,
  XCircle,
  Clock,
  FileSearch,
  Boxes,
  GitMerge,
  Sparkles,
} from "lucide-react";
import { getBookStatus } from "../../api/books";
import type { BookStatus, ChapterStatus } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface Props {
  bookId: string;
  onReady: () => void;
}

const CHAPTER_STATUS = {
  pending: { label: "Ожидание", icon: Clock, variant: "secondary" } as const,
  processing: { label: "Обработка", icon: Loader2, variant: "default" } as const,
  done: { label: "Готово", icon: CheckCircle2, variant: "outline" } as const,
  error: { label: "Ошибка", icon: XCircle, variant: "destructive" } as const,
};

type Stage = "parsing" | "extracting" | "merging" | "done";

const STAGES: { key: Stage; label: string; icon: typeof FileSearch }[] = [
  { key: "parsing", label: "Разбор PDF", icon: FileSearch },
  { key: "extracting", label: "Извлечение понятий и связей", icon: Boxes },
  { key: "merging", label: "Объединение и сохранение графа", icon: GitMerge },
];

function computeProgress(status: BookStatus | null): {
  pct: number;
  stage: Stage;
} {
  if (!status || status.chapters.length === 0) {
    return { pct: 5, stage: "parsing" };
  }
  if (status.done) {
    return { pct: 100, stage: "done" };
  }

  const total = status.chapters.length;
  let weighted = 0;
  for (const ch of status.chapters) {
    if (ch.status === "done" || ch.status === "error") weighted += 1;
    else if (ch.status === "processing") weighted += 0.5;
  }
  const allChaptersFinished = status.chapters.every(
    (c) => c.status === "done" || c.status === "error",
  );

  if (allChaptersFinished) {
    return { pct: 95, stage: "merging" };
  }

  const pct = Math.round(10 + (weighted / total) * 80);
  return { pct, stage: "extracting" };
}

function currentChapter(chapters: ChapterStatus[]): ChapterStatus | null {
  return chapters.find((c) => c.status === "processing") ?? null;
}

export function ProcessingStatus({ bookId, onReady }: Props) {
  const [status, setStatus] = useState<BookStatus | null>(null);
  const [error, setError] = useState(false);
  const maxPctRef = useRef(0);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const s = await getBookStatus(bookId);
        if (!active) return;
        setStatus(s);
        setError(false);
        if (s.done) {
          onReady();
        } else {
          timer = setTimeout(poll, 2000);
        }
      } catch {
        if (!active) return;
        setError(true);
        timer = setTimeout(poll, 4000);
      }
    };
    poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [bookId, onReady]);

  const { pct, stage } = computeProgress(status);
  if (pct > maxPctRef.current) maxPctRef.current = pct;
  const displayPct = maxPctRef.current;
  const active = currentChapter(status?.chapters ?? []);
  const doneCount =
    status?.chapters.filter((c) => c.status === "done").length ?? 0;
  const total = status?.chapters.length ?? 0;

  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <Card className="w-full max-w-lg">
        <CardHeader className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Sparkles className="size-5" />
            </span>
            <CardTitle>Обработка учебника</CardTitle>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium" aria-live="polite">
                {STAGES.find((s) => s.key === stage)?.label ?? "Готово"}
              </span>
              <span className="tabular-nums text-muted-foreground">
                {displayPct}%
              </span>
            </div>
            <Progress value={displayPct} />
            {total > 0 && stage === "extracting" && (
              <p className="text-xs text-muted-foreground">
                {doneCount} из {total} глав обработано
                {active && <> · сейчас: {active.title}</>}
              </p>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <ol className="space-y-2">
            {STAGES.map((s) => {
              const reached = stageIndex(stage) >= stageIndex(s.key) || stage === "done";
              const isCurrent = s.key === stage;
              const Icon = isCurrent ? Loader2 : reached ? CheckCircle2 : s.icon;
              return (
                <li
                  key={s.key}
                  className={cn(
                    "flex items-center gap-2 text-sm",
                    reached ? "text-foreground" : "text-muted-foreground",
                  )}
                >
                  <Icon
                    className={cn(
                      "size-4 shrink-0",
                      isCurrent && "animate-spin text-primary",
                      !isCurrent && reached && "text-green-600 dark:text-green-500",
                    )}
                  />
                  {s.label}
                </li>
              );
            })}
          </ol>

          {status && status.chapters.length > 0 && (
            <ul className="max-h-56 space-y-2 overflow-y-auto border-t border-border pt-3">
              {status.chapters.map((ch) => {
                const cfg = CHAPTER_STATUS[ch.status] ?? CHAPTER_STATUS.pending;
                const Icon = cfg.icon;
                return (
                  <li
                    key={ch.id}
                    className="flex items-center justify-between gap-2"
                  >
                    <span className="flex-1 truncate text-sm" title={ch.title}>
                      {ch.title}
                    </span>
                    <Badge variant={cfg.variant} className="shrink-0 gap-1">
                      <Icon
                        className={cn(
                          "size-3",
                          ch.status === "processing" && "animate-spin",
                        )}
                      />
                      {cfg.label}
                    </Badge>
                  </li>
                );
              })}
            </ul>
          )}

          {(!status || status.chapters.length === 0) && !error && (
            <div className="flex items-center gap-2 py-2 text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              <span className="text-sm">Извлечение глав из PDF…</span>
            </div>
          )}

          {error && (
            <p className="text-sm text-destructive">
              Потеряна связь с сервером. Повторная попытка…
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function stageIndex(stage: Stage): number {
  return STAGES.findIndex((s) => s.key === stage);
}
