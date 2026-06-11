import { create } from "zustand";
import type { Graph, GraphNode, TraversalEdge } from "../types";
import { getGraph } from "../api/books";

interface Highlight {
  nodes: Set<string>;
  edges: TraversalEdge[];
}

interface GraphState {
  graph: Graph | null;
  selectedNode: GraphNode | null;
  loading: boolean;
  highlight: Highlight | null;
  load: (bookId: string, sessionId?: string) => Promise<void>;
  selectNode: (node: GraphNode | null) => void;
  setHighlight: (highlight: Highlight | null) => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  graph: null,
  selectedNode: null,
  loading: false,
  highlight: null,
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
  setHighlight: (highlight) => set({ highlight }),
}));
