# D4 · Aktivitätsdiagramm — Ingest-Pipeline

```mermaid
flowchart TD
    A([Upload: Datei / Paste / Website-Import*]) --> B{Validierung}
    B -- "Typ nicht erlaubt" --> E1[[400: nur PDF / Plaintext]]
    B -- "zu groß (> Limit)" --> E2[[413: Datei zu groß]]
    B -- ok --> C[TextExtractor: Rohtext + Seiten]
    C --> D{Text vorhanden?}
    D -- "leer / nur Bilder" --> E3[[422: kein extrahierbarer Text]]
    D -- ja --> F["Chunker: ~800 Tokens, 15 % Overlap,<br/>Schnitt an Satzgrenzen"]
    F --> G[EmbeddingProvider: Batch-Embed]
    G -- "Provider-Fehler" --> E4[[502: Embedding fehlgeschlagen,<br/>kein Teil-Zustand im Store]]
    G --> H["VectorStore.upsert<br/>(doc_id, chunk_index, page, text)"]
    H --> I[Metadaten registrieren:<br/>Dokument im Notebook]
    I --> Z([201: Dokument bereit für Chat])
```

Fehlerpfade sind Teil des Vertrags: Upload-Validierung (Typ-Whitelist, Größenlimit),
leere PDFs werden abgewiesen statt stumm 0 Chunks zu erzeugen, und ein Metadaten-Fehler
nach dem Vektor-Upsert rollt die Vektoren zurück (kein halb-ingestierter Zustand).

\* Der Website-Import durchläuft VOR diesem Diagramm den `WebPageFetcher` mit
SSRF-Guard und Extraktion ([ADR-009](adr/ADR-009-url-import-ssrf.md)) — der
extrahierte Text kommt dann als Plaintext in genau diesen Pfad.
