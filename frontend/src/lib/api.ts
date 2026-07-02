import type { ChatResponse, DocumentInfo, Notebook } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function createNotebook(name: string): Promise<Notebook> {
  return request("/notebooks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export function listNotebooks(): Promise<Notebook[]> {
  return request("/notebooks");
}

export function listDocuments(notebookId: string): Promise<DocumentInfo[]> {
  return request(`/notebooks/${notebookId}/documents`);
}

export function uploadFile(notebookId: string, file: File): Promise<DocumentInfo> {
  const form = new FormData();
  form.append("file", file);
  return request(`/notebooks/${notebookId}/documents`, { method: "POST", body: form });
}

export function pasteText(
  notebookId: string,
  name: string,
  text: string,
): Promise<DocumentInfo> {
  return request(`/notebooks/${notebookId}/documents/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, text }),
  });
}

export function askQuestion(notebookId: string, question: string): Promise<ChatResponse> {
  return request(`/notebooks/${notebookId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}
