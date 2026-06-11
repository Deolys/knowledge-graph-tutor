import { useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Send } from "lucide-react";
import { askQuestion } from "../../api/qa";
import type { QASource } from "../../types";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

interface Props {
  bookId: string;
  sessionId: string;
}

interface Message {
  role: "user" | "assistant";
  text: string;
  sources?: QASource[];
}

export function QAChat({ bookId, sessionId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const send = async () => {
    const query = input.trim();
    if (!query || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: query }]);
    setBusy(true);
    try {
      const res = await askQuestion({ query, book_id: bookId, session_id: sessionId });
      setMessages((m) => [...m, { role: "assistant", text: res.answer, sources: res.sources }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside className="w-80 border-l border-border flex flex-col shrink-0 bg-card">
      <div className="p-4 font-semibold">Вопрос по учебнику</div>
      <Separator />

      <ScrollArea className="min-h-0 flex-1 [&>[data-slot=scroll-area-viewport]>div]:!block">
        <div className="p-4 space-y-3">
          {messages.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-8">
              Задайте вопрос по содержанию учебника
            </p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={cn("flex flex-col gap-1", m.role === "user" ? "items-end" : "items-start")}
            >
              <div
                className={cn(
                  "rounded-lg px-3 py-2 text-sm max-w-[90%] break-words whitespace-pre-wrap",
                  m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground",
                )}
              >
                {m.text}
              </div>
              {m.sources && m.sources.length > 0 && (
                <div className="flex flex-wrap gap-1 px-1 max-w-full">
                  {m.sources.map((s) => (
                    <Badge
                      key={s.id}
                      variant="outline"
                      className="h-auto max-w-full whitespace-normal break-words py-0.5 text-xs leading-snug"
                    >
                      {s.name}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ))}
          {busy && (
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <div className="size-3 rounded-full border-2 border-muted-foreground border-t-transparent animate-spin" />
              Думаю…
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <Separator />
      <div className="p-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ваш вопрос…"
          disabled={busy}
          className="flex-1 rounded-md border border-input bg-background px-3 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
        />
        <Button size="icon" variant="default" onClick={send} disabled={busy || !input.trim()}>
          <Send className="size-4" />
        </Button>
      </div>
    </aside>
  );
}
