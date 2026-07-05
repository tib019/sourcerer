# Setup & Entwicklung

## In 30 Sekunden starten (ohne Keys)

```bash
# Backend (Terminal 1)
cd backend && python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt      # Windows | Unix: .venv/bin/pip
.venv\Scripts\python -m uvicorn app.main:app --port 8000

# Frontend (Terminal 2)
cd frontend && npm install && npm run dev               # → http://localhost:3000
```

Ohne Konfiguration läuft `SOURCERER_PROVIDERS=fake`: deterministische Provider für
Embeddings, LLM, TTS und Vektor-Store — der komplette Flow (Upload → zitierte
Antwort → Studio → Audio) funktioniert offline, ohne Keys, ohne Kosten.

## Mit echten Providern (openai-Modus)

`backend/.env` anlegen (Vorlage: `.env.example`) und `SOURCERER_PROVIDERS=openai`
setzen. Die Composition Root ([app/main.py](../backend/app/main.py)) wählt dann
OpenAI + Pinecone + Supabase.

## Env-Variablen (nur Namen — Werte gehören NIE ins Repo)

| Variable | Beschreibung |
|---|---|
| `SOURCERER_PROVIDERS` | `fake` (Default, offline) oder `openai` |
| `OPENAI_API_KEY` | OpenAI (Chat GPT-4o, Embeddings, TTS) — nur openai-Modus |
| `PINECONE_API_KEY` | Pinecone-Vektor-Index — nur openai-Modus |
| `PINECONE_INDEX` | Indexname (Default `sourcerer`; dim 1536, metric cosine) |
| `SUPABASE_URL` | Supabase-Projekt-URL — nur openai-Modus |
| `SUPABASE_KEY` | Supabase **Service-Role-Key** (RLS aktiv, anon ist gesperrt) |
| `SOURCERER_CHUNK_SIZE` | Chunk-Größe in Tokens (Default 800) |
| `SOURCERER_CHUNK_OVERLAP` | Overlap in Tokens (Default 120 ≈ 15 %) |
| `SOURCERER_TOP_K` | Retrieval-Treffer pro Frage (Default 6) |
| `SOURCERER_MIN_SCORE` | Override für den Retrieval-Floor (Default siehe ADR-004) |
| `SOURCERER_MAX_UPLOAD_BYTES` | Upload-Limit (Default 10 MB) |
| `SOURCERER_CORS_ORIGINS` | erlaubte Frontend-Origins, kommagetrennt |
| `PORT` | Bind-Port des Backends (Railway injiziert; Default 8000) |
| `NEXT_PUBLIC_API_URL` | (Frontend) URL des Backends — der einzige `NEXT_PUBLIC_`-Wert |

## Tests ausführen

```bash
cd backend && .venv\Scripts\python -m pytest            # Unit + Mathe + Eval
cd backend && .venv\Scripts\python -m ruff check .      # Lint
cd frontend && npm run lint && npm test                 # Typecheck + Vitest
cd e2e && npx playwright test                           # startet beide Server selbst
```

Details zur Teststrategie: [testing.md](testing.md).

## Projektlayout

```
sourcerer/
  backend/app/
    ingest/       # TextExtractor (PDF/Text), Chunker, DocumentIngestor, WebPageFetcher (SSRF-Guard)
    rag/          # Retriever, PromptBuilder, CitationMapper, RAGPipeline, StudioService, AudioOverview
    providers/    # ABCs + Implementierungen: Embeddings, LLM, VectorStore, TTS (je OpenAI + Fake)
    repository.py / repository_supabase.py   # Metadaten: Interface + InMemory/Supabase
    main.py       # FastAPI + Composition Root (die EINE Stelle, die komponiert)
  backend/tests/  # unit/ · math/ · eval/ (Groundedness-Golden-Set)
  frontend/src/   # app/ (Page), components/, lib/ (api, types, validation, mermaid)
  e2e/            # Playwright (startet Backend fake + Frontend selbst)
  docs/           # dieses Verzeichnis: ADRs, Diagramme, Referenzen
```
