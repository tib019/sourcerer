import type { AudioOverviewData, ChatResponse, DocumentInfo, Notebook } from "./types";

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

export function createAudioOverview(notebookId: string): Promise<AudioOverviewData> {
  return request(`/notebooks/${notebookId}/audio-overview`, { method: "POST" });
}

async function requestVoid(path: string, init?: RequestInit): Promise<void> {
  const response = await fetch(`${BASE}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${response.status}`);
  }
}

export function deleteDocument(notebookId: string, documentId: string): Promise<void> {
  return requestVoid(`/notebooks/${notebookId}/documents/${documentId}`, {
    method: "DELETE",
  });
}

export function resetNotebook(notebookId: string): Promise<void> {
  return requestVoid(`/notebooks/${notebookId}/reset`, { method: "POST" });
}

export function deleteNotebook(notebookId: string): Promise<void> {
  return requestVoid(`/notebooks/${notebookId}`, { method: "DELETE" });
}

export function askQuestion(notebookId: string, question: string): Promise<ChatResponse> {
  return request(`/notebooks/${notebookId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}
