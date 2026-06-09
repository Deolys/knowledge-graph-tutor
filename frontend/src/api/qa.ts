import { client } from "./client";
import type { QAResponse } from "../types";

export async function askQuestion(payload: {
  query: string;
  book_id: string;
  session_id?: string;
}): Promise<QAResponse> {
  const { data } = await client.post<QAResponse>("/api/qa", payload);
  return data;
}
