# ADR-001: Getrenntes TS-Frontend + Python-RAG-Service statt Next.js-Monolith

**Status:** akzeptiert

## Kontext
Ein NotebookLM-Klon braucht UI (Upload, Chat, Quellen-Panel) und einen RAG-Kern
(Extraktion, Chunking, Embeddings, Retrieval, Zitat-Mapping). Der „KI-Default" wäre ein
Next.js-Monolith mit API-Routes aus dem Template.

## Entscheidung
Getrenntes Next.js/TypeScript-Frontend (Vercel) + eigenständiger Python/FastAPI-Service
(Railway, Docker) für den gesamten RAG-Kern.

## Alternativen
- **Next.js-Monolith (API-Routes in TS):** weniger Deploy-Aufwand, aber die RAG-Tiefe
  (Chunking-Arithmetik, Retrieval, Eval-Tests) liegt in Python deutlich besser — pypdf,
  pytest-Ökosystem, und Python ist die stärkste Sprache des Autors.
- **Python-Fullstack (FastAPI + Jinja/HTMX):** ein Deploy weniger, aber schwächere UI-DX
  und kein erprobter Frontend-Stack.

## Konsequenzen
- Zwei Deploys (Vercel + Railway), CORS-Konfiguration nötig.
- RAG-Logik dort, wo Testbarkeit und Produktionserfahrung liegen.
- Klare API-Grenze erzwingt sauberes Schnittstellen-Design.
