"""Notebook-/Dokument-Metadaten — Repository-Interface + In-Memory-Implementierung.

Schema siehe docs/er-diagram.md. Die Supabase-Implementierung ist dieselbe
Schnittstelle (NOTES.md §6) — für den Demo-Scope reicht In-Memory.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import DocumentMeta, Notebook, new_id
from app.errors import NotebookNotFoundError


class NotebookRepository(ABC):
    @abstractmethod
    def create_notebook(self, name: str) -> Notebook: ...

    @abstractmethod
    def get_notebook(self, notebook_id: str) -> Notebook: ...

    @abstractmethod
    def list_notebooks(self) -> list[Notebook]: ...

    @abstractmethod
    def add_document(self, document: DocumentMeta) -> None: ...

    @abstractmethod
    def list_documents(self, notebook_id: str) -> list[DocumentMeta]: ...


class InMemoryNotebookRepository(NotebookRepository):
    def __init__(self) -> None:
        self._notebooks: dict[str, Notebook] = {}
        self._documents: dict[str, list[DocumentMeta]] = {}

    def create_notebook(self, name: str) -> Notebook:
        notebook = Notebook(id=new_id(), name=name)
        self._notebooks[notebook.id] = notebook
        self._documents[notebook.id] = []
        return notebook

    def get_notebook(self, notebook_id: str) -> Notebook:
        notebook = self._notebooks.get(notebook_id)
        if notebook is None:
            raise NotebookNotFoundError(f"Notebook '{notebook_id}' existiert nicht.")
        return notebook

    def list_notebooks(self) -> list[Notebook]:
        return list(self._notebooks.values())

    def add_document(self, document: DocumentMeta) -> None:
        self.get_notebook(document.notebook_id)
        self._documents[document.notebook_id].append(document)

    def list_documents(self, notebook_id: str) -> list[DocumentMeta]:
        self.get_notebook(notebook_id)
        return list(self._documents[notebook_id])
