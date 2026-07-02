# ADR-003: Explizite RAG-Pipeline statt LangChain/Framework

**Status:** akzeptiert

## Kontext
Für RAG existieren Frameworks (LangChain, LlamaIndex), die Chunking, Retrieval und
Prompting hinter Abstraktionen verstecken.

## Entscheidung
Keine Frameworks. Eine explizite, lesbare Pipeline aus eigenen Klassen
(`DocumentIngestor`, `RAGPipeline` — siehe [Klassendiagramm](../class-diagram.md)).

## Alternativen
- **LangChain:** schnellerer Start, aber Verhalten (Chunk-Grenzen, Prompt-Aufbau,
  Retry-Logik) steckt in Framework-Magie — im Nachgespräch nicht verteidigbar und
  schwer deterministisch zu testen.
- **LlamaIndex:** gleiche Abwägung.

## Konsequenzen
- Jede Zeile der Pipeline ist erklärbar, jede Klasse einzeln unit-testbar.
- Chunk-Overlap-Arithmetik und Zitat-Mapping sind exakt spezifiziert und per
  deterministischer Mathematik getestet (`tests/math/`).
- Mehr eigener Code — bei diesem Umfang (~5 Kernklassen) bewusst in Kauf genommen.
