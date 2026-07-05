# D6 · Deployment-Diagramm

```mermaid
flowchart TB
    subgraph GH["GitHub"]
        REPO[Repo tib019/sourcerer]
        CI["Actions: lint → alle Testebenen<br/>(rot = kein Merge)"]
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

    CLI["Manueller Deploy nach grüner CI:<br/>vercel deploy --prod · railway up"]
    CI -.->|"Gate: erst grün, dann deployen"| CLI
    CLI --> FE
    CLI --> BE
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
  Push. Deploys erfolgen manuell per CLI (`railway up`, `vercel deploy --prod`) —
  Regel: nur bei grünem `main` (Auto-Deploy wäre der nächste Ausbauschritt).
