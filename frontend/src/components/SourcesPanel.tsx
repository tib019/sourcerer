"use client";

import { useRef, useState } from "react";
import type { Citation, DocumentInfo } from "@/lib/types";
import { MAX_PASTE_CHARS, validatePastedText } from "@/lib/validation";

export function SourcesPanel({
  documents,
  activeCitation,
  onUploadFile,
  onPasteText,
  onImportUrl,
  onDeleteDocument,
  onCloseCitation,
  busy,
}: {
  documents: DocumentInfo[];
  activeCitation: Citation | null;
  onUploadFile: (file: File) => void;
  onPasteText: (name: string, text: string) => void;
  onImportUrl: (url: string) => void;
  onDeleteDocument: (doc: DocumentInfo) => void;
  onCloseCitation: () => void;
  busy: boolean;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [showPaste, setShowPaste] = useState(false);
  const [showUrl, setShowUrl] = useState(false);
  const [urlValue, setUrlValue] = useState("");
  const [urlError, setUrlError] = useState<string | null>(null);
  const [pasteName, setPasteName] = useState("");
  const [pasteText, setPasteText] = useState("");
  const [pasteError, setPasteError] = useState<string | null>(null);

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
            onClick={() => {
              setShowPaste((v) => !v);
              setShowUrl(false);
            }}
            disabled={busy}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50
              disabled:opacity-50"
          >
            Text
          </button>
          <button
            onClick={() => {
              setShowUrl((v) => !v);
              setShowPaste(false);
            }}
            disabled={busy}
            data-testid="url-import-toggle"
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50
              disabled:opacity-50"
          >
            Website
          </button>
        </div>
        {showUrl && (
          <form
            className="mt-3 space-y-2"
            onSubmit={(e) => {
              e.preventDefault();
              const url = urlValue.trim();
              if (!/^https?:\/\/.+/.test(url)) {
                setUrlError("Bitte eine vollständige http(s)-URL angeben.");
                return;
              }
              onImportUrl(url);
              setUrlValue("");
              setUrlError(null);
              setShowUrl(false);
            }}
          >
            <input
              value={urlValue}
              onChange={(e) => setUrlValue(e.target.value)}
              placeholder="https://…"
              data-testid="url-input"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            {urlError && (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700" role="alert">
                {urlError}
              </p>
            )}
            <button
              type="submit"
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-white
                hover:bg-slate-700"
            >
              Website importieren
            </button>
          </form>
        )}
        <input
          ref={fileInput}
          type="file"
          accept=".pdf,.txt,.md"
          className="hidden"
          data-testid="file-input"
          disabled={busy}
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
              const error = validatePastedText(pasteName, pasteText);
              if (error) {
                setPasteError(error);
                return;
              }
              onPasteText(pasteName.trim(), pasteText);
              setPasteName("");
              setPasteText("");
              setPasteError(null);
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
            <p className="text-right text-xs text-slate-400">
              {pasteText.length.toLocaleString("de-DE")} /{" "}
              {MAX_PASTE_CHARS.toLocaleString("de-DE")} Zeichen
            </p>
            {pasteError && (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700" role="alert">
                {pasteError}
              </p>
            )}
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
            className={`group flex items-start justify-between rounded-lg p-3 text-sm ${
              activeCitation?.document_id === doc.id ? "bg-indigo-50" : ""
            }`}
          >
            <div className="min-w-0">
              <p className="font-medium text-slate-800">{doc.name}</p>
              <p className="text-xs text-slate-500">
                {doc.page_count} Seite{doc.page_count === 1 ? "" : "n"} ·{" "}
                {doc.chunk_count} Chunks
              </p>
              {doc.source_url && (
                <a
                  href={doc.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block truncate text-xs text-indigo-500 hover:underline"
                  title={doc.source_url}
                >
                  {doc.source_url}
                </a>
              )}
            </div>
            <button
              onClick={() => onDeleteDocument(doc)}
              aria-label={`Quelle ${doc.name} löschen`}
              title="Quelle löschen"
              className="ml-2 text-slate-300 hover:text-red-600 group-hover:text-slate-400"
            >
              ✕
            </button>
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
