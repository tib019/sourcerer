# D5 · ER-Diagramm — Metadaten-Schema (Supabase / Postgres)

```mermaid
erDiagram
    NOTEBOOKS ||--o{ DOCUMENTS : "enthält"
    DOCUMENTS ||--o{ CHUNKS : "zerlegt in"

    NOTEBOOKS {
        uuid id PK
        text name
        timestamptz created_at
    }

    DOCUMENTS {
        uuid id PK
        uuid notebook_id FK
        text name
        text media_type "application/pdf | text/plain"
        int page_count
        int chunk_count
        text storage_path "Herkunfts-URL bei Website-Import (sonst null)"
        timestamptz created_at
    }

    CHUNKS {
        uuid id PK "= Vektor-ID im Vektor-Store"
        uuid document_id FK
        int chunk_index
        int page "Startseite des Chunks"
        text text "Original-Textstelle (für Zitat-Anzeige)"
    }
```

**Doppelrolle der CHUNKS-Zeile:** dieselben Felder liegen als Metadaten am Vektor im
Vektor-Store (Pinecone) — das Retrieval liefert damit direkt alles, was der
`CitationMapper` und das Quellen-Panel brauchen, ohne zweiten Lookup.
Der Vektor-Namespace ist die `notebook_id` → Quellen sind pro Notebook isoliert.

**Demo-Scope:** im MVP bedient eine In-Memory-Repository-Implementierung dieses Schema;
die Supabase-Implementierung ist dieselbe Schnittstelle (siehe NOTES.md §6).
