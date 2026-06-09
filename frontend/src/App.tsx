import { useState } from "react";
import { useSession } from "./hooks/useSession";
import { UploadView } from "./components/upload/UploadView";
import { GraphView } from "./components/graph/GraphView";

/**
 * Каркас приложения: если книга не выбрана — экран загрузки PDF,
 * иначе — граф знаний. Полноценный роутинг/layout — по мере роста.
 */
export function App() {
  const sessionId = useSession();
  const [bookId, setBookId] = useState<string | null>(null);

  if (!bookId) {
    return <UploadView onReady={setBookId} />;
  }
  return <GraphView bookId={bookId} sessionId={sessionId} />;
}
