# D1 · Komponenten-/Architekturdiagramm

Getrenntes Frontend + eigenständiger Python-RAG-Service ([ADR-001](adr/ADR-001-frontend-backend-split.md)).

```mermaid
flowchart LR
    subgraph Vercel
        FE["Next.js Frontend<br/>Upload · Chat · Quellen-Panel"]
    end

    subgraph Railway["Railway (Docker)"]
        API["FastAPI<br/>REST-API"]
        FETCH["WebPageFetcher<br/>SSRF-Guard: Schema/IP-Block,<br/>Redirect-Check, 5-MB-Cap (ADR-009)"]
        ING["DocumentIngestor<br/>Extract → Chunk → Embed → Store"]
        RAG["RAGPipeline<br/>Retrieve → Prompt → Answer → Citations"]
        STUDIO["StudioService<br/>Startfragen · Bericht · Karten · Quiz ·<br/>Mindmap (Server baut Mermaid, ADR-010)"]
        AUDIO["AudioOverviewService<br/>Summary → TTS"]
        API --> FETCH
        FETCH -- "extrahierter Text" --> ING
        API --> ING
        API --> RAG
        API --> STUDIO
        API --> AUDIO
    end

    subgraph Extern["Externe Dienste"]
        PC[("Pinecone<br/>Vektor-Index")]
        SB[("Supabase<br/>Postgres, RLS aktiv")]
        OAI["OpenAI<br/>GPT-4o · text-embedding-3-small · tts-1"]
        WEB["Öffentliches Web<br/>(nur http/https, keine internen Ziele)"]
    end

    User((User)) --> FE
    FE -- "REST (JSON / multipart)" --> API
    FETCH -- "GET (Timeout, UA, Größen-Cap)" --> WEB
    ING -- "Embeddings" --> OAI
    ING -- "Upsert Vektoren + Metadaten" --> PC
    ING -- "Dokument + Chunks" --> SB
    RAG -- "Query-Embedding · Chat" --> OAI
    RAG -- "Top-k Query" --> PC
    STUDIO -- "Quellen-Querschnitt" --> SB
    STUDIO -- "strukturierte JSON-Outputs" --> OAI
    AUDIO -- "Summary · TTS" --> OAI
```

**Datenfluss:** Upload → Extract (pypdf) → Chunk (~800 Tokens, 15 % Overlap) → Embed →
Vektor-Store (Metadaten: doc_id, chunk_index, page, text) → Chat: Query-Embedding →
Top-k Retrieval → Prompt mit nummerierten Quellen-Chunks → Antwort mit `[n]`-Zitaten →
Frontend mappt Zitate auf Chunks.

**Provider-Grenze:** OpenAI, Pinecone und Supabase liegen hinter Interfaces
([ADR-006](adr/ADR-006-provider-abstraction.md)); im Fake-Modus ersetzt sie ein
deterministisches In-Memory-Setup (Tests, CI, Offline-Demo).
