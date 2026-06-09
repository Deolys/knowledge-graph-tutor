import { client } from "./client";
import type { Book, BookStatus, Graph } from "../types";

export async function uploadBook(file: File): Promise<Book> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post<Book>("/api/books/upload", form);
  return data;
}

export async function getBookStatus(bookId: string): Promise<BookStatus> {
  const { data } = await client.get<BookStatus>(`/api/books/${bookId}`);
  return data;
}

export async function getGraph(
  bookId: string,
  sessionId?: string,
): Promise<Graph> {
  const { data } = await client.get<Graph>(`/api/books/${bookId}/graph`, {
    params: sessionId ? { session_id: sessionId } : undefined,
  });
  return data;
}
