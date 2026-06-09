import { useState } from "react";
import { uploadBook } from "../../api/books";
import { ProcessingStatus } from "./ProcessingStatus";

interface Props {
  onReady: (bookId: string) => void;
}

/** Загрузка PDF + ожидание завершения ingestion. */
export function UploadView({ onReady }: Props) {
  const [bookId, setBookId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    setError(null);
    setUploading(true);
    try {
      const book = await uploadBook(file);
      setBookId(book.id);
    } catch {
      setError("Не удалось загрузить файл");
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  if (bookId) {
    return <ProcessingStatus bookId={bookId} onReady={() => onReady(bookId)} />;
  }

  return (
    <div style={{ padding: 40, maxWidth: 600, margin: "0 auto" }}>
      <h1>Knowledge Graph Tutor</h1>
      <div
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        style={{
          border: "2px dashed #94a3b8",
          borderRadius: 12,
          padding: 60,
          textAlign: "center",
          color: "#475569",
        }}
      >
        {uploading ? (
          <p>Загрузка…</p>
        ) : (
          <>
            <p>Перетащите PDF-учебник сюда</p>
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) =>
                e.target.files?.[0] && handleFile(e.target.files[0])
              }
            />
          </>
        )}
      </div>
      {error && <p style={{ color: "#ef4444" }}>{error}</p>}
    </div>
  );
}
