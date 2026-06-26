import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { listBooks, getBookStatus } from "../../api/books";
import { createTest } from "../../api/tests";
import type { BookListItem, ChapterStatus, TestListItem } from "../../types";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sessionId: string;
  presetBookId?: string;
  onCreated: (test: TestListItem) => void;
}

export function CreateTestDialog({
  open,
  onOpenChange,
  sessionId,
  presetBookId,
  onCreated,
}: Props) {
  const [books, setBooks] = useState<BookListItem[]>([]);
  const [bookId, setBookId] = useState(presetBookId ?? "");
  const [chapters, setChapters] = useState<ChapterStatus[]>([]);
  const [chapterId, setChapterId] = useState("");
  const [count, setCount] = useState(10);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    listBooks()
      .then((bs) => {
        const ready = bs.filter((b) => b.status === "done");
        setBooks(ready);
        if (!bookId && ready.length > 0) setBookId(presetBookId ?? ready[0].id);
      })
      .catch(() => setError("Не удалось загрузить список книг"));
  }, [open, presetBookId, bookId]);

  useEffect(() => {
    if (!bookId) {
      setChapters([]);
      return;
    }
    setChapterId("");
    getBookStatus(bookId)
      .then((s) => setChapters(s.chapters.filter((c) => c.status === "done")))
      .catch(() => setChapters([]));
  }, [bookId]);

  const submit = async () => {
    if (!bookId) return;
    setSubmitting(true);
    setError(null);
    try {
      const test = await createTest({
        book_id: bookId,
        session_id: sessionId,
        question_count: count,
        chapter_ids: chapterId ? [chapterId] : [],
      });
      onCreated(test);
      onOpenChange(false);
    } catch {
      setError("Не удалось сгенерировать тест. Попробуйте другой охват.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Новый тест по графу</DialogTitle>
          <DialogDescription>
            Вопросы генерируются по сущностям выбранного графа знаний.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="test-book">Книга</Label>
            <select
              id="test-book"
              value={bookId}
              onChange={(e) => setBookId(e.target.value)}
              disabled={!!presetBookId}
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
            >
              {books.length === 0 && <option value="">Нет готовых графов</option>}
              {books.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.title}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="test-chapter">Охват</Label>
            <select
              id="test-chapter"
              value={chapterId}
              onChange={(e) => setChapterId(e.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">Вся книга</option>
              {chapters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="test-count">Количество вопросов (1–100)</Label>
            <Input
              id="test-count"
              type="number"
              min={1}
              max={100}
              value={count}
              onChange={(e) =>
                setCount(
                  Math.min(100, Math.max(1, Number(e.target.value) || 1)),
                )
              }
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button
            className="w-full gap-2"
            onClick={submit}
            disabled={submitting || !bookId}
          >
            {submitting && <Loader2 className="size-4 animate-spin" />}
            {submitting ? "Генерация…" : "Создать тест"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
