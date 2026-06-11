import { client } from "./client";
import type { Book, BookListItem, BookStatus, Graph } from "../types";

export async function listBooks(): Promise<BookListItem[]> {
  const { data } = await client.get<BookListItem[]>("/api/books");
  return data;
}

export async function uploadBook(
  file: File,
  profile: string,
): Promise<Book> {
  const form = new FormData();
  form.append("file", file);
  form.append("profile", profile);
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
