# D3 · Sequenzdiagramm — „Frage → zitierte Antwort"

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Frontend (Next.js)
    participant API as FastAPI
    participant R as Retriever
    participant E as EmbeddingProvider
    participant VS as VectorStore
    participant PB as PromptBuilder
    participant LLM as LLMProvider
    participant CM as CitationMapper

    U->>FE: Frage eingeben
    FE->>API: POST /notebooks/{id}/chat { question }
    API->>R: retrieve(question, notebook_id)
    R->>E: embed([question])
    E-->>R: query_vector
    R->>VS: query(query_vector, top_k, namespace=notebook_id)
    VS-->>R: Top-k ScoredChunks
    API->>PB: build(question, chunks)
    PB-->>API: Messages (System + nummerierte Quellen [1..k])
    API->>LLM: complete(messages)
    LLM-->>API: Antworttext mit [n]-Markern
    API->>CM: map(answer_text, chunks)
    CM-->>API: ChatAnswer { text, citations[] }
    API-->>FE: JSON { answer, citations }
    FE-->>U: Antwort mit klickbaren [n]-Badges
    U->>FE: Klick auf [2]
    FE-->>U: Quellen-Panel: Dokument, Seite, Original-Textstelle
```

Sonderfall **keine belastbare Quelle**: Findet das Retrieval nichts Relevantes bzw. steht
die Antwort nicht in den Chunks, antwortet das System „Dazu steht nichts in den Quellen."
— ohne Zitate, ohne Halluzination (abgesichert im Groundedness-Eval, `tests/eval/`).
