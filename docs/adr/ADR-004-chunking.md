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

## Nachtrag: Retrieval-Mindest-Score (empirisch kalibriert)

Groundedness hat **zwei Verteidigungslinien**, die zusammenwirken:
1. **Retrieval-Threshold:** Chunks unter einem Cosine-Mindest-Score gelten nicht als
   Quelle. Liefert das Retrieval nichts über dem Threshold, antwortet das System
   „steht nicht in den Quellen", **ohne das LLM überhaupt aufzurufen** (ehrlich + spart
   Kosten).
2. **Prompt-Instruktion:** Auch mit Treffern über dem Threshold darf das LLM nur aus
   den Quellen antworten — für Fälle, in denen thematisch ähnliche Chunks die konkrete
   Frage trotzdem nicht beantworten.

Der Threshold wurde **gemessen, nicht geraten** (`scripts/calibrate_min_score.py`,
Golden-Set aus `tests/eval/`): text-embedding-3-small trennt sauber —
max(unbeantwortbar) = 0.21, min(beantwortbar) = 0.39 → **min_score = 0.30** (Mitte,
Marge beidseitig). Der Fake-Test-Stub hat eine eigene, unkalibrierte Score-Verteilung
und deshalb einen eigenen festen Wert (0.05, nur Boden gegen Null-Treffer); beide
Werte stehen in `app/config.py`, Override per Env-Variable `SOURCERER_MIN_SCORE`.
