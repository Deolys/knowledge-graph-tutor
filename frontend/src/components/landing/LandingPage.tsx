import { Link } from "react-router-dom";
import {
  ArrowRight,
  FileText,
  MessagesSquare,
  Network,
  Sparkles,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const STEPS = [
  {
    icon: Upload,
    title: "Загрузка PDF",
    text: "Загрузите учебник в PDF — система разобьёт его по главам и сохранит формулы.",
  },
  {
    icon: Network,
    title: "Граф знаний",
    text: "LLM извлекает понятия и связи между ними, объединяет дубликаты по смыслу.",
  },
  {
    icon: Sparkles,
    title: "Адаптивные тесты",
    text: "Проверяйте усвоение по каждому понятию — прогресс каскадно открывает темы.",
  },
  {
    icon: MessagesSquare,
    title: "Вопросы и ответы",
    text: "Спрашивайте по материалу — ответ опирается на контекст графа с источниками.",
  },
];

export function LandingPage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
      <section className="flex flex-col items-center py-16 text-center sm:py-24">
        <span className="mb-5 inline-flex items-center gap-1.5 rounded-full border border-border bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
          <Sparkles className="size-3.5" />
          Адаптивное обучение на основе графа знаний
        </span>
        <h1 className="max-w-3xl text-balance text-4xl font-bold tracking-tight sm:text-5xl">
          Превратите учебник в интерактивный граф знаний
        </h1>
        <p className="mt-5 max-w-xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
          Загрузите PDF — и получите визуальную карту понятий, адаптивные тесты
          и ассистента, отвечающего по материалу учебника.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Button asChild size="lg" className="gap-2">
            <Link to="/upload">
              <Upload className="size-4" />
              Загрузить книгу
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="gap-2">
            <Link to="/graphs">
              <Network className="size-4" />
              Открыть граф
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
      </section>

      <section className="pb-20" aria-labelledby="how-it-works">
        <h2
          id="how-it-works"
          className="mb-8 text-center text-2xl font-semibold tracking-tight"
        >
          Как это работает
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            return (
              <Card key={step.title} className="h-full">
                <CardContent className="flex h-full flex-col gap-3 p-5">
                  <div className="flex items-center gap-2">
                    <span className="flex size-9 items-center justify-center rounded-lg bg-muted text-foreground">
                      <Icon className="size-5" />
                    </span>
                    <span className="text-sm font-medium tabular-nums text-muted-foreground">
                      Шаг {i + 1}
                    </span>
                  </div>
                  <h3 className="font-semibold">{step.title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {step.text}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      <section className="pb-24">
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center gap-4 px-6 py-12 text-center">
            <span className="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <FileText className="size-6" />
            </span>
            <h2 className="text-xl font-semibold tracking-tight">
              Готовы начать?
            </h2>
            <p className="max-w-md text-sm text-muted-foreground">
              Загрузите первый учебник и постройте граф знаний за пару минут.
            </p>
            <Button asChild className="gap-2">
              <Link to="/upload">
                <Upload className="size-4" />
                Загрузить книгу
              </Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
