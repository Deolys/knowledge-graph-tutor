import { Outlet } from "react-router-dom";
import { Header } from "./Header";

export function Layout() {
  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <Header />
      <main className="flex min-h-0 flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  );
}
