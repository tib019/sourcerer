"""Orphan-Schutz (2d): weder fehlgeschlagener Ingest noch Notebook-Löschung
dürfen verwaiste Vektoren im Store zurücklassen."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import SourcererError
from app.ingest.chunker import Chunker
from app.ingest.extractor import PlainTextExtractor
from app.ingest.ingestor import MEDIA_TYPE_TEXT, DocumentIngestor
from app.main import create_app
from app.providers.embeddings import FakeEmbeddings
from app.providers.vector_store import InMemoryVectorStore
from app.repository import InMemoryNotebookRepository


class _FailingRepository(InMemoryNotebookRepository):
    """Simuliert einen Metadaten-Ausfall NACH dem Vektor-Upsert."""

    def add_document(self, document):
        raise SourcererError("Supabase nicht erreichbar (simuliert)")


def test_failed_ingest_rolls_back_upserted_vectors():
    store = InMemoryVectorStore()
    embedder = FakeEmbeddings()
    repository = _FailingRepository()
    notebook = repository.create_notebook("NB")

    ingestor = DocumentIngestor(
        extractors={MEDIA_TYPE_TEXT: PlainTextExtractor()},
        chunker=Chunker(chunk_size=50, overlap=5),
        embedder=embedder,
        store=store,
        repository=repository,
    )

    with pytest.raises(SourcererError):
        ingestor.ingest(
            b"Ein Satz mit Inhalt. Noch ein Satz mit Inhalt.",
            filename="doc.txt",
            media_type=MEDIA_TYPE_TEXT,
            notebook_id=notebook.id,
        )

    query_vector = embedder.embed(["Satz Inhalt"])[0]
    assert store.query(query_vector, top_k=5, namespace=notebook.id) == [], (
        "Nach fehlgeschlagenem Ingest dürfen keine Vektoren zurückbleiben"
    )


def test_delete_notebook_removes_documents_and_vectors():
    client = TestClient(create_app(Settings(providers="fake")))
    notebook_id = client.post("/notebooks", json={"name": "NB"}).json()["id"]
    client.post(
        f"/notebooks/{notebook_id}/documents/text",
        json={"name": "fakten.txt", "text": "Der Eiffelturm ist 330 Meter hoch."},
    )
    assert client.post(
        f"/notebooks/{notebook_id}/chat", json={"question": "Wie hoch ist der Eiffelturm?"}
    ).json()["citations"], "Vorbedingung: Retrieval findet das Dokument"

    response = client.delete(f"/notebooks/{notebook_id}")
    assert response.status_code == 204

    # Metadaten weg …
    assert client.get(f"/notebooks/{notebook_id}/documents").status_code == 404
    # … und die Vektor-Seite auch: neues Notebook, alte Frage → keine Treffer von früher.
    fresh_id = client.post("/notebooks", json={"name": "Frisch"}).json()["id"]
    answer = client.post(
        f"/notebooks/{fresh_id}/chat", json={"question": "Wie hoch ist der Eiffelturm?"}
    ).json()
    assert answer["citations"] == []


def test_delete_unknown_notebook_404():
    client = TestClient(create_app(Settings(providers="fake")))
    assert client.delete("/notebooks/gibt-es-nicht").status_code == 404
