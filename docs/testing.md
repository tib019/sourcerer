# Test- & Qualitätsstrategie

**Regel aus CONTEXT.md:** Tests entstehen MIT dem Feature, nicht am Ende — kein
Feature im RAG-Kern ohne Test. Möglich macht das der Fake-Provider-Modus
([ADR-006](adr/ADR-006-provider-abstraction.md)): deterministische Implementierungen
aller Provider-Interfaces, dieselbe Composition Root — die komplette Suite läuft
offline, reproduzierbar und kostenfrei.

## Ebenen

| Ebene | Werkzeug | Was konkret abgesichert wird |
|---|---|---|
| **Unit (Python)** | pytest | Chunking-Grenzen (leeres Doc, 1 Satz, Riesen-Satz), Extraktion (generiertes PDF-Fixture), Zitat-Mapping (inkl. verworfener `[99]`-Halluzinationen), Orphan-Schutz (Ingest-Rollback, Delete räumt Vektoren), Studio-Schemata, SSRF-Blockliste (gemockt, kein Netz) |
| **Retrieval-Mathematik** | pytest | handgerechnete Cosine-Similarity, exakte Top-k-Reihenfolge mit festen Vektoren, Chunk-Overlap-Arithmetik Token für Token |
| **Groundedness-Eval** | pytest + Golden-Set | 8 beantwortbare + 2 unbeantwortbare Fragen auf festem Testdokument: zitierte Chunks enthalten die Antwort wirklich; ohne Quelle antwortet das System ehrlich. Opt-in gegen echte OpenAI-Provider (`SOURCERER_EVAL_OPENAI=1`) |
| **Unit (TS)** | Vitest | Zitat-Parsing, API-Client (inkl. Fehlerdurchreichung), Paste-Validierung, Mermaid-Fallback |
| **E2E** | Playwright | startet Backend (fake) + Frontend selbst: Kern-Flow mit Zitat-Klick, Quellen löschen (persistent nach Reload), Notebook-Isolation, Studio (Bericht/Karten/Quiz/Mindmap), Startfragen-Chips, Empty-States |

## Besonderheiten

- **Kalibrierte Konstanten statt Meinungen:** Der Retrieval-Floor ist zweimal
  empirisch gemessen ([ADR-004](adr/ADR-004-chunking.md), Script
  `backend/scripts/calibrate_min_score.py`); die Messwerte stehen als Konstanten in
  den Regressionstests.
- **Negativ-Pfade zuerst:** kein LLM-Call bei leerem Notebook (Spy-Test), ungültige
  Zitate/answer_index werden verworfen, SSRF-Fälle einzeln parametrisiert.
- **Kein Netz in Tests:** OpenAI/Pinecone/Supabase per Fake bzw. Mock
  (httpx.MockTransport, gemockter Supabase-Client, DNS gemockt).

## CI (GitHub Actions, bei jedem Push)

Drei Jobs, rot = kein Merge: **backend** (ruff + pytest), **frontend**
(tsc + Vitest + next build), **e2e** (Playwright gegen den echten lokalen Stack).

Aktueller Stand: **123 pytest · 20 Vitest · 10 Playwright** — alle grün.
