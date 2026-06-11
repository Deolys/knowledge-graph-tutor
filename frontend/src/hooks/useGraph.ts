import { useEffect } from "react";
import { useGraphStore } from "../store/graphStore";

export function useGraph(bookId: string | null, sessionId?: string) {
  const { graph, loading, load, selectedNode, selectNode, highlight, setHighlight } =
    useGraphStore();

  useEffect(() => {
    if (bookId) load(bookId, sessionId);
  }, [bookId, sessionId, load]);

  return { graph, loading, selectedNode, selectNode, highlight, setHighlight };
}
