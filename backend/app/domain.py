"""Domain-Modelle des RAG-Kerns.

Bewusst schlanke Dataclasses statt Pydantic: das hier ist der innere Kern,
API-Schemas (Pydantic) leben am Rand in main.py.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


def new_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class PageText:
    """Rohtext einer Seite (Plaintext = eine Seite 1)."""

    page: int
    text: str


@dataclass(frozen=True)
class Chunk:
    """Ein Text-Chunk mit allen Metadaten, die ein Zitat braucht."""

    id: str
    document_id: str
    document_name: str
    chunk_index: int
    page: int
    text: str


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Citation:
    """[n]-Referenz aus der Antwort, zurückgemappt auf den Chunk."""

    n: int
    document_id: str
    document_name: str
    chunk_index: int
    page: int
    text: str


@dataclass(frozen=True)
class ChatAnswer:
    text: str
    citations: list[Citation] = field(default_factory=list)


@dataclass(frozen=True)
class IngestResult:
    document_id: str
    document_name: str
    page_count: int
    chunk_count: int


@dataclass(frozen=True)
class DocumentMeta:
    id: str
    notebook_id: str
    name: str
    media_type: str
    page_count: int
    chunk_count: int


@dataclass(frozen=True)
class Notebook:
    id: str
    name: str
