"""SupabaseNotebookRepository — dieselbe Schnittstelle, Postgres statt RAM.

Schema siehe docs/er-diagram.md (Tabellen: notebooks, documents, chunks;
FKs mit ON DELETE CASCADE — delete_notebook räumt die Metadaten-Seite komplett).
Die Vektor-Seite (Pinecone-Namespace) räumt der API-Layer über VectorStore.

Der Client wird injiziert (DI wie überall) — Unit-Tests mocken ihn, ohne Netz.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.domain import Chunk, DocumentMeta, Notebook, new_id
from app.errors import NotebookNotFoundError
from app.repository import NotebookRepository


class SupabaseLike(Protocol):
    """Der schmale Ausschnitt des supabase-py-Clients, den wir benutzen."""

    def table(self, name: str) -> Any: ...


def create_supabase_client(url: str, key: str) -> SupabaseLike:
    from supabase import create_client

    return create_client(url, key)


class SupabaseNotebookRepository(NotebookRepository):
    def __init__(self, client: SupabaseLike) -> None:
        self._client = client

    def create_notebook(self, name: str) -> Notebook:
        notebook = Notebook(id=new_id(), name=name)
        self._client.table("notebooks").insert(
            {"id": notebook.id, "name": notebook.name}
        ).execute()
        return notebook

    def get_notebook(self, notebook_id: str) -> Notebook:
        response = (
            self._client.table("notebooks")
            .select("id, name")
            .eq("id", notebook_id)
            .execute()
        )
        if not response.data:
            raise NotebookNotFoundError(f"Notebook '{notebook_id}' existiert nicht.")
        row = response.data[0]
        return Notebook(id=row["id"], name=row["name"])

    def list_notebooks(self) -> list[Notebook]:
        response = (
            self._client.table("notebooks").select("id, name").order("created_at").execute()
        )
        return [Notebook(id=row["id"], name=row["name"]) for row in response.data]

    def delete_notebook(self, notebook_id: str) -> None:
        self.get_notebook(notebook_id)
        # FKs mit ON DELETE CASCADE entfernen documents + chunks mit.
        self._client.table("notebooks").delete().eq("id", notebook_id).execute()

    def add_document(self, document: DocumentMeta) -> None:
        self.get_notebook(document.notebook_id)
        self._client.table("documents").insert(
            {
                "id": document.id,
                "notebook_id": document.notebook_id,
                "name": document.name,
                "media_type": document.media_type,
                "page_count": document.page_count,
                "chunk_count": document.chunk_count,
            }
        ).execute()

    def add_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        self._client.table("chunks").insert(
            [
                {
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "page": chunk.page,
                    "text": chunk.text,
                }
                for chunk in chunks
            ]
        ).execute()

    def list_chunks(self, notebook_id: str) -> list[Chunk]:
        # Join über documents: nur Chunks dieses Notebooks, inkl. Dokumentname.
        response = (
            self._client.table("chunks")
            .select("id, document_id, chunk_index, page, text, documents!inner(notebook_id, name)")
            .eq("documents.notebook_id", notebook_id)
            .order("document_id")
            .order("chunk_index")
            .execute()
        )
        return [
            Chunk(
                id=row["id"],
                document_id=row["document_id"],
                document_name=row["documents"]["name"],
                chunk_index=row["chunk_index"],
                page=row["page"],
                text=row["text"],
            )
            for row in response.data
        ]

    def list_documents(self, notebook_id: str) -> list[DocumentMeta]:
        self.get_notebook(notebook_id)
        response = (
            self._client.table("documents")
            .select("id, notebook_id, name, media_type, page_count, chunk_count")
            .eq("notebook_id", notebook_id)
            .order("created_at")
            .execute()
        )
        return [
            DocumentMeta(
                id=row["id"],
                notebook_id=row["notebook_id"],
                name=row["name"],
                media_type=row["media_type"],
                page_count=row["page_count"],
                chunk_count=row["chunk_count"],
            )
            for row in response.data
        ]
