// Типы, синхронные с Pydantic-схемами backend.

export type ConceptStatus =
  | "not_started"
  | "in_progress"
  | "learned"
  | "locked";

export interface GraphNode {
  id: string;
  name: string;
  chapter_id: string;
  status: ConceptStatus;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: "depends_on" | "part_of" | "example_of" | "related_to";
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
  created_at: string;
}

export interface BookListItem {
  id: string;
  title: string;
  filename: string;
  created_at: string;
  chapters_total: number;
  chapters_done: number;
  concepts_count: number;
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
  chapters: ChapterStatus[];
  done: boolean;
}

export interface Concept {
  id: string;
  name: string;
  definition: string;
  formula: string | null;
  quote: string | null;
  chapter_id: string;
}

export interface Question {
  id: string;
  text: string;
  options: string[];
  difficulty: "easy" | "medium" | "hard";
}

export interface TestResult {
  concept_id: string;
  score: number;
  status: ConceptStatus;
  unlocked: string[];
}

export interface ProgressEntry {
  concept_id: string;
  status: ConceptStatus;
  score: number | null;
  attempts: number;
}

export interface QASource {
  id: string;
  name: string;
}

export interface QAResponse {
  answer: string;
  sources: QASource[];
}
