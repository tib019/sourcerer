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

## Nachtrag: Retrieval-Mindest-Score (zweimal empirisch kalibriert)

Groundedness hat **zwei Verteidigungslinien**:
1. **Retrieval-Floor:** Chunks unter einem Cosine-Mindest-Score gelten als Rauschen.
   Liefert das Retrieval nichts darüber, antwortet das System „steht nicht in den
   Quellen", ohne das LLM aufzurufen.
2. **Prompt-Instruktion:** Das LLM antwortet nur aus den Quellen und sagt den
   Sentinel, wenn die Treffer die Frage nicht hergeben.

**Kalibrierung 1** (`scripts/calibrate_min_score.py`, synthetisches Golden-Set):
text-embedding-3-small trennte scheinbar sauber — max(unbeantwortbar) = 0.21,
min(beantwortbar) = 0.39 → min_score = 0.30.

**Kalibrierung 2 (Produktions-Incident):** Echte Nutzer-Queries auf ein echtes Paper
brachen die Trennung. Gemessen gegen den Live-Index: Kurz-Query „Ideologie" (in-source,
sinngemäß beantwortbar) top1 = **0.12**; Cross-Language „Stufe 1" (Quelle sagt
„Stage 1") top1 = **0.21** — beides unterhalb von Out-of-Source-Fragen (bis 0.21).
**Es existiert kein Skalarwert, der beides richtig trennt.** Die saubere Trennung aus
Kalibrierung 1 war ein Artefakt des zu einfachen Golden-Sets (wortreiche,
keyword-deckende Fragen).

**Konsequenz:** Der Threshold ist ein **Rausch-Floor (0.05)**, kein Relevanz-Urteil.
Die Relevanz-Entscheidung trifft das LLM über den Prompt — der dafür Synthese,
Definitionsfragen und Cross-Language-Antworten explizit erlaubt (sonst lehnt das
Modell zu strikt ab, zweiter Teil desselben Incidents). Lieber ein unnötiger LLM-Call
(~2 ct), der ehrlich „steht nicht in den Quellen" sagt, als eine fälschlich
verweigerte Antwort. Beide Werte in `app/config.py`, Override via `SOURCERER_MIN_SCORE`.
