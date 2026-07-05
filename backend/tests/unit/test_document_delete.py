"""Einzel-Dokument-Löschung + Notebook-Reset (Fake-Provider, komplette App)."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app(Settings(providers="fake")))


@pytest.fixture()
def notebook_with_two_docs(client: TestClient) -> dict:
    notebook_id = client.post("/notebooks", json={"name": "NB"}).json()["id"]
    doc_a = client.post(
        f"/notebooks/{notebook_id}/documents/text",
        json={"name": "berge.txt", "text": "Der Mount Everest ist 8849 Meter hoch."},
    ).json()
    doc_b = client.post(
        f"/notebooks/{notebook_id}/documents/text",
        json={"name": "tuerme.txt", "text": "Der Eiffelturm ist 330 Meter hoch."},
    ).json()
    return {"notebook_id": notebook_id, "doc_a": doc_a, "doc_b": doc_b}


def _citation_docs(client: TestClient, notebook_id: str, question: str) -> set[str]:
    body = client.post(f"/notebooks/{notebook_id}/chat", json={"question": question}).json()
    return {c["document_name"] for c in body["citations"]}


class TestDeleteSingleDocument:
    def test_only_the_deleted_document_disappears(self, client, notebook_with_two_docs):
        nb = notebook_with_two_docs["notebook_id"]
        doc_a = notebook_with_two_docs["doc_a"]

        # Fragen mit Woertern, die jeweils NUR in einem Dokument vorkommen
        # ("hoch" o. ae. waere in beiden — der Fake-LLM antwortet auf jede Ueberlappung).
        frage_a = "Welche Hoehe hat der Mount Everest?"
        frage_b = "Welche Hoehe hat der Eiffelturm?"

        # Vorbedingung: beide Dokumente zitierbar
        assert _citation_docs(client, nb, frage_a) == {"berge.txt"}
        assert _citation_docs(client, nb, frage_b) == {"tuerme.txt"}

        response = client.delete(f"/notebooks/{nb}/documents/{doc_a['id']}")
        assert response.status_code == 204

        # Metadaten: nur doc_b übrig
        names = [d["name"] for d in client.get(f"/notebooks/{nb}/documents").json()]
        assert names == ["tuerme.txt"]

        # Vektoren: geloeschtes Doc liefert keine Zitate mehr, das andere schon
        assert _citation_docs(client, nb, frage_a) == set()
        assert _citation_docs(client, nb, frage_b) == {"tuerme.txt"}

    def test_unknown_document_404(self, client, notebook_with_two_docs):
        nb = notebook_with_two_docs["notebook_id"]
        assert client.delete(f"/notebooks/{nb}/documents/gibt-es-nicht").status_code == 404

    def test_document_of_other_notebook_404(self, client, notebook_with_two_docs):
        nb = notebook_with_two_docs["notebook_id"]
        other = client.post("/notebooks", json={"name": "Anderes"}).json()["id"]
        doc = client.post(
            f"/notebooks/{other}/documents/text",
            json={"name": "fremd.txt", "text": "Fremder Inhalt hier."},
        ).json()
        # Loeschversuch ueber das FALSCHE Notebook -> 404, Dokument bleibt
        assert client.delete(f"/notebooks/{nb}/documents/{doc['id']}").status_code == 404
        assert [d["name"] for d in client.get(f"/notebooks/{other}/documents").json()] == [
            "fremd.txt"
        ]

    def test_unknown_notebook_404(self, client):
        assert client.delete("/notebooks/nope/documents/egal").status_code == 404


class TestResetNotebook:
    def test_reset_clears_documents_and_vectors_keeps_notebook(
        self, client, notebook_with_two_docs
    ):
        nb = notebook_with_two_docs["notebook_id"]
        assert client.post(f"/notebooks/{nb}/reset").status_code == 204

        assert client.get(f"/notebooks/{nb}/documents").json() == []
        assert _citation_docs(client, nb, "Wie hoch ist der Eiffelturm?") == set()
        # Notebook existiert weiter und ist wieder befuellbar
        assert nb in [n["id"] for n in client.get("/notebooks").json()]
        again = client.post(
            f"/notebooks/{nb}/documents/text",
            json={"name": "neu.txt", "text": "Der Rhein ist 1233 Kilometer lang."},
        )
        assert again.status_code == 201
        assert _citation_docs(client, nb, "Wie lang ist der Rhein?") == {"neu.txt"}

    def test_reset_unknown_notebook_404(self, client):
        assert client.post("/notebooks/nope/reset").status_code == 404
