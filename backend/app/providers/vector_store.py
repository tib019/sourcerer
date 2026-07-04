"""VectorStore — ABC + Pinecone- und In-Memory-Implementierung (ADR-002, ADR-006).

Namespace = notebook_id → Quellen sind pro Notebook isoliert.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

from app.domain import Chunk, ScoredChunk


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine-Similarity zweier Vektoren — deterministisch getestet in tests/math/."""
    if len(a) != len(b):
        raise ValueError(f"Dimensionen passen nicht: {len(a)} != {len(b)}")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, chunks: list[Chunk], vectors: list[list[float]], namespace: str) -> None: ...

    @abstractmethod
    def query(self, vector: list[float], top_k: int, namespace: str) -> list[ScoredChunk]: ...

    @abstractmethod
    def delete_document(self, document_id: str, namespace: str) -> None: ...

    @abstractmethod
    def delete_namespace(self, namespace: str) -> None:
        """Alle Vektoren eines Notebooks entfernen — Gegenstück zu delete_notebook."""


class InMemoryVectorStore(VectorStore):
    """Exakte Cosine-Suche im Speicher — Tests, CI und Offline-Demo."""

    def __init__(self) -> None:
        self._data: dict[str, list[tuple[list[float], Chunk]]] = {}

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]], namespace: str) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks und vectors müssen gleich lang sein")
        bucket = self._data.setdefault(namespace, [])
        replaced_ids = {c.id for c in chunks}
        bucket[:] = [(v, c) for v, c in bucket if c.id not in replaced_ids]
        bucket.extend(zip(vectors, chunks, strict=True))

    def query(self, vector: list[float], top_k: int, namespace: str) -> list[ScoredChunk]:
        bucket = self._data.get(namespace, [])
        scored = [
            ScoredChunk(chunk=chunk, score=cosine_similarity(vector, stored))
            for stored, chunk in bucket
        ]
        scored.sort(key=lambda s: (-s.score, s.chunk.chunk_index))
        return scored[:top_k]

    def delete_document(self, document_id: str, namespace: str) -> None:
        bucket = self._data.get(namespace, [])
        bucket[:] = [(v, c) for v, c in bucket if c.document_id != document_id]

    def delete_namespace(self, namespace: str) -> None:
        self._data.pop(namespace, None)


class PineconeStore(VectorStore):
    """Pinecone-Index; Chunk-Metadaten wandern an den Vektor (ER-Diagramm D5)."""

    def __init__(self, api_key: str, index_name: str) -> None:
        from pinecone import Pinecone

        self._index = Pinecone(api_key=api_key).Index(index_name)

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]], namespace: str) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks und vectors müssen gleich lang sein")
        self._index.upsert(
            vectors=[
                {
                    "id": chunk.id,
                    "values": vector,
                    "metadata": {
                        "document_id": chunk.document_id,
                        "document_name": chunk.document_name,
                        "chunk_index": chunk.chunk_index,
                        "page": chunk.page,
                        "text": chunk.text,
                    },
                }
                for chunk, vector in zip(chunks, vectors, strict=True)
            ],
            namespace=namespace,
        )

    def query(self, vector: list[float], top_k: int, namespace: str) -> list[ScoredChunk]:
        result = self._index.query(
            vector=vector, top_k=top_k, namespace=namespace, include_metadata=True
        )
        return [
            ScoredChunk(
                chunk=Chunk(
                    id=match["id"],
                    document_id=match["metadata"]["document_id"],
                    document_name=match["metadata"]["document_name"],
                    chunk_index=int(match["metadata"]["chunk_index"]),
                    page=int(match["metadata"]["page"]),
                    text=match["metadata"]["text"],
                ),
                score=float(match["score"]),
            )
            for match in result["matches"]
        ]

    def delete_document(self, document_id: str, namespace: str) -> None:
        self._index.delete(filter={"document_id": document_id}, namespace=namespace)

    def delete_namespace(self, namespace: str) -> None:
        self._index.delete(delete_all=True, namespace=namespace)
