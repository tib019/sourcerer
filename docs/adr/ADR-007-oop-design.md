# ADR-007: OOP-Design im RAG-Kern — Klassen + ABCs + DI statt Skript-Code

**Status:** akzeptiert

## Kontext
Der „KI-Default" für RAG-Demos ist prozeduraler Einweg-Skriptcode: eine Datei, globale
Clients, Logik und I/O vermischt. Das funktioniert — ist aber weder testbar noch erweiterbar
und im Nachgespräch nicht als Ingenieursarbeit verteidigbar.

## Entscheidung
Der RAG-Kern wird objektorientiert gebaut — Klassen mit klaren Verantwortlichkeiten
(SOLID, Kapselung), Interfaces als ABCs, Abhängigkeiten per Konstruktor-Injection:

- `DocumentIngestor` ← `TextExtractor` (Strategy je Dateityp), `Chunker`,
  `EmbeddingProvider`, `VectorStore`
- `RAGPipeline` ← `Retriever`, `PromptBuilder`, `LLMProvider`, `CitationMapper`

Siehe [Klassendiagramm (D2)](../class-diagram.md).

## Alternativen
- **Prozedurale Module mit Funktionen:** in Python legitim, aber Provider-Austausch und
  Mocking laufen dann über Modul-Patching statt über explizite Verträge.
- **Framework-Klassen (LangChain):** siehe ADR-003.

## Konsequenzen
- Jede Klasse ist einzeln unit-testbar; Provider werden per DI durch Fakes ersetzt —
  kein `unittest.mock.patch`-Gewebe.
- Austauschbarkeit: Pinecone→pgvector, OpenAI→BYOM = je eine neue Klasse.
- Etwas mehr Struktur-Overhead — bei einem Kern aus ~9 Klassen bewusst investiert.
