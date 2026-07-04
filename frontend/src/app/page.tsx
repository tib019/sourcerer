"use client";

import { useCallback, useEffect, useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { SourcesPanel } from "@/components/SourcesPanel";
import * as api from "@/lib/api";
import type { ChatMessage, Citation, DocumentInfo, Notebook } from "@/lib/types";

function toAudioUrl(base64: string, mediaType: string): string {
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  return URL.createObjectURL(new Blob([bytes], { type: mediaType }));
}

export default function Home() {
  const [notebook, setNotebook] = useState<Notebook | null>(null);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audio, setAudio] = useState<{ url: string; summary: string } | null>(null);
  const [audioLoading, setAudioLoading] = useState(false);

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

  const handleAudioOverview = async () => {
    if (!notebook) return;
    setAudioLoading(true);
    setError(null);
    try {
      const data = await api.createAudioOverview(notebook.id);
      setAudio((old) => {
        if (old) URL.revokeObjectURL(old.url);
        return { url: toAudioUrl(data.audio_base64, data.media_type), summary: data.summary };
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Audio-Overview fehlgeschlagen");
    } finally {
      setAudioLoading(false);
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
        <button
          onClick={handleAudioOverview}
          disabled={!notebook || documents.length === 0 || audioLoading}
          data-testid="audio-overview-button"
          className="rounded-lg border border-indigo-300 px-3 py-1.5 text-sm text-indigo-700
            hover:bg-indigo-50 disabled:opacity-40"
        >
          {audioLoading ? "Erzeuge Audio…" : "🎧 Audio-Overview"}
        </button>
      </header>

      {audio && (
        <div
          className="flex items-center gap-4 border-b border-indigo-200 bg-indigo-50 px-6 py-2"
          data-testid="audio-overview-player"
        >
          <audio controls src={audio.url} className="h-9" />
          <p className="line-clamp-2 flex-1 text-xs text-indigo-900">{audio.summary}</p>
          <button
            aria-label="Audio schließen"
            onClick={() => {
              URL.revokeObjectURL(audio.url);
              setAudio(null);
            }}
            className="text-indigo-400 hover:text-indigo-700"
          >
            ✕
          </button>
        </div>
      )}

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
