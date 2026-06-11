import { useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { Upload } from "lucide-react";
import { uploadBook } from "../../api/books";
import { useOntology } from "../../hooks/useOntology";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ProcessingStatus } from "./ProcessingStatus";

interface Props {
  onReady: (bookId: string) => void;
}

const PROFILE_LABELS: Record<string, string> = {
  universal: "Универсальный",
  math: "Математика",
  cs: "Информатика",
  history: "История",
  economics: "Экономика",
};

export function UploadView({ onReady }: Props) {
  const { ontology } = useOntology();
  const [bookId, setBookId] = useState<string | null>(null);
  const [profile, setProfile] = useState("universal");
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setError(null);
    setUploading(true);
    try {
      const book = await uploadBook(file, profile);
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

  const profiles = ontology?.profiles ?? [];

  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Knowledge Graph Tutor</h1>
          <p className="text-muted-foreground">Загрузите PDF-учебник для построения графа знаний</p>
        </div>

        {profiles.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Профиль дисциплины</p>
            <div className="flex flex-wrap gap-2">
              {profiles.map((p) => {
                const active = profile === p.profile_name;
                return (
                  <button
                    key={p.profile_name}
                    type="button"
                    onClick={() => setProfile(p.profile_name)}
                    className={cn(
                      "rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors",
                      active
                        ? "border-primary bg-primary/10 text-foreground"
                        : "border-border text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    {PROFILE_LABELS[p.profile_name] ?? p.profile_name}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-muted-foreground">
              Определяет, какие типы сущностей извлекаются из учебника.
            </p>
          </div>
        )}

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
