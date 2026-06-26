import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";
import {
  Filter,
  FlaskConical,
  Maximize2,
  MessageCircle,
  Settings2,
  X,
} from "lucide-react";
import { useGraph } from "../../hooks/useGraph";
import { useProgress } from "../../hooks/useProgress";
import { useOntology } from "../../hooks/useOntology";
import { useGraphSettings } from "../../store/graphSettingsStore";
import { getBookStatus } from "../../api/books";
import type { EntityStatus, GraphNode } from "../../types";
import { Button } from "@/components/ui/button";
import { NodePanel } from "./NodePanel";
import { GraphSettingsDialog } from "./GraphSettingsDialog";
import { GraphFilters } from "./GraphFilters";
import { QAChat } from "../qa/QAChat";
import { CreateTestDialog } from "../test/CreateTestDialog";

interface Props {
  bookId: string;
  sessionId: string;
}

const FALLBACK_COLOR = "#94a3b8";

const STATUS_RING: Record<EntityStatus, string> = {
  not_started: "#cbd5e1",
  in_progress: "#3b82f6",
  learned: "#22c55e",
  locked: "#f43f5e",
};

const STATUS_LABELS: Record<EntityStatus, string> = {
  not_started: "Не начато",
  in_progress: "В процессе",
  learned: "Изучено",
  locked: "Заблокировано",
};

interface GNode extends GraphNode {
  color: string;
  x?: number;
  y?: number;
  neighbors?: GNode[];
  links?: GLink[];
  __bckg?: [number, number];
}
interface GLink {
  source: GNode | string;
  target: GNode | string;
  relation_type: string;
}

export function GraphView({ bookId, sessionId }: Props) {
  const { graph, loading, selectedNode, selectNode, highlight, setHighlight } =
    useGraph(bookId, sessionId);
  const { byEntity } = useProgress(sessionId);
  const { entityTypes, relationTypes } = useOntology();
  const settings = useGraphSettings();

  const navigate = useNavigate();
  const [qaOpen, setQaOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [createTestOpen, setCreateTestOpen] = useState(false);
  const [hoverNode, setHoverNode] = useState<GNode | null>(null);
  const [chapterTitles, setChapterTitles] = useState<Record<string, string>>({});

  const [hiddenTypes, setHiddenTypes] = useState<Set<string>>(new Set());
  const [hiddenRelations, setHiddenRelations] = useState<Set<string>>(new Set());
  const [hiddenChapters, setHiddenChapters] = useState<Set<string>>(new Set());

  const fgRef = useRef<ForceGraphMethods<GNode, GLink>>(undefined);
  const graphBoxRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    getBookStatus(bookId)
      .then((s) => {
        const map: Record<string, string> = {};
        for (const ch of s.chapters) map[ch.id] = ch.title;
        setChapterTitles(map);
      })
      .catch(() => undefined);
  }, [bookId]);

  useEffect(() => () => setHighlight(null), [setHighlight]);

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

  const present = useMemo(() => {
    const types = new Set<string>();
    const rels = new Set<string>();
    const chapters = new Set<string>();
    if (graph) {
      for (const n of graph.nodes) {
        types.add(n.entity_type);
        if (n.chapter_id) chapters.add(n.chapter_id);
      }
      for (const e of graph.edges) rels.add(e.relation_type);
    }
    return { types, rels, chapters };
  }, [graph]);

  const data = useMemo(() => {
    if (!graph) return { nodes: [] as GNode[], links: [] as GLink[] };

    const visibleNodes = graph.nodes.filter(
      (n) =>
        !hiddenTypes.has(n.entity_type) &&
        !(n.chapter_id && hiddenChapters.has(n.chapter_id)),
    );
    const nodes: GNode[] = visibleNodes.map((n) => ({
      ...n,
      status: byEntity[n.id]?.status ?? n.status,
      color: entityTypes[n.entity_type]?.color ?? FALLBACK_COLOR,
      neighbors: [],
      links: [],
    }));
    const byId = new Map(nodes.map((n) => [n.id, n]));

    const links: GLink[] = [];
    for (const e of graph.edges) {
      if (hiddenRelations.has(e.relation_type)) continue;
      const src = byId.get(e.source);
      const tgt = byId.get(e.target);
      if (!src || !tgt) continue;
      const link: GLink = {
        source: src,
        target: tgt,
        relation_type: e.relation_type,
      };
      links.push(link);
      src.neighbors!.push(tgt);
      tgt.neighbors!.push(src);
      src.links!.push(link);
      tgt.links!.push(link);
    }
    return { nodes, links };
  }, [graph, byEntity, entityTypes, hiddenTypes, hiddenRelations, hiddenChapters]);

  const traversalNodes = useMemo(
    () => highlight?.nodes ?? null,
    [highlight],
  );
  const traversalEdges = useMemo(() => {
    if (!highlight) return new Set<string>();
    return new Set(
      highlight.edges.map((e) => `${e.source}->${e.target}:${e.relation_type}`),
    );
  }, [highlight]);

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

  const isFocusDimmed = useCallback(
    (node: GNode): number => {
      if (hlNodes.size > 0) return hlNodes.has(node) ? 1 : 0.15;
      if (traversalNodes) return traversalNodes.has(node.id) ? 1 : 0.12;
      return 1;
    },
    [hlNodes, traversalNodes],
  );

  const paintNode = useCallback(
    (node: GNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const status = (node.status ?? "not_started") as EntityStatus;
      const ring = STATUS_RING[status];
      const alpha = isFocusDimmed(node);
      const isHover = node === hoverNode;
      const inTraversal = traversalNodes?.has(node.id);
      ctx.globalAlpha = alpha;

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
        ctx.fillStyle = node.color;
        ctx.fill();
        ctx.lineWidth = (status === "not_started" ? 1 : 2.5) / globalScale;
        ctx.strokeStyle = ring;
        ctx.stroke();

        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = "#fff";
        ctx.fillText(label, node.x!, node.y!);

        node.__bckg = [w, h];
      } else {
        const r = isHover ? 6 : 4.5;
        if (inTraversal) {
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, r + 3, 0, 2 * Math.PI);
          ctx.fillStyle = "#fcd34d";
          ctx.fill();
        }
        ctx.beginPath();
        ctx.arc(node.x!, node.y!, r, 0, 2 * Math.PI);
        ctx.fillStyle = node.color;
        ctx.fill();
        ctx.lineWidth = (status === "not_started" ? 1.2 : 2.4) / globalScale;
        ctx.strokeStyle = ring;
        if (status === "locked") ctx.setLineDash([2 / globalScale, 2 / globalScale]);
        ctx.stroke();
        ctx.setLineDash([]);
      }
      ctx.globalAlpha = 1;
    },
    [settings.nodeDisplay, hoverNode, isFocusDimmed, traversalNodes],
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
  const legendTypes = Object.values(entityTypes).filter((et) =>
    present.types.has(et.type_name),
  );

  return (
    <div className="flex min-h-0 flex-1 overflow-hidden bg-background">
      <div ref={graphBoxRef} className="relative flex-1 overflow-hidden">
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
            onClick={() => setFiltersOpen(true)}
            className="gap-2"
          >
            <Filter className="size-4" />
            <span className="hidden sm:inline">Фильтры</span>
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
            variant="outline"
            size="sm"
            onClick={() => setCreateTestOpen(true)}
            className="gap-2"
          >
            <FlaskConical className="size-4" />
            <span className="hidden sm:inline">Тест</span>
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

        {!empty && (
          <div className="absolute bottom-3 left-3 z-10 max-w-[min(28rem,calc(100%-1.5rem))] space-y-2 rounded-lg border border-border bg-background/80 px-3 py-2 text-xs shadow-sm backdrop-blur">
            <div className="flex flex-wrap gap-x-3 gap-y-1.5">
              {legendTypes.map((et) => (
                <span
                  key={et.type_name}
                  className="flex items-center gap-1.5 text-muted-foreground"
                >
                  <span
                    className="size-2.5 rounded-full"
                    style={{ backgroundColor: et.color }}
                  />
                  {et.label}
                </span>
              ))}
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-1.5 border-t border-border pt-1.5">
              {(Object.keys(STATUS_RING) as EntityStatus[]).map((s) => (
                <span key={s} className="flex items-center gap-1.5 text-muted-foreground">
                  <span
                    className="size-2.5 rounded-full border-2 bg-transparent"
                    style={{ borderColor: STATUS_RING[s] }}
                  />
                  {STATUS_LABELS[s]}
                </span>
              ))}
            </div>
          </div>
        )}

        {empty ? (
          <div className="flex h-full items-center justify-center px-6 text-center text-muted-foreground">
            <p>Граф пуст или всё скрыто фильтрами.</p>
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
            linkColor={(l) => {
              const gl = l as GLink;
              const key = linkKey(gl);
              if (traversalEdges.has(key)) return "#f59e0b";
              if (hlLinks.has(gl)) return "#f59e0b";
              if (hlLinks.size > 0 || traversalNodes) return "rgba(203,213,225,0.2)";
              return "#cbd5e1";
            }}
            linkWidth={(l) =>
              traversalEdges.has(linkKey(l as GLink)) || hlLinks.has(l as GLink)
                ? 2.5
                : 1
            }
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

      <CreateTestDialog
        open={createTestOpen}
        onOpenChange={setCreateTestOpen}
        sessionId={sessionId}
        presetBookId={bookId}
        onCreated={(t) => navigate(`/tests/${t.id}`)}
      />
      <GraphSettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
      <GraphFilters
        open={filtersOpen}
        onOpenChange={setFiltersOpen}
        entityTypes={legendTypes}
        relationTypes={Object.values(relationTypes).filter((rt) =>
          present.rels.has(rt.type_name),
        )}
        chapters={[...present.chapters]
          .map((id) => ({ id, title: chapterTitles[id] ?? "Глава" }))
          .sort((a, b) => a.title.localeCompare(b.title))}
        activeEntityTypes={
          new Set([...present.types].filter((t) => !hiddenTypes.has(t)))
        }
        activeRelationTypes={
          new Set([...present.rels].filter((t) => !hiddenRelations.has(t)))
        }
        activeChapters={
          new Set([...present.chapters].filter((c) => !hiddenChapters.has(c)))
        }
        toggleEntityType={(t) => setHiddenTypes((s) => toggleSet(s, t))}
        toggleRelationType={(t) => setHiddenRelations((s) => toggleSet(s, t))}
        toggleChapter={(id) => setHiddenChapters((s) => toggleSet(s, id))}
        reset={() => {
          setHiddenTypes(new Set());
          setHiddenRelations(new Set());
          setHiddenChapters(new Set());
        }}
      />
    </div>
  );
}

function toggleSet(set: Set<string>, value: string): Set<string> {
  const next = new Set(set);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

function linkKey(l: GLink): string {
  const s = typeof l.source === "string" ? l.source : l.source.id;
  const t = typeof l.target === "string" ? l.target : l.target.id;
  return `${s}->${t}:${l.relation_type}`;
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
