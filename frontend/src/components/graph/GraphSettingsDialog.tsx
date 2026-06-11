import { Circle, Type } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useGraphSettings, type NodeDisplay } from "../../store/graphSettingsStore";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const NODE_MODES: { value: NodeDisplay; label: string; icon: typeof Circle }[] = [
  { value: "dots", label: "Точки", icon: Circle },
  { value: "text", label: "Текст", icon: Type },
];

export function GraphSettingsDialog({ open, onOpenChange }: Props) {
  const s = useGraphSettings();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Настройки графа</DialogTitle>
          <DialogDescription>
            Настройте отображение вершин и связей.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5">
          <div className="space-y-2">
            <Label className="font-medium">Отображение вершин</Label>
            <div
              role="radiogroup"
              aria-label="Отображение вершин"
              className="grid grid-cols-2 gap-2"
            >
              {NODE_MODES.map((mode) => {
                const Icon = mode.icon;
                const active = s.nodeDisplay === mode.value;
                return (
                  <button
                    key={mode.value}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    onClick={() => s.setNodeDisplay(mode.value)}
                    className={cn(
                      "flex items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-medium transition-colors",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      active
                        ? "border-primary bg-primary/10 text-foreground"
                        : "border-border text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    <Icon className="size-4" />
                    {mode.label}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-muted-foreground">
              «Текст» показывает названия понятий прямо на графе.
            </p>
          </div>

          <div className="space-y-3 border-t border-border pt-4">
            <ToggleRow
              id="arrows"
              label="Стрелки направления"
              hint="Показывать направление связей между понятиями"
              checked={s.showArrows}
              onChange={s.setShowArrows}
            />
            <ToggleRow
              id="particles"
              label="Анимация потока"
              hint="Движущиеся частицы вдоль связей"
              checked={s.showParticles}
              onChange={s.setShowParticles}
            />
            <ToggleRow
              id="curved"
              label="Изогнутые связи"
              hint="Кривые линии вместо прямых"
              checked={s.curvedLinks}
              onChange={s.setCurvedLinks}
            />
            <ToggleRow
              id="highlight"
              label="Подсветка соседей"
              hint="Выделять связанные понятия при наведении"
              checked={s.highlightNeighbors}
              onChange={s.setHighlightNeighbors}
            />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

interface ToggleRowProps {
  id: string;
  label: string;
  hint: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}

function ToggleRow({ id, label, hint, checked, onChange }: ToggleRowProps) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="space-y-0.5">
        <Label htmlFor={id} className="font-medium">
          {label}
        </Label>
        <p className="text-xs text-muted-foreground">{hint}</p>
      </div>
      <Switch id={id} checked={checked} onCheckedChange={onChange} />
    </div>
  );
}
