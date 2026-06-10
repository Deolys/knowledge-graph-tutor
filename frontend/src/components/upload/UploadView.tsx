import { useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { Upload } from "lucide-react";
import { uploadBook } from "../../api/books";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ProcessingStatus } from "./ProcessingStatus";

interface Props {
  onReady: (bookId: string) => void;
}

export function UploadView({ onReady }: Props) {
  const [bookId, setBookId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setError(null);
    setUploading(true);
    try {
      const book = await uploadBook(file);
      setBookId(book.id);
    } catch {
      setError("Не удалось загрузить файл. Попробуйте ещё раз.");
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  if (bookId) {
    return <ProcessingStatus bookId={bookId} onReady={() => onReady(bookId)} />;
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Knowledge Graph Tutor</h1>
          <p className="text-muted-foreground">Загрузите PDF-учебник для построения графа знаний</p>
        </div>

        <Card
          onDrop={onDrop}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          className={cn(
            "cursor-pointer transition-colors border-2 border-dashed",
            dragging ? "border-primary bg-accent" : "border-border hover:border-primary/50",
          )}
          onClick={() => inputRef.current?.click()}
        >
          <CardContent className="flex flex-col items-center gap-4 py-16">
            {uploading ? (
              <>
                <div className="size-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
                <p className="text-muted-foreground">Загрузка файла…</p>
              </>
            ) : (
              <>
                <Upload className="size-10 text-muted-foreground" />
                <div className="text-center space-y-1">
                  <p className="font-medium">Перетащите PDF-учебник сюда</p>
                  <p className="text-sm text-muted-foreground">или нажмите для выбора файла</p>
                </div>
                <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}>
                  Выбрать файл
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />

        {error && (
          <p className="text-sm text-destructive text-center">{error}</p>
        )}
      </div>
    </div>
  );
}
