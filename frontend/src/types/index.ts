export type EntityStatus =
  | "not_started"
  | "in_progress"
  | "learned"
  | "locked";

export interface EntityType {
  type_name: string;
  label: string;
  description: string;
  attrs: string[];
  color: string;
  tier: string;
}

export interface RelationType {
  type_name: string;
  label: string;
  domain_types: string[];
  range_types: string[];
  is_transitive: boolean;
  is_symmetric: boolean;
  traversal_weight: number;
}

export interface Profile {
  profile_name: string;
  entity_types: string[];
}

export interface Ontology {
  version: string;
  entity_types: EntityType[];
  relation_types: RelationType[];
  profiles: Profile[];
}

export interface GraphNode {
  id: string;
  name: string;
  entity_type: string;
  chapter_id: string | null;
  status: EntityStatus;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation_type: string;
  confidence: number;
}

export interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Book {
  id: string;
  title: string;
  filename: string;
  profile: string;
  created_at: string;
}

export interface BookListItem {
  id: string;
  title: string;
  filename: string;
  profile: string;
  created_at: string;
  chapters_total: number;
  chapters_done: number;
  entities_count: number;
  status: "processing" | "done" | "error";
}

export interface ChapterStatus {
  id: string;
  title: string;
  order_num: number;
  status: "pending" | "processing" | "done" | "error";
}

export interface BookStatus {
  id: string;
  title: string;
  profile: string;
  chapters: ChapterStatus[];
  done: boolean;
}

export interface Entity {
  id: string;
  entity_type: string;
  name: string;
  attrs: Record<string, unknown>;
  source_quote: string | null;
  chapter_id: string | null;
}

export interface Question {
  id: string;
  text: string;
  options: string[];
  difficulty: "easy" | "medium" | "hard";
}

export interface TestResult {
  entity_id: string;
  score: number;
  status: EntityStatus;
  unlocked: string[];
}

export interface ProgressEntry {
  entity_id: string;
  status: EntityStatus;
  score: number | null;
  attempts: number;
}

export interface QASource {
  id: string;
  name: string;
  entity_type: string;
}

export interface TraversalEdge {
  source: string;
  target: string;
  relation_type: string;
}

export interface QAResponse {
  answer: string;
  sources: QASource[];
  traversal_nodes: string[];
  traversal_edges: TraversalEdge[];
  mode: "graphrag" | "vector_fallback";
}
