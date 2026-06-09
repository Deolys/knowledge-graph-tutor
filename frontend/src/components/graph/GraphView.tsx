import { useMemo, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { useGraph } from "../../hooks/useGraph";
import { useProgress } from "../../hooks/useProgress";
import type { ConceptStatus, GraphNode } from "../../types";
import { NodePanel } from "./NodePanel";
import { QAChat } from "../qa/QAChat";

interface Props {
  bookId: string;
  sessionId: string;
}

export const NODE_COLORS: Record<ConceptStatus, string> = {
  not_started: "#94a3b8",
  in_progress: "#3b82f6",
  learned: "#22c55e",
  locked: "#e2e8f0",
};

export function GraphView({ bookId, sessionId }: Props) {
  const { graph, loading, selectedNode, selectNode } = useGraph(
    bookId,
    sessionId,
  );
  const { byConcept } = useProgress(sessionId);
  const [qaOpen, setQaOpen] = useState(false);

  // Статус узла: прогресс из стора важнее, чем статус из графа.
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

  if (loading) return <p style={{ padding: 40 }}>Загрузка графа…</p>;

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div style={{ flex: 1, position: "relative" }}>
        <button
          onClick={() => setQaOpen((v) => !v)}
          style={{ position: "absolute", top: 12, right: 12, zIndex: 10 }}
        >
          {qaOpen ? "Закрыть QA" : "Спросить"}
        </button>
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
