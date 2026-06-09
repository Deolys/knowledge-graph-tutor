import { useEffect, useState } from "react";
import { getBookStatus } from "../../api/books";
import type { BookStatus } from "../../types";

interface Props {
  bookId: string;
  onReady: () => void;
}

const STATUS_LABEL: Record<string, string> = {
  pending: "ожидание",
  processing: "обработка…",
  done: "готово",
  error: "ошибка",
};

/** Опрос статуса ingestion по главам до завершения обработки. */
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
    return () => {
      active = false;
    };
  }, [bookId, onReady]);

  if (!status) return <p style={{ padding: 40 }}>Запуск обработки…</p>;

  return (
    <div style={{ padding: 40, maxWidth: 600, margin: "0 auto" }}>
      <h2>Обработка учебника</h2>
      {status.chapters.length === 0 && <p>Извлечение глав…</p>}
      <ul>
        {status.chapters.map((ch) => (
          <li key={ch.id}>
            {ch.title} — {STATUS_LABEL[ch.status] ?? ch.status}
          </li>
        ))}
      </ul>
    </div>
  );
}
