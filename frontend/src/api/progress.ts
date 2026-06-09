import { client } from "./client";
import type { ProgressEntry, TestResult } from "../types";

export async function submitTest(payload: {
  session_id: string;
  concept_id: string;
  answers: Record<string, number>;
}): Promise<TestResult> {
  const { data } = await client.post<TestResult>("/api/progress", payload);
  return data;
}

export async function getProgress(
  sessionId: string,
): Promise<ProgressEntry[]> {
  const { data } = await client.get<ProgressEntry[]>(
    `/api/progress/${sessionId}`,
  );
  return data;
}
