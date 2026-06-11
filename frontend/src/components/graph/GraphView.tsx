import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";
import { Maximize2, MessageCircle, Settings2, X } from "lucide-react";
import { useGraph } from "../../hooks/useGraph";
import { useProgress } from "../../hooks/useProgress";
import { useGraphSettings } from "../../store/graphSettingsStore";
import type { ConceptStatus, GraphNode } from "../../types";
import { Button } from "@/components/ui/button";
import { NodePanel } from "./NodePanel";
import { GraphSettingsDialog } from "./GraphSettingsDialog";
import { QAChat } from "../qa/QAChat";

interface Props {
  bookId: string;
  sessionId: string;
}

export const NODE_COLORS: Record<ConceptStatus, string> = {
  not_started: "#94a3b8",
  in_progress: "#3b82f6",
  learned: "#22c55e",
  locked: "#cbd5e1",
};

const STATUS_LABELS: Record<ConceptStatus, string> = {
  not_started: "Не начато",
  in_progress: "В процессе",
  learned: "Изучено",
  locked: "Заблокировано",
};

interface GNode extends GraphNode {
  x?: number;
  y?: number;
  neighbors?: GNode[];
  links?: GLink[];
  __bckg?: [number, number];
}
interface GLink {
  source: GNode | string;
  target: GNode | string;
  type: string;
}

export function GraphView({ bookId, sessionId }: Props) {
  const { graph, loading, selectedNode, selectNode } = useGraph(bookId, sessionId);
  const { byConcept } = useProgress(sessionId);
  const settings = useGraphSettings();

  const [qaOpen, setQaOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [hoverNode, setHoverNode] = useState<GNode | null>(null);

  const fgRef = useRef<ForceGraphMethods<GNode, GLink>>(undefined);
  const graphBoxRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const el = graphBoxRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({ width, height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [loading]);

  const data = useMemo(() => {
    if (!graph) return { nodes: [] as GNode[], links: [] as GLink[] };

    const nodes: GNode[] = graph.nodes.map((n) => ({
      ...n,
      status: byConcept[n.id]?.status ?? n.status,
      neighbors: [],
      links: [],
    }));
    const byId = new Map(nodes.map((n) => [n.id, n]));

    const links: GLink[] = [];
    for (const e of graph.edges) {
      const src = byId.get(e.source);
      const tgt = byId.get(e.target);
      if (!src || !tgt) continue;
      const link: GLink = { source: src, target: tgt, type: e.type };
      links.push(link);
      src.neighbors!.push(tgt);
      tgt.neighbors!.push(src);
      src.links!.push(link);
      tgt.links!.push(link);
    }
    return { nodes, links };
  }, [graph, byConcept]);

  const { hlNodes, hlLinks } = useMemo(() => {
    const hlNodes = new Set<GNode>();
    const hlLinks = new Set<GLink>();
    if (hoverNode && settings.highlightNeighbors) {
      hlNodes.add(hoverNode);
      hoverNode.neighbors?.forEach((n) => hlNodes.add(n));
      hoverNode.links?.forEach((l) => hlLinks.add(l));
    }
    return { hlNodes, hlLinks };
  }, [hoverNode, settings.highlightNeighbors]);

  const handleNodeHover = useCallback((node: GNode | null) => {
    setHoverNode(node);
  }, []);

  const handleNodeClick = useCallback(
    (node: GNode) => {
      selectNode(node as GraphNode);
      const fg = fgRef.current;
      if (fg && node.x != null && node.y != null) {
        fg.centerAt(node.x, node.y, 600);
        fg.zoom(Math.max(fg.zoom(), 3), 600);
      }
    },
    [selectNode],
  );

  const handleFit = useCallback(() => {
    fgRef.current?.zoomToFit(500, 60);
  }, []);

  const paintNode = useCallback(
    (node: GNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const status = (node.status ?? "not_started") as ConceptStatus;
      const color = NODE_COLORS[status];
      const dimmed =
        hlNodes.size > 0 && !hlNodes.has(node) ? 0.15 : 1;
      const isHover = node === hoverNode;
      ctx.globalAlpha = dimmed;

      if (settings.nodeDisplay === "text") {
        const label = node.name;
        const fontSize = Math.max(12 / globalScale, 2);
        ctx.font = `${fontSize}px Inter, Sans-Serif`;
        const textWidth = ctx.measureText(label).width;
        const padX = fontSize * 0.6;
        const padY = fontSize * 0.4;
        const w = textWidth + padX * 2;
        const h = fontSize + padY * 2;

        roundRect(ctx, node.x! - w / 2, node.y! - h / 2, w, h, fontSize * 0.4);
        ctx.fillStyle = isHover ? color : "rgba(255,255,255,0.92)";
        ctx.fill();
        ctx.lineWidth = (isHover ? 2 : 1.2) / globalScale;
        ctx.strokeStyle = color;
        ctx.stroke();

        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = isHover ? "#fff" : "#1e293b";
        ctx.fillText(label, node.x!, node.y!);

        node.__bckg = [w, h];
      } else {
        const r = isHover ? 6 : 4.5;
        if (hlNodes.has(node)) {
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, r + 2.5, 0, 2 * Math.PI);
          ctx.fillStyle = isHover ? "#f59e0b" : "#fcd34d";
          ctx.fill();
        }
        ctx.beginPath();
        ctx.arc(node.x!, node.y!, r, 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = 1 / globalScale;
        ctx.strokeStyle = "rgba(255,255,255,0.85)";
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    },
    [settings.nodeDisplay, hlNodes, hoverNode],
  );

  const paintPointerArea = useCallback(
    (node: GNode, color: string, ctx: CanvasRenderingContext2D) => {
      ctx.fillStyle = color;
      if (settings.nodeDisplay === "text" && node.__bckg) {
        const [w, h] = node.__bckg;
        ctx.fillRect(node.x! - w / 2, node.y! - h / 2, w, h);
      } else {
        ctx.beginPath();
        ctx.arc(node.x!, node.y!, 6, 0, 2 * Math.PI);
        ctx.fill();
      }
    },
    [settings.nodeDisplay],
  );

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

  const empty = data.nodes.length === 0;

  return (
    <div className="flex min-h-0 flex-1 overflow-hidden bg-background">
      <div ref={graphBoxRef} className="relative flex-1 overflow-hidden">
        {/* Тулбар */}
        <div className="absolute right-3 top-3 z-10 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleFit}
            className="gap-2"
            title="Вписать граф в экран"
          >
            <Maximize2 className="size-4" />
            <span className="hidden sm:inline">Вписать</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSettingsOpen(true)}
            className="gap-2"
          >
            <Settings2 className="size-4" />
            <span className="hidden sm:inline">Настройки</span>
          </Button>
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

        {/* Легенда статусов */}
        {!empty && (
          <div className="absolute bottom-3 left-3 z-10 flex flex-wrap gap-x-4 gap-y-1.5 rounded-lg border border-border bg-background/80 px-3 py-2 text-xs shadow-sm backdrop-blur">
            {(Object.keys(NODE_COLORS) as ConceptStatus[]).map((s) => (
              <span key={s} className="flex items-center gap-1.5 text-muted-foreground">
                <span
                  className="size-2.5 rounded-full"
                  style={{ backgroundColor: NODE_COLORS[s] }}
                />
                {STATUS_LABELS[s]}
              </span>
            ))}
          </div>
        )}

        {empty ? (
          <div className="flex h-full items-center justify-center px-6 text-center text-muted-foreground">
            <p>В этом графе пока нет понятий.</p>
          </div>
        ) : (
          <ForceGraph2D
            ref={fgRef}
            width={size.width || undefined}
            height={size.height || undefined}
            graphData={data}
            nodeId="id"
            nodeRelSize={5}
            nodeCanvasObject={paintNode}
            nodePointerAreaPaint={paintPointerArea}
            onNodeHover={(n) => handleNodeHover(n as GNode | null)}
            onNodeClick={(n) => handleNodeClick(n as GNode)}
            onBackgroundClick={() => selectNode(null)}
            linkColor={(l) =>
              hlLinks.has(l as GLink)
                ? "#f59e0b"
                : hlNodes.size > 0
                  ? "rgba(203,213,225,0.25)"
                  : "#cbd5e1"
            }
            linkWidth={(l) => (hlLinks.has(l as GLink) ? 2.5 : 1)}
            linkCurvature={settings.curvedLinks ? 0.25 : 0}
            linkDirectionalArrowLength={settings.showArrows ? 3.5 : 0}
            linkDirectionalArrowRelPos={1}
            linkDirectionalParticles={
              settings.showParticles ? 2 : (l) => (hlLinks.has(l as GLink) ? 3 : 0)
            }
            linkDirectionalParticleWidth={(l) =>
              hlLinks.has(l as GLink) ? 3 : 1.6
            }
            cooldownTicks={120}
            onEngineStop={() => fgRef.current?.zoomToFit(400, 60)}
          />
        )}
      </div>

      {selectedNode && (
        <NodePanel
          node={selectedNode}
          sessionId={sessionId}
          onClose={() => selectNode(null)}
        />
      )}
      {qaOpen && <QAChat bookId={bookId} sessionId={sessionId} />}

      <GraphSettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  );
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
}
