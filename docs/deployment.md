# D6 · Deployment-Diagramm

```mermaid
flowchart TB
    subgraph GH["GitHub"]
        REPO[Repo tib019/sourcerer]
        CI["Actions: lint → test → deploy<br/>(rot = kein Merge)"]
        REPO --> CI
    end

    subgraph Vercel
        FE["Next.js Frontend<br/>ENV: NEXT_PUBLIC_API_URL"]
    end

    subgraph Railway
        BE["FastAPI im Docker-Container<br/>ENV: OPENAI_API_KEY, PINECONE_API_KEY,<br/>SUPABASE_URL, SUPABASE_KEY (nur server-seitig)"]
    end

    subgraph Managed["Managed Services"]
        PC[("Pinecone")]
        SB[("Supabase")]
        OAI["OpenAI API"]
    end

    CI -- "Deploy bei grünem main" --> FE
    CI -- "Docker Build + Deploy" --> BE
    Browser((Browser)) -- HTTPS --> FE
    FE -- "HTTPS REST" --> BE
    BE --> PC
    BE --> SB
    BE --> OAI
```

- **Secrets** liegen ausschließlich in Railway-Env-Variablen (server-seitig); das
  Frontend kennt nur die API-URL.
- **CORS:** Backend erlaubt genau den Vercel-Origin.
- **CI-Gate:** Lint + alle Testebenen (unit, math, eval, TS-unit, E2E) laufen bei jedem
  Push; Deploy nur bei grünem `main`.
