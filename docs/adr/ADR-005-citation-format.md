# ADR-005: Zitat-Format — [n]-Referenzen mit Chunk-Metadaten

**Status:** akzeptiert

## Kontext
Kern-Feature: jede Antwort muss belegbar sein. Der Nutzer muss vom Zitat zur
Original-Textstelle kommen (Dokument + Seite + Text).

## Entscheidung
Das LLM bekommt die Retrieval-Chunks als **nummerierte, delimitierte Blöcke** (`[1]…[k]`)
und zitiert mit `[n]`-Markern im Antworttext. Der `CitationMapper` extrahiert die Marker
und mappt sie zurück auf Chunk-Metadaten (doc_id, doc_name, chunk_index, page, text).
Das Frontend rendert `[n]` als klickbare Badges, Klick öffnet die Original-Textstelle.

## Alternativen
- **Freitext-Quellenangaben** („laut Kapitel 3 des Handbuchs…"): nicht maschinell
  verifizierbar, nicht klickbar, halluzinationsanfällig.
- **Strukturierter JSON-Output des LLM:** präziser parsebar, aber brüchiger (Schema-Drift)
  und schlechter streambar; `[n]`-Marker sind das von NotebookLM etablierte UX-Muster.

## Konsequenzen
- Zitate sind verifizierbar: Tests prüfen, dass jedes `[n]` auf einen realen Chunk zeigt
  und dass zitierte Chunks die Antwort-Info tatsächlich enthalten (Groundedness-Eval).
- Referenzen auf nicht existierende Quellen (`[99]`) werden vom Mapper verworfen —
  ein Halluzinations-Symptom, das damit sichtbar und testbar wird.
- Die Nummerierung ist pro Antwort stabil (Reihenfolge der Retrieval-Treffer).
