"""API-Flow-Tests gegen die komplette App mit Fake-Providern (Composition Root)."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app(Settings(providers="fake")))


@pytest.fixture()
def notebook_id(client: TestClient) -> str:
    response = client.post("/notebooks", json={"name": "Test-Notebook"})
    assert response.status_code == 201
    return response.json()["id"]


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_full_flow_upload_chat_citation(client: TestClient, notebook_id: str):
    text = (
        "Der Sourcerer wurde 2026 gebaut. "
        "Die Hauptstadt von Frankreich ist Paris. "
        "Der Chunker arbeitet mit einem Overlap von fünfzehn Prozent."
    )
    upload = client.post(
        f"/notebooks/{notebook_id}/documents/text",
        json={"name": "fakten.txt", "text": text},
    )
    assert upload.status_code == 201
    assert upload.json()["chunk_count"] >= 1

    docs = client.get(f"/notebooks/{notebook_id}/documents")
    assert [d["name"] for d in docs.json()] == ["fakten.txt"]

    chat = client.post(
        f"/notebooks/{notebook_id}/chat",
        json={"question": "Was ist die Hauptstadt von Frankreich?"},
    )
    assert chat.status_code == 200
    body = chat.json()
    assert "Paris" in body["answer"]
    assert len(body["citations"]) >= 1
    assert body["citations"][0]["document_name"] == "fakten.txt"
    assert "Paris" in body["citations"][0]["text"]


def test_chat_without_sources_says_no_answer(client: TestClient, notebook_id: str):
    chat = client.post(
        f"/notebooks/{notebook_id}/chat", json={"question": "Wer ist CEO von Google?"}
    )
    assert chat.status_code == 200
    assert chat.json()["answer"] == "Dazu steht nichts in den Quellen."
    assert chat.json()["citations"] == []


def test_unknown_notebook_404(client: TestClient):
    assert client.post("/notebooks/nope/chat", json={"question": "x"}).status_code == 404
    assert client.get("/notebooks/nope/documents").status_code == 404


def test_upload_unsupported_type_400(client: TestClient, notebook_id: str):
    response = client.post(
        f"/notebooks/{notebook_id}/documents",
        files={"file": ("bild.png", b"\x89PNG", "image/png")},
    )
    assert response.status_code == 400


def test_upload_empty_text_422(client: TestClient, notebook_id: str):
    response = client.post(
        f"/notebooks/{notebook_id}/documents",
        files={"file": ("leer.txt", b"   ", "text/plain")},
    )
    assert response.status_code == 422
