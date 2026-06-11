import { useMemo, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { MessageCircle, X } from "lucide-react";
import { useGraph } from "../../hooks/useGraph";
import { useProgress } from "../../hooks/useProgress";
import type { ConceptStatus, GraphNode } from "../../types";
import { Button } from "@/components/ui/button";
import { NodePanel } from "./NodePanel";
import { QAChat } from "../qa/QAChat";

interface Props {
  bookId: string;
  sessionId: string;
}

export const NODE_COLORS: Record<ConceptStatus, string> = {
  not_started: "#94a3b8",
  in_progress: "#3b82f6",
  learned:     "#22c55e",
  locked:      "#e2e8f0",
};

export function GraphView({ bookId, sessionId }: Props) {
  const { graph, loading, selectedNode, selectNode } = useGraph(bookId, sessionId);
  const { byConcept } = useProgress(sessionId);
  const [qaOpen, setQaOpen] = useState(false);

  const data = useMemo(() => {
    if (!graph) return { nodes: [], links: [] };
    return {
      nodes: graph.nodes.map((n) => ({
        ...n,
        status: byConcept[n.id]?.status ?? n.status,
      })),
      links: graph.edges.map((e) => ({
        source: e.source,
        target: e.target,
        type: e.type,
      })),
    };
  }, [graph, byConcept]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="size-5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          Загрузка графа…
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 min-h-0 bg-background overflow-hidden">
      <div className="relative flex-1">
        <div className="absolute top-3 right-3 z-10">
          <Button
            variant={qaOpen ? "default" : "outline"}
            size="sm"
            onClick={() => setQaOpen((v) => !v)}
            className="gap-2"
          >
            {qaOpen ? <X className="size-4" /> : <MessageCircle className="size-4" />}
            {qaOpen ? "Закрыть" : "Спросить"}
          </Button>
        </div>

        <ForceGraph2D
          graphData={data}
          nodeId="id"
          nodeLabel="name"
          nodeColor={(n: { status?: ConceptStatus }) =>
            NODE_COLORS[n.status ?? "not_started"]
          }
          onNodeClick={(n) => selectNode(n as unknown as GraphNode)}
          linkColor={() => "#cbd5e1"}
        />
      </div>
      {selectedNode && (
        <NodePanel
          node={selectedNode}
          sessionId={sessionId}
          onClose={() => selectNode(null)}
        />
      )}
      {qaOpen && <QAChat bookId={bookId} sessionId={sessionId} />}
    </div>
  );
}
