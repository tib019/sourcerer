# Betrieb & Deployment

Live-Setup: Frontend auf **Vercel**, Backend als **Docker-Container auf Railway**,
Managed Services Pinecone (Vektor-Index) + Supabase (Postgres, Frankfurt/eu-central-1).
Diagramm: [deployment.md](deployment.md) (D6).

## Backend (Railway)

- **Image:** `backend/Dockerfile` (python:3.12-slim). Railway erkennt das Dockerfile
  automatisch; `railway up` aus `backend/` deployt.
- **Port:** Der Container bindet an `$PORT` (von Railway injiziert), Fallback 8000.
  Empfehlung: `PORT` als Service-Variable explizit setzen und den Domain-Target-Port
  darauf zeigen lassen — deterministisch statt Magic Detection.
- **Env-Variablen** (Service-Variablen, nie im Image): siehe Tabelle in
  [setup.md](setup.md); produktiv `SOURCERER_PROVIDERS=openai` + alle Keys.
- **CORS:** `SOURCERER_CORS_ORIGINS` exakt auf die Vercel-Produktions-Domain(s)
  setzen — Änderungen greifen erst mit einem Redeploy.
- **Health-Check:** `GET /health` → `{"status": "ok", "providers": "openai"}`.

## Frontend (Vercel)

- Projekt-Root ist `frontend/`; Deploy per `vercel deploy --prod`.
- **`NEXT_PUBLIC_API_URL`** als Environment-Variable in den Project Settings
  (Production) — wird zur **Build-Zeit** eingebacken; nach Änderung neu deployen.
  Es ist der einzige `NEXT_PUBLIC_`-Wert des Projekts (öffentliche URL, kein Secret).

## Datenhaltung

- **Supabase:** Tabellen `notebooks` / `documents` / `chunks` (Schema:
  [er-diagram.md](er-diagram.md)); FK `ON DELETE CASCADE`. **RLS ist aktiv ohne
  Policies** — der anon-Key ist vollständig gesperrt, das Backend nutzt den
  Service-Role-Key (nur server-seitig).
- **Pinecone:** Index dim 1536 / metric cosine (text-embedding-3-small);
  **Namespace = Notebook-ID** → Quellen sind pro Notebook isoliert, Löschen räumt
  den Namespace bzw. per Metadaten-Filter einzelne Dokumente.
- Notebooks überleben Container-Neustarts (Metadaten in Supabase, Vektoren in
  Pinecone; der Prozess hält keinen Zustand).

## Secrets-Regeln

Keys existieren nur in `backend/.env` (lokal, gitignored) und den Secret-Stores der
Plattformen (Railway-Variablen, Vercel Project Settings). Vor jedem Commit:
`git ls-files | grep -iE "env|token|secret"` darf nur `.env.example` zeigen.
