import { create } from "zustand";
import type { EntityStatus, ProgressEntry } from "../types";
import { getProgress } from "../api/progress";

interface ProgressState {
  byEntity: Record<string, ProgressEntry>;
  load: (sessionId: string) => Promise<void>;
  setStatus: (entityId: string, status: EntityStatus) => void;
}

export const useProgressStore = create<ProgressState>((set) => ({
  byEntity: {},
  load: async (sessionId) => {
    const entries = await getProgress(sessionId);
    const byEntity: Record<string, ProgressEntry> = {};
    for (const e of entries) byEntity[e.entity_id] = e;
    set({ byEntity });
  },
  setStatus: (entityId, status) =>
    set((s) => ({
      byEntity: {
        ...s.byEntity,
        [entityId]: {
          ...(s.byEntity[entityId] ?? {
            entity_id: entityId,
            score: null,
            attempts: 0,
          }),
          status,
        },
      },
    })),
}));
