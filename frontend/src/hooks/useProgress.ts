import { useEffect } from "react";
import { useProgressStore } from "../store/progressStore";

export function useProgress(sessionId: string) {
  const { byEntity, load, setStatus } = useProgressStore();

  useEffect(() => {
    if (sessionId) load(sessionId);
  }, [sessionId, load]);

  return { byEntity, setStatus, reload: () => load(sessionId) };
}
