import { cn } from "@/lib/utils";
import { Filter, RotateCcw } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { EntityType, RelationType } from "../../types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entityTypes: EntityType[];
  relationTypes: RelationType[];
  chapters: { id: string; title: string }[];
  activeEntityTypes: Set<string>;
  activeRelationTypes: Set<string>;
  activeChapters: Set<string>;
  toggleEntityType: (t: string) => void;
  toggleRelationType: (t: string) => void;
  toggleChapter: (id: string) => void;
  reset: () => void;
}

export function GraphFilters({
  open,
  onOpenChange,
  entityTypes,
  relationTypes,
  chapters,
  activeEntityTypes,
  activeRelationTypes,
  activeChapters,
  toggleEntityType,
  toggleRelationType,
  toggleChapter,
  reset,
}: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Filter className="size-4" />
            Фильтры графа
          </DialogTitle>
          <DialogDescription>
            Скройте типы сущностей, типы связей или главы.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5">
          <FilterGroup title="Типы сущностей">
            <div className="flex flex-wrap gap-1.5">
              {entityTypes.map((et) => {
                const active = activeEntityTypes.has(et.type_name);
                return (
                  <button
                    key={et.type_name}
                    type="button"
                    onClick={() => toggleEntityType(et.type_name)}
                    className={cn(
                      "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
                      active
                        ? "border-border text-foreground"
                        : "border-dashed border-border text-muted-foreground opacity-50",
                    )}
                  >
                    <span
                      className="size-2.5 rounded-full"
                      style={{ backgroundColor: et.color }}
                    />
                    {et.label}
                  </button>
                );
              })}
            </div>
          </FilterGroup>

          <FilterGroup title="Типы связей">
            <div className="flex flex-wrap gap-1.5">
              {relationTypes.map((rt) => {
                const active = activeRelationTypes.has(rt.type_name);
                return (
                  <button
                    key={rt.type_name}
                    type="button"
                    onClick={() => toggleRelationType(rt.type_name)}
                    className={cn(
                      "rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
                      active
                        ? "border-border text-foreground"
                        : "border-dashed border-border text-muted-foreground opacity-50",
                    )}
                  >
                    {rt.label}
                  </button>
                );
              })}
            </div>
          </FilterGroup>

          {chapters.length > 0 && (
            <FilterGroup title="Главы">
              <div className="flex flex-wrap gap-1.5">
                {chapters.map((ch) => {
                  const active = activeChapters.has(ch.id);
                  return (
                    <button
                      key={ch.id}
                      type="button"
                      onClick={() => toggleChapter(ch.id)}
                      className={cn(
                        "max-w-full truncate rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
                        active
                          ? "border-border text-foreground"
                          : "border-dashed border-border text-muted-foreground opacity-50",
                      )}
                      title={ch.title}
                    >
                      {ch.title}
                    </button>
                  );
                })}
              </div>
            </FilterGroup>
          )}

          <Button variant="outline" size="sm" className="gap-2" onClick={reset}>
            <RotateCcw className="size-4" />
            Сбросить фильтры
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function FilterGroup({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{title}</p>
      {children}
    </div>
  );
}
