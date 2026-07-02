# ADR-004: Chunking-Strategie — ~800 Tokens, 15 % Overlap

**Status:** akzeptiert

## Kontext
Dokumente müssen in Chunks zerlegt werden, die (a) klein genug für präzises Retrieval und
(b) groß genug für ausreichenden Antwort-Kontext sind. Zitate zeigen auf Chunks — die
Chunk-Größe bestimmt also auch die Granularität der Quellenangabe.

## Entscheidung
Token-basiertes Sliding-Window: **Chunk-Größe ~800 Tokens, Overlap 15 % (120 Tokens)**,
Schnitt bevorzugt an Satzgrenzen. Seitennummer (PDF) wandert als Metadatum an jeden Chunk.

## Alternativen
- **Fixe Zeichenlänge:** trivial, aber schneidet mitten in Wörter/Sätze → schlechte Zitate.
- **Semantisches Chunking (per Embedding):** bessere thematische Kohärenz, aber
  nicht-deterministisch, langsamer, schwer testbar — Overkill für den MVP.
- **Ganze Seiten als Chunks:** natürliche Zitat-Einheit, aber sehr ungleiche Größen
  (leere vs. dichte Seiten) → instabiles Retrieval.

## Konsequenzen
- Overlap verhindert, dass Antworten an Chunk-Grenzen „zerschnitten" werden.
- Die Overlap-Arithmetik (Startpositionen, Token-Zählung) ist exakt spezifiziert und
  in `tests/math/` deterministisch getestet.
- Größe/Overlap sind Konstruktor-Parameter des `Chunker` — tuning ohne Codeänderung.
