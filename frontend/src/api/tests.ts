import { client } from "./client";
import type {
  CreateTestPayload,
  TestDetail,
  TestListItem,
  TestSubmitResult,
} from "../types";

export async function listTests(sessionId: string): Promise<TestListItem[]> {
  const { data } = await client.get<TestListItem[]>("/api/tests", {
    params: { session_id: sessionId },
  });
  return data;
}

export async function createTest(
  payload: CreateTestPayload,
): Promise<TestListItem> {
  const { data } = await client.post<TestListItem>("/api/tests", payload);
  return data;
}

export async function getTest(testId: string): Promise<TestDetail> {
  const { data } = await client.get<TestDetail>(`/api/tests/${testId}`);
  return data;
}

export async function submitTest(
  testId: string,
  answers: Record<string, number>,
): Promise<TestSubmitResult> {
  const { data } = await client.post<TestSubmitResult>(
    `/api/tests/${testId}/submit`,
    { answers },
  );
  return data;
}

export async function deleteTest(testId: string): Promise<void> {
  await client.delete(`/api/tests/${testId}`);
}
