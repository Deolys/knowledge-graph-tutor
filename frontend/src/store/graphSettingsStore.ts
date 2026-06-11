import { create } from "zustand";
import { persist } from "zustand/middleware";

export type NodeDisplay = "dots" | "text";

export interface GraphSettings {
  nodeDisplay: NodeDisplay;
  showArrows: boolean;
  showParticles: boolean;
  curvedLinks: boolean;
  highlightNeighbors: boolean;
  setNodeDisplay: (v: NodeDisplay) => void;
  setShowArrows: (v: boolean) => void;
  setShowParticles: (v: boolean) => void;
  setCurvedLinks: (v: boolean) => void;
  setHighlightNeighbors: (v: boolean) => void;
}

export const useGraphSettings = create<GraphSettings>()(
  persist(
    (set) => ({
      nodeDisplay: "dots",
      showArrows: true,
      showParticles: false,
      curvedLinks: false,
      highlightNeighbors: true,
      setNodeDisplay: (nodeDisplay) => set({ nodeDisplay }),
      setShowArrows: (showArrows) => set({ showArrows }),
      setShowParticles: (showParticles) => set({ showParticles }),
      setCurvedLinks: (curvedLinks) => set({ curvedLinks }),
      setHighlightNeighbors: (highlightNeighbors) => set({ highlightNeighbors }),
    }),
    { name: "kg_graph_settings" },
  ),
);
