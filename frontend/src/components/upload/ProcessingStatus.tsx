import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { CheckCircle, Loader2, XCircle, Clock } from "lucide-react";
import { getBookStatus } from "../../api/books";
import type { BookStatus } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface Props {
  bookId: string;
  onReady: () => void;
}

const STATUS_CONFIG = {
  pending:    { label: "Ожидание",   icon: Clock,    variant: "secondary" } as const,
  processing: { label: "Обработка",  icon: Loader2,  variant: "default"   } as const,
  done:       { label: "Готово",     icon: CheckCircle, variant: "outline" } as const,
  error:      { label: "Ошибка",     icon: XCircle,  variant: "destructive" } as const,
};

export function ProcessingStatus({ bookId, onReady }: Props) {
  const [status, setStatus] = useState<BookStatus | null>(null);

  useEffect(() => {
    let active = true;
    const poll = async () => {
      const s = await getBookStatus(bookId);
      if (!active) return;
      setStatus(s);
      if (s.done) {
        onReady();
      } else {
        setTimeout(poll, 2000);
      }
    };
    poll();
    return () => { active = false; };
  }, [bookId, onReady]);

  const doneCount = status?.chapters.filter((c) => c.status === "done").length ?? 0;
  const total = status?.chapters.length ?? 0;
  const progressPct = total > 0 ? Math.round((doneCount / total) * 100) : 0;

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Обработка учебника</CardTitle>
          {total > 0 && (
            <div className="space-y-1">
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>{doneCount} из {total} глав</span>
                <span>{progressPct}%</span>
              </div>
              <Progress value={progressPct} />
            </div>
          )}
        </CardHeader>
        <CardContent>
          {!status || status.chapters.length === 0 ? (
            <div className="flex items-center gap-2 text-muted-foreground py-4">
              <Loader2 className="size-4 animate-spin" />
              <span>Извлечение глав из PDF…</span>
            </div>
          ) : (
            <ul className="space-y-2">
              {status.chapters.map((ch) => {
                const cfg = STATUS_CONFIG[ch.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.pending;
                const Icon = cfg.icon;
                return (
                  <li key={ch.id} className="flex items-center justify-between gap-2">
                    <span className="text-sm truncate flex-1">{ch.title}</span>
                    <Badge variant={cfg.variant} className="shrink-0 gap-1">
                      <Icon className={cn("size-3", ch.status === "processing" && "animate-spin")} />
                      {cfg.label}
                    </Badge>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
