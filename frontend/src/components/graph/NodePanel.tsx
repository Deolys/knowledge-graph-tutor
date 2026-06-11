import { useEffect, useState } from "react";
import { X, FlaskConical } from "lucide-react";
import type { Concept, GraphNode } from "../../types";
import { getConcept } from "../../api/concepts";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { TestView } from "../test/TestView";

interface Props {
  node: GraphNode;
  sessionId: string;
  onClose: () => void;
}

export function NodePanel({ node, sessionId, onClose }: Props) {
  const [concept, setConcept] = useState<Concept | null>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    setTesting(false);
    setConcept(null);
    getConcept(node.id).then(setConcept);
  }, [node.id]);

  return (
    <aside className="w-80 border-l border-border flex flex-col shrink-0 bg-card">
      <div className="flex items-start justify-between gap-2 p-4">
        <h3 className="font-semibold leading-tight">{node.name}</h3>
        <Button variant="ghost" size="icon" className="size-7 shrink-0 -mt-0.5" onClick={onClose}>
          <X className="size-4" />
        </Button>
      </div>
      <Separator />

      <ScrollArea className="min-h-0 flex-1 [&>[data-slot=scroll-area-viewport]>div]:!block">
        <div className="p-4 space-y-4">
          {!concept ? (
            <div className="flex items-center gap-2 text-muted-foreground text-sm py-4">
              <div className="size-4 rounded-full border-2 border-muted-foreground border-t-transparent animate-spin" />
              Загрузка…
            </div>
          ) : testing ? (
            <TestView
              conceptId={concept.id}
              sessionId={sessionId}
              onDone={() => setTesting(false)}
            />
          ) : (
            <>
              <p className="text-sm leading-relaxed">{concept.definition}</p>

              {concept.formula && (
                <div className="rounded-md bg-muted px-3 py-2">
                  <pre className="text-xs font-mono whitespace-pre-wrap">{concept.formula}</pre>
                </div>
              )}

              {concept.quote && (
                <blockquote className="border-l-2 border-border pl-3 text-sm text-muted-foreground italic">
                  {concept.quote}
                </blockquote>
              )}

              <Button className="w-full gap-2" onClick={() => setTesting(true)}>
                <FlaskConical className="size-4" />
                Пройти тест
              </Button>
            </>
          )}
        </div>
      </ScrollArea>
    </aside>
  );
}
