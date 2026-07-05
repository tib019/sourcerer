"""DocumentIngestor — orchestriert Extract → Chunk → Embed → Store (D4)."""

from __future__ import annotations

from app.domain import DocumentMeta, IngestResult, new_id
from app.errors import FileTooLargeError, UnsupportedFileTypeError
from app.ingest.chunker import Chunker
from app.ingest.extractor import TextExtractor
from app.providers.embeddings import EmbeddingProvider
from app.providers.vector_store import VectorStore
from app.repository import NotebookRepository

MEDIA_TYPE_PDF = "application/pdf"
MEDIA_TYPE_TEXT = "text/plain"


class DocumentIngestor:
    def __init__(
        self,
        extractors: dict[str, TextExtractor],
        chunker: Chunker,
        embedder: EmbeddingProvider,
        store: VectorStore,
        repository: NotebookRepository,
        max_bytes: int = 10 * 1024 * 1024,
    ) -> None:
        self._extractors = extractors
        self._chunker = chunker
        self._embedder = embedder
        self._store = store
        self._repository = repository
        self._max_bytes = max_bytes

    def ingest(
        self,
        data: bytes,
        *,
        filename: str,
        media_type: str,
        notebook_id: str,
        source_url: str | None = None,
    ) -> IngestResult:
        self._repository.get_notebook(notebook_id)  # wirft NotebookNotFoundError

        if len(data) > self._max_bytes:
            raise FileTooLargeError(
                f"Datei zu groß ({len(data)} Bytes, Limit {self._max_bytes})."
            )
        extractor = self._extractors.get(media_type)
        if extractor is None:
            raise UnsupportedFileTypeError(
                f"'{media_type}' wird nicht unterstützt (erlaubt: "
                f"{', '.join(sorted(self._extractors))})."
            )

        pages = extractor.extract(data)  # wirft EmptyDocumentError
        document_id = new_id()
        chunks = self._chunker.chunk(pages, document_id=document_id, document_name=filename)

        # Erst embedden, dann upserten — ein Embedding-Fehler hinterlässt keinen Teil-Zustand.
        vectors = self._embedder.embed([chunk.text for chunk in chunks])
        self._store.upsert(chunks, vectors, namespace=notebook_id)

        try:
            self._repository.add_document(
                DocumentMeta(
                    id=document_id,
                    notebook_id=notebook_id,
                    name=filename,
                    media_type=media_type,
                    page_count=len(pages),
                    chunk_count=len(chunks),
                    source_url=source_url,
                )
            )
            self._repository.add_chunks(chunks)
        except Exception:
            # Metadaten fehlgeschlagen → bereits upserted Vektoren wären Orphans.
            self._store.delete_document(document_id, namespace=notebook_id)
            raise
        return IngestResult(
            document_id=document_id,
            document_name=filename,
            page_count=len(pages),
            chunk_count=len(chunks),
        )
