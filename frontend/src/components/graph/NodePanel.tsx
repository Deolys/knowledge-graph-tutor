import { useEffect, useState } from "react";
import { X, FlaskConical } from "lucide-react";
import type { Entity, GraphNode } from "../../types";
import { getEntity } from "../../api/entities";
import { useOntology } from "../../hooks/useOntology";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Markdown } from "@/components/ui/markdown";
import { TestView } from "../test/TestView";

interface Props {
  node: GraphNode;
  sessionId: string;
  onClose: () => void;
}

const TEXT_ATTRS = new Set(["definition", "statement", "description"]);
const ATTR_LABELS: Record<string, string> = {
  definition: "Определение",
  statement: "Утверждение",
  description: "Описание",
  latex: "Формула",
  steps: "Шаги",
  variables: "Переменные",
  complexity: "Сложность",
  aliases: "Синонимы",
  proof_sketch: "Идея доказательства",
  kind: "Вид",
  full_name: "Полное имя",
  years: "Годы",
  role: "Роль",
  difficulty: "Сложность",
  category: "Категория",
  vendor: "Производитель",
  organization: "Организация",
  year: "Год",
  date: "Дата",
  location: "Место",
  outcome: "Итог",
  founded: "Основано",
  type: "Тип",
  start: "Начало",
  end: "Конец",
  stages: "Этапы",
  title: "Заголовок",
  order: "Порядок",
};

export function NodePanel({ node, sessionId, onClose }: Props) {
  const [entity, setEntity] = useState<Entity | null>(null);
  const [testing, setTesting] = useState(false);
  const { entityTypes } = useOntology();

  useEffect(() => {
    setTesting(false);
    setEntity(null);
    getEntity(node.id).then(setEntity);
  }, [node.id]);

  const meta = entityTypes[node.entity_type];

  return (
    <aside className="w-80 border-l border-border flex flex-col shrink-0 bg-card">
      <div className="flex items-start justify-between gap-2 p-4">
        <div className="space-y-1.5">
          <h3 className="font-semibold leading-tight">{node.name}</h3>
          {meta && (
            <Badge
              variant="outline"
              className="gap-1.5"
              style={{ borderColor: meta.color }}
            >
              <span
                className="size-2 rounded-full"
                style={{ backgroundColor: meta.color }}
              />
              {meta.label}
            </Badge>
          )}
        </div>
        <Button variant="ghost" size="icon" className="size-7 shrink-0 -mt-0.5" onClick={onClose}>
          <X className="size-4" />
        </Button>
      </div>
      <Separator />

      <ScrollArea className="min-h-0 flex-1 [&>[data-slot=scroll-area-viewport]>div]:!block">
        <div className="p-4 space-y-4">
          {!entity ? (
            <div className="flex items-center gap-2 text-muted-foreground text-sm py-4">
              <div className="size-4 rounded-full border-2 border-muted-foreground border-t-transparent animate-spin" />
              Загрузка…
            </div>
          ) : testing ? (
            <TestView
              entityId={entity.id}
              sessionId={sessionId}
              onDone={() => setTesting(false)}
            />
          ) : (
            <>
              {Object.entries(entity.attrs)
                .filter(([, v]) => v != null && v !== "" && !(Array.isArray(v) && v.length === 0))
                .map(([key, value]) => (
                  <AttrBlock key={key} attrKey={key} value={value} />
                ))}

              {entity.source_quote && (
                <blockquote className="border-l-2 border-border pl-3 text-sm text-muted-foreground italic">
                  {entity.source_quote}
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

function AttrBlock({ attrKey, value }: { attrKey: string; value: unknown }) {
  const label = ATTR_LABELS[attrKey] ?? attrKey;

  if (attrKey === "latex" && typeof value === "string") {
    return (
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <div className="rounded-md bg-muted px-3 py-2">
          <Markdown content={`$$${value}$$`} />
        </div>
      </div>
    );
  }

  if (TEXT_ATTRS.has(attrKey) && typeof value === "string") {
    return (
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <Markdown content={value} className="text-sm leading-relaxed" />
      </div>
    );
  }

  if (Array.isArray(value)) {
    return (
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <div className="flex flex-wrap gap-1">
          {value.map((v, i) => (
            <Badge key={i} variant="secondary" className="font-normal">
              {String(v)}
            </Badge>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="text-sm leading-relaxed">{String(value)}</p>
    </div>
  );
}
