import { create } from "zustand";
import type { Graph, GraphNode } from "../types";
import { getGraph } from "../api/books";

interface GraphState {
  graph: Graph | null;
  selectedNode: GraphNode | null;
  loading: boolean;
  load: (bookId: string, sessionId?: string) => Promise<void>;
  selectNode: (node: GraphNode | null) => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  graph: null,
  selectedNode: null,
  loading: false,
  load: async (bookId, sessionId) => {
    set({ loading: true });
    try {
      const graph = await getGraph(bookId, sessionId);
      set({ graph });
    } finally {
      set({ loading: false });
    }
  },
  selectNode: (node) => set({ selectedNode: node }),
}));
