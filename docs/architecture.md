# D1 · Komponenten-/Architekturdiagramm

Getrenntes Frontend + eigenständiger Python-RAG-Service ([ADR-001](adr/ADR-001-frontend-backend-split.md)).

```mermaid
flowchart LR
    subgraph Vercel
        FE["Next.js Frontend<br/>Upload · Chat · Quellen-Panel"]
    end

    subgraph Railway["Railway (Docker)"]
        API["FastAPI<br/>REST-API"]
        ING["DocumentIngestor<br/>Extract → Chunk → Embed → Store"]
        RAG["RAGPipeline<br/>Retrieve → Prompt → Answer → Citations"]
        API --> ING
        API --> RAG
    end

    subgraph Extern["Externe Dienste"]
        PC[("Pinecone<br/>Vektor-Index")]
        SB[("Supabase<br/>Storage + Postgres")]
        OAI["OpenAI<br/>GPT-4o · text-embedding-3-small"]
    end

    User((User)) --> FE
    FE -- "REST (JSON / multipart)" --> API
    ING -- "Embeddings" --> OAI
    ING -- "Upsert Vektoren + Metadaten" --> PC
    ING -- "Dokument + Metadaten" --> SB
    RAG -- "Query-Embedding · Chat" --> OAI
    RAG -- "Top-k Query" --> PC
```

**Datenfluss:** Upload → Extract (pypdf) → Chunk (~800 Tokens, 15 % Overlap) → Embed →
Vektor-Store (Metadaten: doc_id, chunk_index, page, text) → Chat: Query-Embedding →
Top-k Retrieval → Prompt mit nummerierten Quellen-Chunks → Antwort mit `[n]`-Zitaten →
Frontend mappt Zitate auf Chunks.

**Provider-Grenze:** OpenAI, Pinecone und Supabase liegen hinter Interfaces
([ADR-006](adr/ADR-006-provider-abstraction.md)); im Fake-Modus ersetzt sie ein
deterministisches In-Memory-Setup (Tests, CI, Offline-Demo).
