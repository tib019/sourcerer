"use client";

import { useCallback, useEffect, useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { SourcesPanel } from "@/components/SourcesPanel";
import * as api from "@/lib/api";
import type { ChatMessage, Citation, DocumentInfo, Notebook } from "@/lib/types";

export default function Home() {
  const [notebook, setNotebook] = useState<Notebook | null>(null);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Demo-Scope: ein Notebook, beim ersten Laden angelegt bzw. wiederverwendet.
  useEffect(() => {
    (async () => {
      try {
        const existing = await api.listNotebooks();
        const nb = existing[0] ?? (await api.createNotebook("Mein Notebook"));
        setNotebook(nb);
        setDocuments(await api.listDocuments(nb.id));
      } catch {
        setError(
          "Backend nicht erreichbar — läuft der RAG-Service? (uvicorn app.main:app)",
        );
      }
    })();
  }, []);

  const refreshDocuments = useCallback(async (notebookId: string) => {
    setDocuments(await api.listDocuments(notebookId));
  }, []);

  const handleUpload = async (file: File) => {
    if (!notebook) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadFile(notebook.id, file);
      await refreshDocuments(notebook.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload fehlgeschlagen");
    } finally {
      setUploading(false);
    }
  };

  const handlePaste = async (name: string, text: string) => {
    if (!notebook) return;
    setUploading(true);
    setError(null);
    try {
      await api.pasteText(notebook.id, name, text);
      await refreshDocuments(notebook.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hinzufügen fehlgeschlagen");
    } finally {
      setUploading(false);
    }
  };

  const handleAsk = async (question: string) => {
    if (!notebook) return;
    setMessages((m) => [...m, { role: "user", text: question, citations: [] }]);
    setAsking(true);
    setError(null);
    try {
      const response = await api.askQuestion(notebook.id, question);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: response.answer, citations: response.citations },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Anfrage fehlgeschlagen");
    } finally {
      setAsking(false);
    }
  };

  return (
    <main className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🧙‍♂️</span>
          <h1 className="text-lg font-bold tracking-tight">Sourcerer</h1>
          <span className="text-sm text-slate-400">
            {notebook ? `· ${notebook.name}` : ""}
          </span>
        </div>
        <p className="hidden text-xs text-slate-400 sm:block">
          Keine Antwort ohne Quelle.
        </p>
      </header>

      {error && (
        <div className="border-b border-red-200 bg-red-50 px-6 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        <SourcesPanel
          documents={documents}
          activeCitation={activeCitation}
          onUploadFile={handleUpload}
          onPasteText={handlePaste}
          onCloseCitation={() => setActiveCitation(null)}
          busy={uploading || !notebook}
        />
        <ChatPanel
          messages={messages}
          onAsk={handleAsk}
          onCitationClick={setActiveCitation}
          activeCitation={activeCitation}
          busy={asking}
          hasSources={documents.length > 0}
        />
      </div>
    </main>
  );
}
