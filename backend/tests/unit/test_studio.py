"""Studio-Generatoren (Fake-Modus): JSON-Struktur, Zitat-Validierung, Leere-Schutz."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domain import Chunk, DocumentMeta
from app.errors import EmptyDocumentError, GenerationError
from app.main import create_app
from app.providers.llm import FakeLLM, LLMProvider, LLMResponse
from app.rag.studio import StudioService
from app.repository import InMemoryNotebookRepository


def _repo_with_sources() -> tuple[InMemoryNotebookRepository, str]:
    repository = InMemoryNotebookRepository()
    notebook = repository.create_notebook("Studio-NB")
    texts = [
        ("donau.txt", "Die Donau fliesst durch zehn Laender. Sie muendet ins Schwarze Meer."),
        ("alpen.txt", "Der Mont Blanc ist der hoechste Berg der Alpen. Er liegt an der Grenze."),
    ]
    for i, (name, text) in enumerate(texts):
        doc_id = f"d{i}"
        repository.add_document(
            DocumentMeta(
                id=doc_id, notebook_id=notebook.id, name=name,
                media_type="text/plain", page_count=1, chunk_count=1,
            )
        )
        repository.add_chunks(
            [Chunk(id=f"c{i}", document_id=doc_id, document_name=name,
                   chunk_index=0, page=1, text=text)]
        )
    return repository, notebook.id


@pytest.fixture()
def service_and_nb() -> tuple[StudioService, str]:
    repository, notebook_id = _repo_with_sources()
    return StudioService(repository=repository, llm=FakeLLM()), notebook_id


class TestStructure:
    def test_suggested_questions_schema(self, service_and_nb):
        service, nb = service_and_nb
        result = service.suggested_questions(nb)
        assert 3 <= len(result.questions) <= 4
        assert all(isinstance(q, str) and q.strip() for q in result.questions)

    def test_report_schema_and_valid_citations(self, service_and_nb):
        service, nb = service_and_nb
        result = service.report(nb)
        assert result.title.strip()
        assert result.sections
        valid = {s.n for s in result.sources}
        assert valid == {1, 2}  # zwei Quellen-Chunks
        for section in result.sections:
            assert section.heading.strip() and section.content.strip()
            assert all(n in valid for n in section.citations)

    def test_flashcards_schema_and_valid_citations(self, service_and_nb):
        service, nb = service_and_nb
        result = service.flashcards(nb)
        assert 8 <= len(result.cards) <= 12
        valid = {s.n for s in result.sources}
        for card in result.cards:
            assert card.front.strip() and card.back.strip()
            assert card.citation is None or card.citation in valid

    def test_quiz_schema_answer_index_and_citations(self, service_and_nb):
        service, nb = service_and_nb
        result = service.quiz(nb)
        assert result.questions
        valid = {s.n for s in result.sources}
        for q in result.questions:
            assert len(q.options) >= 2
            assert 0 <= q.answer_index < len(q.options)
            assert q.citation is None or q.citation in valid


class TestGuards:
    def test_empty_notebook_rejects_without_llm_call(self):
        class SpyLLM(LLMProvider):
            calls = 0

            def complete(self, messages):
                SpyLLM.calls += 1
                return LLMResponse(text="{}")

        repository = InMemoryNotebookRepository()
        notebook = repository.create_notebook("leer")
        service = StudioService(repository=repository, llm=SpyLLM())
        for generator in (service.suggested_questions, service.report,
                          service.flashcards, service.quiz):
            with pytest.raises(EmptyDocumentError):
                generator(notebook.id)
        assert SpyLLM.calls == 0, "bei 0 Quellen darf kein LLM-Call passieren"

    def test_invalid_citations_are_dropped(self):
        class BadCitationLLM(LLMProvider):
            def complete(self, messages):
                return LLMResponse(
                    text='{"title": "T", "sections": [{"heading": "H", '
                    '"content": "C", "citations": [1, 99]}]}'
                )

        repository, nb = _repo_with_sources()
        result = StudioService(repository=repository, llm=BadCitationLLM()).report(nb)
        assert result.sections[0].citations == [1]  # [99] verworfen

    def test_invalid_json_raises_generation_error(self):
        class BrokenLLM(LLMProvider):
            def complete(self, messages):
                return LLMResponse(text="Hier ist dein Bericht: ...")

        repository, nb = _repo_with_sources()
        with pytest.raises(GenerationError):
            StudioService(repository=repository, llm=BrokenLLM()).report(nb)

    def test_json_code_fence_is_tolerated(self):
        class FencedLLM(LLMProvider):
            def complete(self, messages):
                return LLMResponse(
                    text='```json\n{"questions": ["A?", "B?", "C?"]}\n```'
                )

        repository, nb = _repo_with_sources()
        result = StudioService(repository=repository, llm=FencedLLM()).suggested_questions(nb)
        assert result.questions == ["A?", "B?", "C?"]

    def test_quiz_question_with_invalid_answer_index_is_dropped(self):
        class BadIndexLLM(LLMProvider):
            def complete(self, messages):
                return LLMResponse(
                    text='{"questions": ['
                    '{"question": "ok?", "options": ["a", "b"], "answer_index": 0},'
                    '{"question": "kaputt?", "options": ["a", "b"], "answer_index": 7}]}'
                )

        repository, nb = _repo_with_sources()
        result = StudioService(repository=repository, llm=BadIndexLLM()).quiz(nb)
        assert [q.question for q in result.questions] == ["ok?"]


class TestAPI:
    @pytest.fixture()
    def client(self) -> TestClient:
        return TestClient(create_app(Settings(providers="fake")))

    @pytest.fixture()
    def notebook_id(self, client: TestClient) -> str:
        nb = client.post("/notebooks", json={"name": "NB"}).json()["id"]
        client.post(
            f"/notebooks/{nb}/documents/text",
            json={"name": "fakten.txt",
                  "text": "Der Rhein ist 1233 Kilometer lang. Er entspringt in der Schweiz."},
        )
        return nb

    @pytest.mark.parametrize(
        "path", ["suggested-questions", "report", "flashcards", "quiz"]
    )
    def test_endpoints_return_json(self, client, notebook_id, path):
        response = client.post(f"/notebooks/{notebook_id}/{path}")
        assert response.status_code == 200
        assert response.json()

    @pytest.mark.parametrize(
        "path", ["suggested-questions", "report", "flashcards", "quiz"]
    )
    def test_endpoints_422_on_empty_notebook(self, client, path):
        empty = client.post("/notebooks", json={"name": "leer"}).json()["id"]
        assert client.post(f"/notebooks/{empty}/{path}").status_code == 422

    def test_report_sources_enable_clickable_citations(self, client, notebook_id):
        body = client.post(f"/notebooks/{notebook_id}/report").json()
        assert body["sources"], "sources-Liste macht Zitat-Chips klickbar (wie im Chat)"
        assert {"n", "document_name", "page", "text"} <= set(body["sources"][0])
