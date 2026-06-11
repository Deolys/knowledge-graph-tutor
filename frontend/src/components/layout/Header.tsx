import { Link, NavLink } from "react-router-dom";
import { Network, Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const NAV_ITEMS = [
  { to: "/", label: "Главная", end: true },
  { to: "/graphs", label: "Графы", end: false },
];

export function Header() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-4 sm:px-6">
        <Link
          to="/"
          className="flex items-center gap-2 font-semibold tracking-tight transition-opacity hover:opacity-80"
        >
          <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Network className="size-4" />
          </span>
          <span className="hidden sm:inline">Knowledge Graph Tutor</span>
          <span className="sm:hidden">KG Tutor</span>
        </Link>

        <nav className="flex items-center gap-1" aria-label="Основная навигация">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  isActive
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto">
          <Button asChild size="sm" className="gap-1.5">
            <Link to="/upload">
              <Upload className="size-4" />
              <span className="hidden sm:inline">Загрузить книгу</span>
              <span className="sm:hidden">Загрузить</span>
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
