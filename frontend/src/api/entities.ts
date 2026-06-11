import { client } from "./client";
import type { Entity, Question } from "../types";

export async function getEntity(entityId: string): Promise<Entity> {
  const { data } = await client.get<Entity>(`/api/entities/${entityId}`);
  return data;
}

export async function getQuestions(entityId: string): Promise<Question[]> {
  const { data } = await client.get<Question[]>(
    `/api/entities/${entityId}/questions`,
  );
  return data;
}
