# API-Referenz

Vollständige Referenz aller Endpoints. Interaktiv: `/docs` (Swagger UI) auf dem
laufenden Backend. Alle Fehler haben die Form `{"detail": "<Meldung>"}`.

## Fehlercodes (überall gleich gemappt)

| Code | Bedeutung | Ausgelöst durch |
|---|---|---|
| 400 | `UnsupportedFileTypeError` / `UrlNotAllowedError` | unbekannter Dateityp · URL-Schema ≠ http/https oder Ziel im internen Netz (SSRF-Block, [ADR-009](adr/ADR-009-url-import-ssrf.md)) |
| 404 | `NotebookNotFoundError` / `DocumentNotFoundError` | unbekannte Notebook-/Dokument-ID (auch: Dokument gehört zu anderem Notebook) |
| 413 | `FileTooLargeError` | Upload über dem Limit (Default 10 MB) |
| 422 | `EmptyDocumentError` / `UrlFetchFailedError` | kein extrahierbarer Text · leeres Notebook für Generatoren · URL: HTTP-Fehler, falscher Content-Type, > 5 MB |
| 502 | `GenerationError` | LLM lieferte kein schema-konformes JSON (Studio) |

## Notebooks

| Methode + Pfad | Request | Response |
|---|---|---|
| `POST /notebooks` | `{"name": str}` | `201 {"id", "name"}` |
| `GET /notebooks` | – | `200 [{"id", "name"}]` |
| `DELETE /notebooks/{id}` | – | `204` — löscht Metadaten (FK CASCADE) **und** Vektor-Namespace |
| `POST /notebooks/{id}/reset` | – | `204` — alle Quellen weg, Notebook bleibt |

## Quellen (Dokumente)

| Methode + Pfad | Request | Response |
|---|---|---|
| `POST /notebooks/{id}/documents` | multipart `file` (PDF/TXT/MD) | `201 DocumentResponse` |
| `POST /notebooks/{id}/documents/text` | `{"name": str, "text": str}` | `201 DocumentResponse` |
| `POST /notebooks/{id}/documents/url` | `{"url": str}` | `201 DocumentResponse` (mit `source_url`) — Schutzmaßnahmen siehe [ADR-009](adr/ADR-009-url-import-ssrf.md) |
| `GET /notebooks/{id}/documents` | – | `200 [DocumentResponse]` |
| `DELETE /notebooks/{id}/documents/{doc_id}` | – | `204` — löscht Vektoren **dieses** Dokuments (Namespace bleibt) + DB-Zeilen |

`DocumentResponse = {"id", "name", "media_type", "page_count", "chunk_count", "source_url"?}`

## Chat

| Methode + Pfad | Request | Response |
|---|---|---|
| `POST /notebooks/{id}/chat` | `{"question": str}` | `200 {"answer": str, "citations": [Citation]}` |

`Citation = {"n", "document_id", "document_name", "chunk_index", "page", "text"}` —
`[n]`-Marker im Antworttext verweisen auf diese Liste ([ADR-005](adr/ADR-005-citation-format.md)).
Ohne belastbare Quelle antwortet das System exakt `"Dazu steht nichts in den Quellen."`
mit leerer Zitatliste.

## Studio-Generatoren (alle gegroundet, leeres Notebook → 422 ohne LLM-Call)

| Methode + Pfad | Response |
|---|---|
| `POST /notebooks/{id}/suggested-questions` | `{"questions": [str]}` (3–4) |
| `POST /notebooks/{id}/report` | `{"title", "sections": [{"heading", "content", "citations": [int]}], "sources": [Citation]}` |
| `POST /notebooks/{id}/flashcards` | `{"cards": [{"front", "back", "citation"?}], "sources": [Citation]}` (8–12) |
| `POST /notebooks/{id}/quiz` | `{"questions": [{"question", "options": [str], "answer_index", "citation"?}], "sources": [Citation]}` |
| `POST /notebooks/{id}/mindmap` | `{"mermaid": str}` — serverseitig gebaut und bereinigt ([ADR-010](adr/ADR-010-mindmap-fallback.md)) |

`citations`/`citation` sind Quellen-Nummern und verweisen in die `sources`-Liste —
ungültige Referenzen werden serverseitig verworfen.

## Audio

| Methode + Pfad | Response |
|---|---|
| `POST /notebooks/{id}/audio-overview` | `{"summary": str, "media_type": "audio/mpeg"\|"audio/wav", "audio_base64": str}` |

## Sonstiges

| Methode + Pfad | Response |
|---|---|
| `GET /health` | `{"status": "ok", "providers": "fake"\|"openai"}` |
