"""Audio-Overview (Phase 3): Summary aus den Quellen, TTS hinter Interface."""

import base64
import io
import wave

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domain import Chunk
from app.errors import EmptyDocumentError
from app.main import create_app
from app.providers.llm import FakeLLM
from app.providers.tts import FakeTTS
from app.rag.audio_overview import AudioOverviewService
from app.repository import InMemoryNotebookRepository


def _repo_with_chunks(texts: list[str]):
    repository = InMemoryNotebookRepository()
    notebook = repository.create_notebook("NB")
    from app.domain import DocumentMeta

    repository.add_document(
        DocumentMeta(
            id="d1", notebook_id=notebook.id, name="doc.txt",
            media_type="text/plain", page_count=1, chunk_count=len(texts),
        )
    )
    repository.add_chunks(
        [
            Chunk(id=f"c{i}", document_id="d1", document_name="doc.txt",
                  chunk_index=i, page=1, text=text)
            for i, text in enumerate(texts)
        ]
    )
    return repository, notebook.id


class TestAudioOverviewService:
    def test_summary_comes_from_the_sources(self):
        repository, notebook_id = _repo_with_chunks(
            ["Der Eiffelturm ist 330 Meter hoch. Er steht in Paris.",
             "Der Turm wurde 1889 eroeffnet. Er war lange das hoechste Bauwerk."]
        )
        service = AudioOverviewService(repository, FakeLLM(), FakeTTS())
        overview = service.generate(notebook_id)

        assert "Eiffelturm" in overview.summary
        assert overview.speech.media_type == "audio/wav"
        assert len(overview.speech.audio) > 1000

    def test_fake_tts_produces_playable_wav(self):
        speech = FakeTTS().synthesize("Hallo Welt")
        with wave.open(io.BytesIO(speech.audio)) as wav:
            assert wav.getnchannels() == 1
            assert wav.getframerate() == 16_000
            assert wav.getnframes() > 0

    def test_empty_notebook_raises(self):
        repository = InMemoryNotebookRepository()
        notebook = repository.create_notebook("leer")
        service = AudioOverviewService(repository, FakeLLM(), FakeTTS())
        with pytest.raises(EmptyDocumentError):
            service.generate(notebook.id)


class TestAudioOverviewAPI:
    @pytest.fixture()
    def client(self) -> TestClient:
        return TestClient(create_app(Settings(providers="fake")))

    def test_endpoint_returns_summary_and_audio(self, client):
        notebook_id = client.post("/notebooks", json={"name": "NB"}).json()["id"]
        client.post(
            f"/notebooks/{notebook_id}/documents/text",
            json={"name": "fakten.txt", "text": "Der Mount Everest ist 8849 Meter hoch."},
        )
        response = client.post(f"/notebooks/{notebook_id}/audio-overview")
        assert response.status_code == 200
        body = response.json()
        assert "Everest" in body["summary"]
        assert body["media_type"] == "audio/wav"
        audio = base64.b64decode(body["audio_base64"])
        assert audio[:4] == b"RIFF"  # valides WAV

    def test_empty_notebook_422(self, client):
        notebook_id = client.post("/notebooks", json={"name": "leer"}).json()["id"]
        assert client.post(f"/notebooks/{notebook_id}/audio-overview").status_code == 422

    def test_unknown_notebook_404(self, client):
        assert client.post("/notebooks/nope/audio-overview").status_code == 404
