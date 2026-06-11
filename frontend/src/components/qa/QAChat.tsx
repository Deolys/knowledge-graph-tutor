import { useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Send, Sparkles, Search } from "lucide-react";
import { askQuestion } from "../../api/qa";
import type { QAResponse, QASource, TraversalEdge } from "../../types";
import { useGraphStore } from "../../store/graphStore";
import { useOntologyStore } from "../../store/ontologyStore";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Markdown } from "@/components/ui/markdown";

interface Props {
  bookId: string;
  sessionId: string;
}

interface Message {
  role: "user" | "assistant";
  text: string;
  sources?: QASource[];
  traversalNodes?: string[];
  traversalEdges?: TraversalEdge[];
  mode?: QAResponse["mode"];
}

export function QAChat({ bookId, sessionId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const setHighlight = useGraphStore((s) => s.setHighlight);
  const graph = useGraphStore((s) => s.graph);
  const selectNode = useGraphStore((s) => s.selectNode);
  const entityTypes = useOntologyStore((s) => s.entityTypes);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const highlightMessage = (m: Message) => {
    if (!m.traversalNodes?.length) return;
    setHighlight({
      nodes: new Set(m.traversalNodes),
      edges: m.traversalEdges ?? [],
    });
  };

  const send = async () => {
    const query = input.trim();
    if (!query || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: query }]);
    setBusy(true);
    try {
      const res = await askQuestion({ query, book_id: bookId, session_id: sessionId });
      const msg: Message = {
        role: "assistant",
        text: res.answer,
        sources: res.sources,
        traversalNodes: res.traversal_nodes,
        traversalEdges: res.traversal_edges,
        mode: res.mode,
      };
      setMessages((m) => [...m, msg]);
      highlightMessage(msg);
    } finally {
      setBusy(false);
    }
  };

  const openSource = (s: QASource) => {
    const node = graph?.nodes.find((n) => n.id === s.id);
    if (node) selectNode(node);
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
                  "rounded-lg px-3 py-2 text-sm max-w-[90%] break-words",
                  m.role === "user"
                    ? "bg-primary text-primary-foreground whitespace-pre-wrap"
                    : "bg-muted text-foreground",
                )}
              >
                {m.role === "assistant" ? <Markdown content={m.text} /> : m.text}
              </div>

              {m.role === "assistant" && m.mode === "vector_fallback" && (
                <span className="flex items-center gap-1 px-1 text-[11px] text-muted-foreground">
                  <Search className="size-3" />
                  векторный поиск
                </span>
              )}

              {m.sources && m.sources.length > 0 && (
                <div className="flex flex-col gap-1.5 px-1 max-w-full">
                  <div className="flex flex-wrap gap-1">
                    {m.sources.map((s) => {
                      const color = entityTypes[s.entity_type]?.color;
                      return (
                        <button key={s.id} type="button" onClick={() => openSource(s)}>
                          <Badge
                            variant="outline"
                            className="h-auto max-w-full cursor-pointer whitespace-normal break-words py-0.5 text-xs leading-snug hover:bg-accent"
                            style={color ? { borderColor: color } : undefined}
                          >
                            {s.name}
                          </Badge>
                        </button>
                      );
                    })}
                  </div>
                  {m.traversalNodes && m.traversalNodes.length > 0 && (
                    <button
                      type="button"
                      onClick={() => highlightMessage(m)}
                      className="flex w-fit items-center gap-1 text-[11px] text-primary hover:underline"
                    >
                      <Sparkles className="size-3" />
                      Показать на графе
                    </button>
                  )}
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
