import { client } from "./client";
import type { Concept, Question } from "../types";

export async function getConcept(conceptId: string): Promise<Concept> {
  const { data } = await client.get<Concept>(`/api/concepts/${conceptId}`);
  return data;
}

export async function getQuestions(conceptId: string): Promise<Question[]> {
  const { data } = await client.get<Question[]>(
    `/api/concepts/${conceptId}/questions`,
  );
  return data;
}
