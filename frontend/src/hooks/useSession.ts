import { useEffect, useState } from "react";

const KEY = "kg_session_id";

function createId(): string {
  return crypto.randomUUID();
}

/** session_id хранится в localStorage — авторизации в MVP нет. */
export function useSession(): string {
  const [sessionId] = useState<string>(() => {
    const existing = localStorage.getItem(KEY);
    if (existing) return existing;
    const id = createId();
    localStorage.setItem(KEY, id);
    return id;
  });

  useEffect(() => {
    if (!localStorage.getItem(KEY)) localStorage.setItem(KEY, sessionId);
  }, [sessionId]);

  return sessionId;
}
