# Architecture Decision Records

Jede wesentliche Entscheidung als ADR: Kontext → Entscheidung → Alternativen →
Konsequenzen. Reihenfolge = Entstehungsreihenfolge.

| # | Entscheidung |
|---|---|
| [ADR-001](ADR-001-frontend-backend-split.md) | Getrenntes TS-Frontend + Python-RAG-Service statt Next.js-Monolith |
| [ADR-002](ADR-002-pinecone.md) | Pinecone statt pgvector (pgvector als dokumentierte Alternative) |
| [ADR-003](ADR-003-no-framework.md) | Explizite RAG-Pipeline statt LangChain/Framework |
| [ADR-004](ADR-004-chunking.md) | Chunking-Strategie + Retrieval-Floor (zweimal empirisch kalibriert) |
| [ADR-005](ADR-005-citation-format.md) | Zitat-Format: [n]-Referenzen ↔ Chunk-Metadaten |
| [ADR-006](ADR-006-provider-abstraction.md) | Provider-Abstraktion (ABCs + DI, Fake-Provider für Tests/CI) |
| [ADR-007](ADR-007-oop-design.md) | OOP-Design im RAG-Kern statt Skript-Code |
| [ADR-008](ADR-008-audio-overview-tts.md) | Audio-Overview: TTS hinter Provider-Interface |
| [ADR-009](ADR-009-url-import-ssrf.md) | URL-Import mit SSRF-Härtung |
| [ADR-010](ADR-010-mindmap-fallback.md) | Mindmap: Server baut Mermaid, Client rendert mit Fallback |
