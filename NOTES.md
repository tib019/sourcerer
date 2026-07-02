# NOTES.md — Entscheidungen, Trade-offs, KI-Einsatz

## 1 · Ansatz & Arbeitsweise

Agent Loop mit [CONTEXT.md](CONTEXT.md) als Harness: Scope, Architektur und Prioritäten wurden
VOR dem ersten Code festgelegt und blieben über die gesamte Session stabil. Jede Aufgabe wurde
aus CONTEXT.md abgeleitet, an die KI delegiert, das Ergebnis reviewt, korrigiert, committet.
Die Git-History erzählt den Prozess (Conventional Commits, Docs vor Code, Tests mit dem Feature).

## 2 · KI-Einsatz konkret

- **Wofür genutzt:** Scaffolding (Repo-Struktur, Boilerplate), Implementierung der in CONTEXT.md
  spezifizierten Klassen, Testfälle ausformulieren, Diagramme aus der Architektur ableiten.
- **Wo korrigiert (echte Beispiele aus der Session):**
  - **Race-Condition im Upload-Flow, vom E2E-Test aufgedeckt:** Die erste UI-Version
    erlaubte den Datei-Upload, bevor das Notebook vom Backend geladen war —
    `handleUpload` brach bei `notebook === null` **stumm** ab (klassischer KI-Code:
    Guard-Clause statt sauberem Zustand). Der Playwright-Test schlug fehl, die Analyse
    zeigte den stillen No-Op. Fix: Upload-UI ist erst aktiv, wenn das Notebook bereit ist
    (`busy = uploading || !notebook`), der Test wartet explizit auf den enabled-Zustand.
  - **Lint als Review-Instanz:** ruff meldete `zip()` ohne `strict` im Vektor-Code —
    bei ungleich langen chunk/vector-Listen wäre stumm gekürzt worden. Auf `strict=True`
    gesetzt: Längen-Mismatch ist jetzt ein lauter Fehler statt Datenverlust.

## 3 · Eigene Design-Entscheidungen

Alle wesentlichen Entscheidungen als ADRs in [docs/adr/](docs/adr/):
Frontend/Backend-Split (001), Pinecone (002), keine Frameworks (003), Chunking (004),
Zitat-Format (005), Provider-Abstraktion (006), OOP-Design (007).

Zusätzlich: **Fake-Provider-Modus** (`SOURCERER_PROVIDERS=fake`) — deterministische
Embedding/LLM/Store-Implementierungen hinter denselben Interfaces. Dadurch laufen Unit-,
Mathe- und E2E-Tests komplett offline und reproduzierbar in CI, ohne API-Kosten und ohne Flakes.

## 4 · Bewusst weggelassen + warum

- **Kein LangChain / Agent-Framework** — für RAG reicht eine explizite, lesbare Pipeline.
  Weniger Magie, mehr Kontrolle ([ADR-003](docs/adr/ADR-003-no-framework.md)).
- **Kein Multi-User/Auth** — Demo-Scope. Produktion: Supabase Auth + Row Level Security.
- **Kein Multi-Provider-UI** — aber LLM/Embeddings/Store hinter Interfaces → BYOM ist eine
  neue Klasse, kein Umbau ([ADR-006](docs/adr/ADR-006-provider-abstraction.md)).
- **Kein Firebase** — Supabase deckt Storage + Metadaten ab; kein unbegründeter Plattform-Zoo.
- **Kein Word-Support** — PDF + Plaintext decken den Kern-Flow ab; docx wäre nur ein weiterer
  `TextExtractor`, ohne neuen Erkenntniswert fürs Testprojekt.

## 5 · Sicherheit

Hochgeladene Dokumente sind untrusted Input → **Prompt-Injection-Risiko**. Maßnahmen:

1. Quellen-Chunks werden delimitiert und nummeriert in den Prompt gesetzt — klar getrennt
   vom System-Prompt (`PromptBuilder`).
2. Explizite Instruktion: Quellen sind Daten, keine Anweisungen. Anweisungen in Dokumenten
   werden ignoriert.
3. Input-Validierung beim Upload: Dateityp-Whitelist, Größenlimit, leere Dokumente abgelehnt.
4. Keys nur server-seitig (Env-Variablen), nie im Frontend, `.env` in `.gitignore`.

## 6 · Produktions-Ausblick

- **EU-Hosting** (Supabase Frankfurt, Azure OpenAI EU-Region) für DSGVO
- **Supabase RLS + Auth** für Multi-User
- **Monitoring:** in Produktion Langfuse für Kosten-/Qualitäts-Tracking der LLM-Calls
  (im Code: simples Token/Kosten-Logging pro Call, siehe `providers/llm.py`)
- Word-Support (weiterer `TextExtractor`), mehrere Notebooks pro User, Audio-Overview (TTS)
