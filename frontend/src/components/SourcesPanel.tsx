"use client";

import { useRef, useState } from "react";
import type { Citation, DocumentInfo } from "@/lib/types";

export function SourcesPanel({
  documents,
  activeCitation,
  onUploadFile,
  onPasteText,
  onCloseCitation,
  busy,
}: {
  documents: DocumentInfo[];
  activeCitation: Citation | null;
  onUploadFile: (file: File) => void;
  onPasteText: (name: string, text: string) => void;
  onCloseCitation: () => void;
  busy: boolean;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [showPaste, setShowPaste] = useState(false);
  const [pasteName, setPasteName] = useState("");
  const [pasteText, setPasteText] = useState("");

  return (
    <aside className="flex h-full w-80 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Quellen
        </h2>
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => fileInput.current?.click()}
            disabled={busy}
            className="flex-1 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white
              hover:bg-indigo-700 disabled:opacity-50"
          >
            {busy ? "Verarbeite…" : "Datei hochladen"}
          </button>
          <button
            onClick={() => setShowPaste((v) => !v)}
            disabled={busy}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50
              disabled:opacity-50"
          >
            Text
          </button>
        </div>
        <input
          ref={fileInput}
          type="file"
          accept=".pdf,.txt,.md"
          className="hidden"
          data-testid="file-input"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUploadFile(file);
            e.target.value = "";
          }}
        />
        {showPaste && (
          <form
            className="mt-3 space-y-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (!pasteName.trim() || !pasteText.trim()) return;
              onPasteText(pasteName.trim(), pasteText);
              setPasteName("");
              setPasteText("");
              setShowPaste(false);
            }}
          >
            <input
              value={pasteName}
              onChange={(e) => setPasteName(e.target.value)}
              placeholder="Name der Quelle"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder="Text einfügen…"
              rows={5}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="submit"
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-white
                hover:bg-slate-700"
            >
              Als Quelle hinzufügen
            </button>
          </form>
        )}
      </div>

      <ul className="flex-1 overflow-y-auto p-2" data-testid="document-list">
        {documents.length === 0 && (
          <li className="p-3 text-sm text-slate-400">
            Noch keine Quellen — lade ein PDF hoch oder füge Text ein.
          </li>
        )}
        {documents.map((doc) => (
          <li
            key={doc.id}
            className={`rounded-lg p-3 text-sm ${
              activeCitation?.document_id === doc.id ? "bg-indigo-50" : ""
            }`}
          >
            <p className="font-medium text-slate-800">{doc.name}</p>
            <p className="text-xs text-slate-500">
              {doc.page_count} Seite{doc.page_count === 1 ? "" : "n"} ·{" "}
              {doc.chunk_count} Chunks
            </p>
          </li>
        ))}
      </ul>

      {activeCitation && (
        <div
          className="border-t border-indigo-200 bg-indigo-50 p-4"
          data-testid="citation-detail"
        >
          <div className="flex items-start justify-between">
            <h3 className="text-sm font-semibold text-indigo-900">
              Zitat [{activeCitation.n}]
            </h3>
            <button
              onClick={onCloseCitation}
              aria-label="Zitat schließen"
              className="text-indigo-400 hover:text-indigo-700"
            >
              ✕
            </button>
          </div>
          <p className="mt-1 text-xs text-indigo-700">
            {activeCitation.document_name} · Seite {activeCitation.page} · Chunk{" "}
            {activeCitation.chunk_index}
          </p>
          <blockquote className="mt-2 max-h-48 overflow-y-auto border-l-2 border-indigo-400 pl-3 text-sm text-slate-700">
            {activeCitation.text}
          </blockquote>
        </div>
      )}
    </aside>
  );
}
