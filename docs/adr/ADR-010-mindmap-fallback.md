# ADR-010: Mindmap — Server baut Mermaid, Client rendert mit Fallback

**Status:** akzeptiert

## Kontext
Die Mindmap visualisiert die Quellen eines Notebooks. Naiver Ansatz: das LLM erzeugt
direkt Mermaid-Text, das Frontend rendert ihn. Zwei Risiken: (a) LLM-Output bricht
die Mermaid-Syntax → Rendering-Crash im Panel, (b) LLM-Output (bzw. via Prompt-
Injection eingeschleuster Quelltext) injiziert Mermaid-Direktiven/Links.

## Entscheidung
**Das LLM liefert nie Mermaid.** Es liefert einen JSON-Baum
(`{root, branches[{label, children[]}]}`), Pydantic-validiert. Den Mermaid-Text baut
der **Server** aus Whitelist-bereinigten Labels (nur Wortzeichen + harmlose
Interpunktion; Quotes/Klammern/Backticks/Zeilenumbrüche entfernt, 60-Zeichen-Cap)
mit hartem Knoten-Deckel (25).

Das Frontend rendert mit mermaid.js (`securityLevel: strict`, lazy geladen) in
try/catch: schlägt Parsen/Rendern trotzdem fehl, zeigt die UI die Gliederung als
Liste plus Hinweis — **nie** ein Crash der Seite oder des Panels.

## Alternativen
- **LLM erzeugt rohes Mermaid + Regex-Bereinigung:** Blacklists gegen eine lebende
  Syntax sind ein Wettrüsten; das JSON-Zwischenformat macht die gefährliche Fläche
  strukturell unerreichbar.
- **Server rendert SVG (mermaid-cli/Puppeteer):** Headless-Browser im Backend-
  Container — massiver Betriebsaufwand für ein Stretch-Feature.

## Konsequenzen
- Feindliche Labels sind per Test abgedeckt (`((shape))`, `[[link]]`, `<script>`,
  Backticks, Newlines → alles neutralisiert), ebenso der Knoten-Cap.
- Der Fallback-Pfad ist eigenständig getestet (Vitest, gemocktes mermaid wirft).
- mermaid lädt als eigener Chunk erst beim Öffnen des Mindmap-Tabs — kein
  Bundle-Gewicht für den Kern-Flow.
