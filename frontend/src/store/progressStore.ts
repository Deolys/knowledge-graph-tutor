import { create } from "zustand";
import type { ConceptStatus, ProgressEntry } from "../types";
import { getProgress } from "../api/progress";

interface ProgressState {
  byConcept: Record<string, ProgressEntry>;
  load: (sessionId: string) => Promise<void>;
  setStatus: (conceptId: string, status: ConceptStatus) => void;
}

export const useProgressStore = create<ProgressState>((set) => ({
  byConcept: {},
  load: async (sessionId) => {
    const entries = await getProgress(sessionId);
    const byConcept: Record<string, ProgressEntry> = {};
    for (const e of entries) byConcept[e.concept_id] = e;
    set({ byConcept });
  },
  setStatus: (conceptId, status) =>
    set((s) => ({
      byConcept: {
        ...s.byConcept,
        [conceptId]: {
          ...(s.byConcept[conceptId] ?? {
            concept_id: conceptId,
            score: null,
            attempts: 0,
          }),
          status,
        },
      },
    })),
}));
