# ADR-002: Pinecone statt pgvector

**Status:** akzeptiert

## Kontext
Der RAG-Kern braucht einen Vektor-Store für Chunk-Embeddings mit Top-k-Similarity-Suche.
Supabase (Postgres) ist ohnehin im Stack — pgvector läge nahe.

## Entscheidung
Pinecone als produktiver Vektor-Store, hinter dem `VectorStore`-Interface (ABC).

## Alternativen
- **pgvector (in Supabase):** eine Plattform weniger, transaktional mit den Metadaten.
  Ernsthaft erwogen — für dieses Datenvolumen völlig ausreichend. Ausschlag für Pinecone:
  identisch zur produktiven healing-humans-Pipeline (Produktionserfahrung, bekannte
  Betriebs-Eigenschaften). pgvector bleibt als dokumentierte Migration: eine neue
  `VectorStore`-Implementierung, kein Umbau.
- **FAISS/Chroma lokal:** kein persistenter Managed-Betrieb, für Deploy-Demo ungeeignet.

## Konsequenzen
- Ein zusätzlicher externer Service (Key, Index-Management).
- Durch das Interface ist der Wechsel zu pgvector jederzeit eine Klasse groß.
- Tests laufen gegen einen `InMemoryVectorStore` — kein Pinecone-Zugriff in CI.
