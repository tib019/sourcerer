"""Retriever — Query-Embedding + Top-k-Suche im VectorStore."""

from __future__ import annotations

from app.domain import ScoredChunk
from app.providers.embeddings import EmbeddingProvider
from app.providers.vector_store import VectorStore


class Retriever:
    def __init__(
        self,
        embedder: EmbeddingProvider,
        store: VectorStore,
        top_k: int = 6,
        min_score: float = 0.0,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._top_k = top_k
        self._min_score = min_score

    def retrieve(self, question: str, notebook_id: str) -> list[ScoredChunk]:
        vector = self._embedder.embed([question])[0]
        results = self._store.query(vector, top_k=self._top_k, namespace=notebook_id)
        # score > min_score: Treffer ohne jede Ähnlichkeit sind keine Quellen.
        return [r for r in results if r.score > self._min_score]
