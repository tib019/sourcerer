"""SupabaseNotebookRepository gegen einen gemockten Client — kein Netz, keine Keys."""

import pytest

from app.domain import Chunk, DocumentMeta
from app.errors import NotebookNotFoundError
from app.repository_supabase import SupabaseNotebookRepository


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    """Chainable Stub: zeichnet Operationen auf, liefert vorbereitete Daten."""

    def __init__(self, table: "_FakeClient", name: str):
        self._client = table
        self._name = name
        self._op = None
        self._payload = None
        self._filters = {}

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def select(self, *_):
        self._op = "select"
        return self

    def delete(self):
        self._op = "delete"
        return self

    def eq(self, column, value):
        self._filters[column] = value
        return self

    def order(self, *_):
        return self

    def execute(self):
        self._client.calls.append(
            (self._name, self._op, self._payload, dict(self._filters))
        )
        if self._op == "select":
            rows = self._client.rows.get(self._name, [])
            for column, value in self._filters.items():
                rows = [r for r in rows if r.get(column) == value]
            return _Response(rows)
        return _Response(self._payload)


class _FakeClient:
    def __init__(self):
        self.calls: list = []
        self.rows: dict[str, list[dict]] = {"notebooks": [], "documents": [], "chunks": []}

    def table(self, name):
        return _Query(self, name)


@pytest.fixture()
def client() -> _FakeClient:
    return _FakeClient()


@pytest.fixture()
def repo(client: _FakeClient) -> SupabaseNotebookRepository:
    return SupabaseNotebookRepository(client)


def test_create_notebook_inserts_row(repo, client):
    notebook = repo.create_notebook("Mein Notebook")
    table, op, payload, _ = client.calls[0]
    assert (table, op) == ("notebooks", "insert")
    assert payload == {"id": notebook.id, "name": "Mein Notebook"}


def test_get_notebook_unknown_raises(repo):
    with pytest.raises(NotebookNotFoundError):
        repo.get_notebook("gibt-es-nicht")


def test_get_and_list_documents_roundtrip(repo, client):
    client.rows["notebooks"] = [{"id": "n1", "name": "NB"}]
    client.rows["documents"] = [
        {
            "id": "d1", "notebook_id": "n1", "name": "a.txt",
            "media_type": "text/plain", "page_count": 1, "chunk_count": 3,
        },
        {
            "id": "d2", "notebook_id": "ANDERES", "name": "fremd.txt",
            "media_type": "text/plain", "page_count": 1, "chunk_count": 1,
        },
    ]
    documents = repo.list_documents("n1")
    assert [d.id for d in documents] == ["d1"]  # eq-Filter greift
    assert documents[0].chunk_count == 3


def test_add_document_requires_existing_notebook(repo):
    with pytest.raises(NotebookNotFoundError):
        repo.add_document(
            DocumentMeta(
                id="d1", notebook_id="fehlt", name="x.txt",
                media_type="text/plain", page_count=1, chunk_count=1,
            )
        )


def test_add_chunks_bulk_insert(repo, client):
    chunks = [
        Chunk(id=f"c{i}", document_id="d1", document_name="a.txt",
              chunk_index=i, page=1, text=f"Text {i}")
        for i in range(3)
    ]
    repo.add_chunks(chunks)
    table, op, payload, _ = client.calls[0]
    assert (table, op) == ("chunks", "insert")
    assert len(payload) == 3
    assert payload[2] == {
        "id": "c2", "document_id": "d1", "chunk_index": 2, "page": 1, "text": "Text 2",
    }
    # document_name ist bewusst NICHT in der Tabelle (kommt via FK -> documents.name)


def test_delete_notebook_deletes_by_id(repo, client):
    client.rows["notebooks"] = [{"id": "n1", "name": "NB"}]
    repo.delete_notebook("n1")
    table, op, _, filters = client.calls[-1]
    assert (table, op) == ("notebooks", "delete")
    assert filters == {"id": "n1"}
