"use client";

import { useCallback, useEffect, useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { SourcesPanel } from "@/components/SourcesPanel";
import { StudioPanel } from "@/components/StudioPanel";
import * as api from "@/lib/api";
import type { ChatMessage, Citation, DocumentInfo, Notebook } from "@/lib/types";

export default function Home() {
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [notebook, setNotebook] = useState<Notebook | null>(null);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggested, setSuggested] = useState<string[]>([]);

  const clearConversation = useCallback(() => {
    setMessages([]);
    setActiveCitation(null);
    setSuggested([]);
  }, []);

  const activateNotebook = useCallback(
    async (target: Notebook) => {
      setNotebook(target);
      clearConversation();
      setDocuments(await api.listDocuments(target.id));
    },
    [clearConversation],
  );

  // Beim Laden: Notebooks holen, erstes aktivieren (oder eines anlegen).
  useEffect(() => {
    (async () => {
      try {
        const existing = await api.listNotebooks();
        const list = existing.length
          ? existing
          : [await api.createNotebook("Mein Notebook")];
        setNotebooks(list);
        await activateNotebook(list[0]);
      } catch {
        setError(
          "Backend nicht erreichbar — läuft der RAG-Service? (uvicorn app.main:app)",
        );
      }
    })();
  }, [activateNotebook]);

  const refreshDocuments = useCallback(async (notebookId: string) => {
    setDocuments(await api.listDocuments(notebookId));
  }, []);

  // Startfragen: nach Upload bzw. bei leerem Chat einmal pro Quellen-Stand laden.
  useEffect(() => {
    if (!notebook || documents.length === 0 || messages.length > 0) return;
    let cancelled = false;
    api
      .suggestedQuestions(notebook.id)
      .then((data) => {
        if (!cancelled) setSuggested(data.questions);
      })
      .catch(() => {
        if (!cancelled) setSuggested([]); // Chips sind nice-to-have, kein Fehlerbanner
      });
    return () => {
      cancelled = true;
    };
  }, [notebook, documents, messages.length]);

  const run = async (action: () => Promise<void>) => {
    setError(null);
    try {
      await action();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Aktion fehlgeschlagen");
    }
  };

  const handleUpload = async (file: File) => {
    if (!notebook) return;
    setUploading(true);
    await run(async () => {
      await api.uploadFile(notebook.id, file);
      await refreshDocuments(notebook.id);
    });
    setUploading(false);
  };

  const handlePaste = async (name: string, text: string) => {
    if (!notebook) return;
    setUploading(true);
    await run(async () => {
      await api.pasteText(notebook.id, name, text);
      await refreshDocuments(notebook.id);
    });
    setUploading(false);
  };

  const handleAsk = async (question: string) => {
    if (!notebook) return;
    setMessages((m) => [...m, { role: "user", text: question, citations: [] }]);
    setAsking(true);
    await run(async () => {
      const response = await api.askQuestion(notebook.id, question);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: response.answer, citations: response.citations },
      ]);
    });
    setAsking(false);
  };

  const handleDeleteDocument = async (doc: DocumentInfo) => {
    if (!notebook) return;
    if (!window.confirm(`Quelle „${doc.name}" endgültig löschen?`)) return;
    await run(async () => {
      await api.deleteDocument(notebook.id, doc.id);
      if (activeCitation?.document_id === doc.id) setActiveCitation(null);
      await refreshDocuments(notebook.id);
    });
  };

  const handleCreateNotebook = async () => {
    const name = window.prompt("Name des neuen Notebooks:", "Neues Notebook");
    if (!name?.trim()) return;
    await run(async () => {
      const created = await api.createNotebook(name.trim());
      setNotebooks((list) => [...list, created]);
      await activateNotebook(created);
    });
  };

  const handleSelectNotebook = async (id: string) => {
    const target = notebooks.find((n) => n.id === id);
    if (target && target.id !== notebook?.id) await run(() => activateNotebook(target));
  };

  const handleResetNotebook = async () => {
    if (!notebook) return;
    if (!window.confirm(`Alle Quellen aus „${notebook.name}" entfernen? Das Notebook bleibt.`))
      return;
    await run(async () => {
      await api.resetNotebook(notebook.id);
      clearConversation();
      await refreshDocuments(notebook.id);
    });
  };

  const handleDeleteNotebook = async () => {
    if (!notebook) return;
    if (!window.confirm(`Notebook „${notebook.name}" samt aller Quellen löschen?`)) return;
    await run(async () => {
      await api.deleteNotebook(notebook.id);
      const remaining = notebooks.filter((n) => n.id !== notebook.id);
      const list = remaining.length
        ? remaining
        : [await api.createNotebook("Mein Notebook")];
      setNotebooks(list);
      await activateNotebook(list[0]);
    });
  };

  return (
    <main className="flex h-screen flex-col">
      <header className="flex items-center justify-between gap-3 border-b border-slate-200 bg-white px-6 py-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🧙‍♂️</span>
          <h1 className="text-lg font-bold tracking-tight">Sourcerer</h1>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={notebook?.id ?? ""}
            onChange={(e) => handleSelectNotebook(e.target.value)}
            data-testid="notebook-select"
            className="max-w-48 rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
          >
            {notebooks.map((n) => (
              <option key={n.id} value={n.id}>
                {n.name}
              </option>
            ))}
          </select>
          <button
            onClick={handleCreateNotebook}
            data-testid="notebook-create"
            title="Neues Notebook"
            className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm hover:bg-slate-50"
          >
            ＋
          </button>
          <button
            onClick={handleResetNotebook}
            disabled={!notebook || documents.length === 0}
            data-testid="notebook-reset"
            title="Alle Quellen entfernen, Notebook behalten"
            className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-40"
          >
            ⟲
          </button>
          <button
            onClick={handleDeleteNotebook}
            disabled={!notebook}
            data-testid="notebook-delete"
            title="Notebook löschen"
            className="rounded-lg border border-red-200 px-2.5 py-1.5 text-sm text-red-600 hover:bg-red-50 disabled:opacity-40"
          >
            🗑
          </button>
        </div>
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
          onDeleteDocument={handleDeleteDocument}
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
          suggestedQuestions={suggested}
        />
        <StudioPanel
          notebookId={notebook?.id ?? null}
          hasSources={documents.length > 0}
          onCitationClick={setActiveCitation}
          activeCitation={activeCitation}
        />
      </div>
    </main>
  );
}
