import { useEffect } from "react";
import { useProgressStore } from "../store/progressStore";

/** Подгружает прогресс сессии в progressStore. */
export function useProgress(sessionId: string) {
  const { byConcept, load, setStatus } = useProgressStore();

  useEffect(() => {
    if (sessionId) load(sessionId);
  }, [sessionId, load]);

  return { byConcept, setStatus, reload: () => load(sessionId) };
}
