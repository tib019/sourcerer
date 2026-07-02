"""Mini-RAG-Eval: Groundedness auf einem festen Test-Dokument (Golden-Set).

Zwei Behauptungen werden geprüft:
(a) Bei beantwortbaren Fragen enthalten die ZITIERTEN Chunks die Antwort-Info wirklich —
    das Zitat ist also belastbar, nicht dekorativ.
(b) Bei Fragen OHNE Antwort in den Quellen sagt das System "steht nicht in den Quellen"
    statt zu halluzinieren.

Läuft standardmäßig mit den deterministischen Fake-Providern (CI-tauglich).
Mit gesetztem OPENAI_API_KEY laufen dieselben Asserts gegen die echten Provider
(gleicher Golden-Set, echtes LLM) — via SOURCERER_EVAL_OPENAI=1.
"""

import json
import os
from pathlib import Path

import pytest

from app.ingest.chunker import Chunker
from app.ingest.extractor import PlainTextExtractor
from app.providers.embeddings import FakeEmbeddings
from app.providers.llm import NO_ANSWER, FakeLLM
from app.providers.vector_store import InMemoryVectorStore
from app.rag.citations import CitationMapper
from app.rag.pipeline import RAGPipeline
from app.rag.prompt_builder import PromptBuilder
from app.rag.retriever import Retriever

_HERE = Path(__file__).parent
GOLDEN = json.loads((_HERE / "golden_set.json").read_text(encoding="utf-8"))
DOCUMENT = (_HERE / "test_document.txt").read_bytes()

NOTEBOOK = "eval-notebook"


def _build_pipeline(embedder, llm) -> RAGPipeline:
    store = InMemoryVectorStore()
    pages = PlainTextExtractor().extract(DOCUMENT)
    # Kleine Chunks (~60 Tokens) → das Dokument ergibt mehrere Chunks und das
    # Retrieval muss wirklich diskriminieren.
    chunks = Chunker(chunk_size=60, overlap=10).chunk(
        pages, document_id="handbuch", document_name="handbuch.txt"
    )
    store.upsert(chunks, embedder.embed([c.text for c in chunks]), namespace=NOTEBOOK)
    return RAGPipeline(
        retriever=Retriever(embedder=embedder, store=store, top_k=4),
        prompt_builder=PromptBuilder(),
        llm=llm,
        citation_mapper=CitationMapper(),
    )


@pytest.fixture(scope="module")
def pipeline() -> RAGPipeline:
    return _build_pipeline(FakeEmbeddings(), FakeLLM())


@pytest.mark.parametrize(
    "case", GOLDEN["answerable"], ids=[c["question"][:40] for c in GOLDEN["answerable"]]
)
def test_cited_chunks_actually_contain_the_answer(pipeline: RAGPipeline, case: dict):
    answer = pipeline.answer(case["question"], NOTEBOOK)
    assert answer.text != NO_ANSWER, f"Keine Antwort für: {case['question']}"
    assert answer.citations, "Antwort ohne Zitat ist im Sourcerer ein Fehler"
    cited_text = " ".join(c.text for c in answer.citations)
    assert case["expected_in_citation"] in cited_text, (
        f"Zitierte Chunks belegen die Antwort nicht: '{case['expected_in_citation']}' "
        f"fehlt in: {cited_text[:200]}…"
    )


@pytest.mark.parametrize(
    "case",
    GOLDEN["unanswerable"],
    ids=[c["question"][:40] for c in GOLDEN["unanswerable"]],
)
def test_unanswerable_question_is_answered_honestly(pipeline: RAGPipeline, case: dict):
    answer = pipeline.answer(case["question"], NOTEBOOK)
    assert answer.text == NO_ANSWER
    assert answer.citations == []


@pytest.mark.skipif(
    not (os.environ.get("OPENAI_API_KEY") and os.environ.get("SOURCERER_EVAL_OPENAI")),
    reason="echter LLM-Eval nur mit OPENAI_API_KEY + SOURCERER_EVAL_OPENAI=1",
)
class TestWithRealOpenAI:
    """Gleicher Golden-Set gegen echte Provider — bewusst opt-in (Kosten, Netz)."""

    @pytest.fixture(scope="class")
    def real_pipeline(self) -> RAGPipeline:
        from app.providers.embeddings import OpenAIEmbeddings
        from app.providers.llm import OpenAIChat

        api_key = os.environ["OPENAI_API_KEY"]
        return _build_pipeline(OpenAIEmbeddings(api_key), OpenAIChat(api_key))

    @pytest.mark.parametrize(
        "case",
        GOLDEN["answerable"],
        ids=[c["question"][:40] for c in GOLDEN["answerable"]],
    )
    def test_grounded(self, real_pipeline: RAGPipeline, case: dict):
        answer = real_pipeline.answer(case["question"], NOTEBOOK)
        assert answer.citations
        cited = " ".join(c.text for c in answer.citations)
        assert case["expected_in_citation"] in cited

    @pytest.mark.parametrize(
        "case",
        GOLDEN["unanswerable"],
        ids=[c["question"][:40] for c in GOLDEN["unanswerable"]],
    )
    def test_honest(self, real_pipeline: RAGPipeline, case: dict):
        answer = real_pipeline.answer(case["question"], NOTEBOOK)
        assert NO_ANSWER in answer.text
        assert answer.citations == []
